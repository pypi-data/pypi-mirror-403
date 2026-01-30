import json
import time
import copy
from dataclasses import dataclass
from typing import Optional, Union, Any

import requests
from requests.exceptions import ConnectionError    # noqa A004

from metasdk.logger import LOGGER_ENTITY
from metasdk.exceptions import RetryHttpRequestError, EndOfTriesError, UnexpectedError, ApiProxyError, RateLimitError, \
    ApiProxyBusinessErrorMixin


@dataclass
class RequestPolicy:
    """Политика выполнения HTTP-запросов: таймауты и повторные попытки."""

    max_retries: int = 20
    """Максимальное количество попыток."""

    retry_delay_sec: int = 20
    """Задержка между попытками в секундах."""

    timeout_sec: int | float = 3600
    """Общий таймаут запроса в секундах (используется если connect/read не заданы)."""

    connect_timeout_sec: Optional[int | float] = None
    """Таймаут установки соединения. None означает без лимита (если задан read_timeout_sec)."""

    read_timeout_sec: Optional[int | float] = None
    """Таймаут чтения ответа. None означает без лимита (если задан connect_timeout_sec)."""

    @property
    def timeout(self) -> Union[int | float, tuple[int | float | None, int | float | None]]:
        """
        Возвращает настройки таймаута для requests.

        - Если оба connect/read не заданы — возвращает timeout_sec (общий таймаут).
        - Если хотя бы один задан — возвращает tuple (connect, read).
          None в tuple интерпретируется requests как "без таймаута".
        """
        if self.connect_timeout_sec is None and self.read_timeout_sec is None:
            return self.timeout_sec

        return self.connect_timeout_sec, self.read_timeout_sec


