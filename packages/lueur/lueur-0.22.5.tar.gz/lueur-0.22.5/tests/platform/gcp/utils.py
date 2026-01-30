from contextlib import contextmanager
from typing import Any, Callable, Generator
from unittest.mock import patch, AsyncMock

from google.auth.credentials import AnonymousCredentials


class TestAnonymousCredentials(AnonymousCredentials):
    async def before_request(self, request, method, url, headers):
        pass


@contextmanager
def patch_auth() -> Generator[AsyncMock, None, None]:
    with patch("lueur.platform.gcp.client.default_async", autospec=True) as p:
        p.return_value = (TestAnonymousCredentials(), "")
        yield p
