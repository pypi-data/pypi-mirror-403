import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Type

from kubernetes import client, config
from urllib3.response import HTTPResponse

__all__ = ["Client", "AsyncClient"]
logger = logging.getLogger("lueur.lib")


class AsyncClient:
    def __init__(self, api: Type, credentials: dict[str, Any] | None) -> None:
        self.api: Type | None = api
        self.credentials = credentials
        self.client: client.ApiClient | None = None
        self.inst = None

    async def __aenter__(self) -> "AsyncClient":
        assert self.api

        if self.credentials is not None:
            config.load_kube_config_from_dict(self.credentials)
        else:
            config.load_kube_config()
        self.client = client.ApiClient()
        self.inst = self.api(self.client)

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: Any | None = None,
    ) -> None:
        self.api = None
        self.client = None
        self.inst = None

    async def execute(
        self, func: str, /, *args, **kwargs
    ) -> HTTPResponse | client.ApiException:
        def _run(*args, **kwargs) -> HTTPResponse:
            f = getattr(self.inst, func)
            try:
                return f(*args, _preload_content=False, **kwargs)
            except client.ApiException as x:
                logger.debug("Kubernetes client execution error", exc_info=True)

                return x

        return await asyncio.to_thread(_run, *args, **kwargs)


@asynccontextmanager
async def Client(
    api: Type, credentials: dict[str, Any] | None
) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(api, credentials) as c:
        yield c
