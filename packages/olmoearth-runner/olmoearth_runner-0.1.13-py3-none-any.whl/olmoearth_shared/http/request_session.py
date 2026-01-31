import logging
from datetime import timedelta
from http import HTTPStatus
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class RequestSession:
    def __init__(
        self,
        total_retries: int,
        backoff_factor: float,
        backoff_max: timedelta,
        allowed_methods_for_retry: tuple[str, ...] = ("DELETE", "GET", "PATCH", "POST", "PUT"),
        statuses_for_retry: tuple[int, ...] = (
            HTTPStatus.TOO_MANY_REQUESTS,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT,
        ),
    ):
        self._session = requests.Session()
        retry = Retry(
            total=total_retries,
            backoff_factor=backoff_factor,
            backoff_max=backoff_max.total_seconds(),
            allowed_methods=allowed_methods_for_retry,
            status_forcelist=statuses_for_retry,
            raise_on_status=False,
            respect_retry_after_header=True,
        )
        self._session.mount("http://", HTTPAdapter(max_retries=retry))
        self._session.mount("https://", HTTPAdapter(max_retries=retry))
        self._session.hooks["response"] = lambda response, *args, **kwargs: response

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        logger.debug("[request] %s %s %s", method, url, kwargs)
        return self._session.request(method, url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("DELETE", url, **kwargs)

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("PATCH", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("PUT", url, **kwargs)
