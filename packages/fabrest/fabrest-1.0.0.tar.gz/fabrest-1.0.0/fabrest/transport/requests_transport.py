from typing import Any, Dict, Optional

import requests

from .options import RequestOptions
from ..api.client import Client


class RequestsTransport:
    def __init__(self, client: Client) -> None:
        self._client = client

    def request(
        self,
        method: str,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> requests.Response:
        opts = options or RequestOptions()
        return self._client.request(
            method=method,
            url=url,
            session=session,
            headers=opts.headers,
            params=opts.params,
            json=json,
            timeout=opts.timeout or 120,
            wait_for_completion=opts.wait_for_completion,
            throttle_retry_interval=opts.throttle_retry_interval,
            lro_check_interval=opts.lro_check_interval,
            item_name_in_use_max_retries=opts.item_name_in_use_max_retries,
            item_name_in_use_retry_interval=opts.item_name_in_use_retry_interval,
            max_retries=opts.max_retries,
            retry_interval=opts.retry_interval,
        )

    def invoke(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> requests.Response:
        opts = options or RequestOptions()
        return self._client._invoke(
            url=url,
            headers=opts.headers,
            session=session,
            params=opts.params,
            json=json,
            timeout=opts.timeout or 120,
            wait_for_completion=opts.wait_for_completion,
            throttle_retry_interval=opts.throttle_retry_interval,
            invoke_check_interval=opts.job_check_interval,
            max_retries=opts.max_retries,
            retry_interval=opts.retry_interval,
        )

    def close_session_if_owned(self, session: Optional[requests.Session]) -> bool:
        return self._client.close_session_if_owned(session)

    def close(self) -> None:
        self._client.close()
