from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from google.auth import exceptions, transport
from google.auth._credentials_async import Credentials
from google.auth._default_async import default_async
from google.oauth2._service_account_async import Credentials as OAuthCreds
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

__all__ = ["Client", "AuthorizedSession"]


class _Response(transport.Response):
    """
    Requests transport response adapter.
    Args:
        response (httpx.Response): The raw Requests response.
    """

    def __init__(self, response: httpx.Response):
        self._response = response
        self._content: bytes | None = None

    @property
    def status(self) -> int:
        return self._response.status_code

    @property
    def headers(self) -> httpx.Headers:
        return self._response.headers

    @property
    def data(self) -> bytes:
        return self._response.content

    async def raw_content(self):
        return await self.content()

    async def content(self) -> bytes:
        if self._content is None:
            self._content = await self._response.aread()
        return self._content


class Request(transport.Request):
    def __init__(self, httpx_client: httpx.AsyncClient) -> None:
        self.client = httpx_client

    async def __call__(
        self,
        url: str,
        method: str = "GET",
        body: Any = None,
        headers: dict[str, str] | None = None,
        timeout: httpx._types.TimeoutTypes | None = None,
        **kwargs,
    ):
        try:
            response = await self.client.request(
                method,
                url,
                data=body,
                headers=headers,
                timeout=timeout or httpx.Timeout(60),
                **kwargs,
            )
            return _Response(response)

        except httpx.HTTPError as caught_exc:
            new_exc = exceptions.TransportError(caught_exc)
            raise new_exc from caught_exc


class AuthorizedSession(httpx.AsyncClient):
    def __init__(
        self,
        credentials: Credentials | OAuthCreds,
        **kwargs,
    ):
        super(AuthorizedSession, self).__init__(**kwargs)
        self.credentials: Credentials = credentials

    @retry(
        retry=(
            retry_if_exception_type(httpx.TimeoutException)
            | retry_if_exception_type(httpx.ConnectError)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=5, max=20),
    )
    async def request(  # type: ignore
        self,
        method: str,
        url: str,
        data: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> httpx.Response:
        limits = httpx.Limits(max_connections=10, max_keepalive_connections=10)
        timeout = httpx.Timeout(60)

        async with httpx.AsyncClient(http2=True, limits=limits) as session:
            request_headers = headers.copy() if headers is not None else {}

            await self.credentials.before_request(
                Request(session), method, url, request_headers
            )

            # we want to force or timeout value
            kwargs.pop("timeout", None)

            response: httpx.Response = await super(
                AuthorizedSession, self
            ).request(
                method,
                url,
                data=data,
                headers=request_headers,
                timeout=timeout,
                **kwargs,
            )

            return response


@asynccontextmanager
async def Client(
    base_url: str, creds: OAuthCreds | None = None
) -> AsyncIterator[AuthorizedSession]:
    credentials = creds
    if creds is None:
        credentials, _ = default_async()

    async with AuthorizedSession(
        credentials,  # type: ignore
        base_url=httpx.URL(base_url),
    ) as s:
        yield s
