import msgspec
from google.oauth2._service_account_async import Credentials

from lueur.platform.gcp.client import Client

__all__ = ["list_project_regions"]


async def list_project_regions(
    project: str, creds: Credentials | None = None
) -> list[str]:
    async with Client("https://compute.googleapis.com", creds) as c:
        response = await c.get(
            f"/compute/v1/projects/{project}/regions",
            params={"fields": "items.name"},
        )

        regions = msgspec.json.decode(response.content)

        return [r["name"] for r in regions["items"]]
