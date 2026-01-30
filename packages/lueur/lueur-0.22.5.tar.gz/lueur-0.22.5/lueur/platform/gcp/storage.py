# mypy: disable-error-code="index,union-attr"
import logging

import msgspec
from google.oauth2._service_account_async import Credentials

from lueur.make_id import make_id
from lueur.models import GCPMeta, Resource
from lueur.platform.gcp.client import AuthorizedSession, Client

__all__ = ["explore_storage"]
logger = logging.getLogger("lueur.lib")


async def explore_storage(
    project: str, creds: Credentials | None = None
) -> list[Resource]:
    resources = []

    async with Client("https://storage.googleapis.com", creds) as c:
        buckets = await explore_buckets(c, project)
        resources.extend(buckets)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_buckets(c: AuthorizedSession, project: str) -> list[Resource]:
    response = await c.get("/storage/v1/b", params={"project": project})

    buckets = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"Storage API access failure: {buckets}")
        return []

    if "items" not in buckets:
        logger.warning(f"No buckets found: {buckets}")
        return []

    results = []
    for bucket in buckets["items"]:
        self_link = bucket.get("selfLink")

        results.append(
            Resource(
                id=make_id(bucket["id"]),
                meta=GCPMeta(
                    name=bucket["name"],
                    display=bucket["name"],
                    kind="bucket",
                    platform="gcp",
                    project=project,
                    zone=bucket.get("location"),
                    self_link=self_link,
                    category="storage",
                ),
                struct=bucket,
            )
        )

    return results