class ApiProxyService:
    MAX_PAGES = 100000

    def __init__(self, app):
        """
        :type app: metasdk.MetaApp
        """
        self.__app = app
        self.__options = {}
        self.__data_get_cache = {}
        self.__data_get_flatten_cache = {}

    def __api_proxy_call(
        self,
        engine: str,
        payload: dict[str, Any],
        method: str,
        analyze_json_error_param: bool,
        retry_request_substr_variants: list[str],
        stream: bool = False,
        raise_business_errors: bool = False,
        log: bool = False,
        request_policy: RequestPolicy | None = None,
    ):
        """
        :param engine: Система
        :param payload: Данные для запроса
        :param method: string Может содержать native_call | tsv | json_newline
        :param analyze_json_error_param: Нужно ли производить анализ параметра error в ответе прокси
        :param retry_request_substr_variants: Список подстрок, при наличии которых в ответе будет происходить перезапрос
        :param stream: стримиговый запрос, можно будет итерироваться по строкам ответа, не загружая весь ответ в память
        :param log: логировать параметры запроса
        :param request_policy: Политика выполнения запроса (таймауты, ретраи). По умолчанию RequestPolicy().
        :return:
        """
        policy = request_policy or RequestPolicy()

        log_ctx = {
            "engine": engine,
            "method": payload.get('method'),
            "method_params": payload.get('method_params')
        }
        if log:
            self.__app.log.info("Call api proxy", log_ctx)
        body = {
            "engine": engine,
            "payload": payload
        }
        for _try_idx in range(policy.max_retries):
            try:
                body_str = json.dumps(body)
                headers = {
                    "User-Agent": self.__app.user_agent,
                    "X-App": "META",
                    "X-Worker": self.__app.service_id,
                    "X-ObjectLocator": LOGGER_ENTITY.get("objectLocator")
                }
                resp = requests.post(
                    self.__app.api_proxy_url + "/" + method,
                    body_str,
                    timeout=policy.timeout,
                    stream=stream,
                    headers=headers,
                )

                self.check_err(resp, analyze_json_error_param=analyze_json_error_param,
                               retry_request_substr_variants=retry_request_substr_variants,
                               raise_business_errors=raise_business_errors)
                return resp
            except (RetryHttpRequestError, RateLimitError, ConnectionError) as e:
                self.__app.log.warning("Sleep retry query: " + str(e), log_ctx)
                sleep_time = policy.retry_delay_sec

                if e.__class__.__name__ == "RateLimitError":
                    sleep_time = e.waiting_time

                time.sleep(sleep_time)
        raise EndOfTriesError("Api of api proxy tries request")

    def call_proxy_with_paging(
        self,
        engine: str,
        payload: dict[str, Any],
        method: str,
        analyze_json_error_param: bool,
        retry_request_substr_variants: list[str],
        max_pages: int = MAX_PAGES,
        raise_business_errors: bool = False,
        log: bool = False,
        request_policy: RequestPolicy | None = None,
    ):
        """
        Постраничный запрос
        :param engine: Система
        :param payload: Данные для запроса
        :param method: string Может содержать native_call | tsv | json_newline
        :param analyze_json_error_param: Нужно ли производить анализ параметра error в ответе прокси
        :param retry_request_substr_variants: Список подстрок, при наличии которых в ответе будет происходить перезапрос
        :param max_pages: Максимальное количество страниц в запросе
        :param raise_business_errors: Преобразовывать ApiProxyError в конкретную BusinessError
        :param log: логировать параметры запроса
        :param request_policy: Политика выполнения запроса (таймауты, ретраи). По умолчанию RequestPolicy().
        :return: объект генератор
        """
        copy_payload = copy.deepcopy(payload)

        idx = 0
        for idx in range(max_pages):    # noqa B007
            resp = self.__api_proxy_call(
                engine,
                copy_payload,
                method,
                analyze_json_error_param,
                retry_request_substr_variants,
                raise_business_errors=raise_business_errors,
                log=log,
                request_policy=request_policy,
            )
            yield resp

            paging_resp = resp.json().get("paging")
            if not paging_resp:
                break
            copy_payload["paging"] = paging_resp

        if idx >= max_pages:
            self.__app.log.warning("Достигнут максимальный предел страниц", {"max_pages": max_pages})

    def call_proxy(
        self,
        engine: str,
        payload: dict[str, Any],
        method: str,
        analyze_json_error_param: bool,
        retry_request_substr_variants: list[str],
        stream: bool = False,
        raise_business_errors: bool = False,
        log: bool = False,
        request_policy: RequestPolicy | None = None,
    ):
        """
        :param engine: Система
        :param payload: Данные для запроса
        :param method: string Может содержать native_call | tsv | json_newline
        :param analyze_json_error_param: Нужно ли производить анализ параметра error в ответе прокси
        :param retry_request_substr_variants: Список подстрок, при наличии которых в ответе будет происходить перезапрос
        :param raise_business_errors: Преобразовывать ApiProxyError в конкретную BusinessError
        :param stream: стримиговый запрос, можно будет итерироваться по строкам ответа, не загружая весь ответ в память
        :param log: логировать параметры запроса
        :param request_policy: Политика выполнения запроса (таймауты, ретраи). По умолчанию RequestPolicy().
        :return:
        """
        return self.__api_proxy_call(
            engine,
            payload,
            method,
            analyze_json_error_param,
            retry_request_substr_variants,
            stream,
            raise_business_errors=raise_business_errors,
            request_policy=request_policy,
        )

    @staticmethod
    def check_err(resp, analyze_json_error_param=False, retry_request_substr_variants=None,
                  raise_business_errors=False):
        """
        :type retry_request_substr_variants: list Список вхождений строк, при налиции которых в ошибке апи будет произведен повторный запрос к апи
        """
        if retry_request_substr_variants is None:
            retry_request_substr_variants = []

        # РКН блокировки вызывают ошибку SSL
        retry_request_substr_variants.append("TLSV1_ALERT_ACCESS_DENIED")

        if resp.status_code in [502, 503, 504]:
            raise RetryHttpRequestError(resp.text)

        if resp.status_code >= 400:
            rtext = resp.text
            for v_ in retry_request_substr_variants:
                if v_ in rtext:
                    raise RetryHttpRequestError(rtext)
            raise UnexpectedError("HTTP request failed: {} {}".format(resp.status_code, rtext))
        if analyze_json_error_param:
            data_ = resp.json()
            error = data_.get("error")
            if error:
                full_err_ = json.dumps(error, ensure_ascii=False)

                if error.get("type") == "RateLimitError":
                    raise RateLimitError(error.get("message"), waiting_time=error.get("waiting_time"))

                for v_ in retry_request_substr_variants:
                    if v_ in full_err_:
                        raise RetryHttpRequestError(full_err_)
                if raise_business_errors:
                    for cls in ApiProxyBusinessErrorMixin.__subclasses__():
                        if cls.__name__ == error.get("type"):
                            raise cls(full_err_)
                raise ApiProxyError(full_err_)
        return resp
