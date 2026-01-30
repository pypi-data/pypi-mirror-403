import logging

import msgspec
from google.oauth2._service_account_async import Credentials

from lueur.platform.gcp.client import Client

__all__ = ["list_project_zones", "list_project_region_zones"]
logger = logging.getLogger("lueur.lib")


async def list_project_zones(
    project: str, creds: Credentials | None = None
) -> list[str]:
    async with Client("https://compute.googleapis.com", creds) as c:
        response = await c.get(
            f"/compute/v1/projects/{project}/zones",
            params={"fields": "items.name"},
        )

        zones = msgspec.json.decode(response.content)

        if response.status_code == 403:
            logger.warning(f"Compute API access failure: {zones}")
            return []

        if "items" not in zones:
            logger.warning(f"No project zones found: {zones}")
            return []

        return [r["name"] for r in zones["items"]]


async def list_project_region_zones(
    project: str, region: str, creds: Credentials | None = None
) -> list[str]:
    async with Client("https://compute.googleapis.com", creds) as c:
        response = await c.get(
            f"/compute/v1/projects/{project}/regions/{region}/zones",
            params={"fields": "items.name"},
        )

        zones = msgspec.json.decode(response.content)

        if response.status_code == 403:
            logger.warning(f"Compute API access failure: {zones}")
            return []

        if "items" not in zones:
            logger.warning(f"No region zones found: {zones}")
            return []

        return [r["name"] for r in zones.get("items", [])]
