# mypy: disable-error-code="index,union-attr"
import logging

import msgspec
from google.oauth2._service_account_async import Credentials

from lueur.make_id import make_id
from lueur.models import GCPMeta, Resource
from lueur.platform.gcp.client import AuthorizedSession, Client

__all__ = ["explore_memorystore"]
logger = logging.getLogger("lueur.lib")


async def explore_memorystore(
    project: str, creds: Credentials | None = None
) -> list[Resource]:
    resources = []

    async with Client("https://redis.googleapis.com", creds) as c:
        buckets = await explore_all_instances(c, project)
        resources.extend(buckets)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_all_instances(
    c: AuthorizedSession, project: str
) -> list[Resource]:
    response = await c.get(f"/v1/projects/{project}/locations/-/instances")

    stores = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"Memorystore API access failure: {stores}")
        return []

    if "instances" not in stores:
        logger.warning(f"No memorystore instances found: {stores}")
        return []

    results = []
    for store in stores["instances"]:
        results.append(
            Resource(
                id=make_id(store["name"]),
                meta=GCPMeta(
                    name=store["name"],
                    display=store["displayName"],
                    kind="instance",
                    platform="gcp",
                    project=project,
                    zone=store.get("locationId"),
                    category="memorystore",
                ),
                struct=store,
            )
        )

    return results
