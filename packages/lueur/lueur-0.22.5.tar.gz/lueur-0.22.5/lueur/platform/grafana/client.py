from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx

__all__ = ["Client"]


@asynccontextmanager
async def Client(
    stack_url: str, token: str
) -> AsyncGenerator[httpx.AsyncClient, None]:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(
        http2=True, base_url=stack_url, headers=headers
    ) as c:
        yield c
