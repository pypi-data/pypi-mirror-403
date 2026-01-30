# mypy: disable-error-code="index,union-attr"
import asyncio
import logging

import msgspec
from google.oauth2._service_account_async import Credentials

from lueur.make_id import make_id
from lueur.models import GCPMeta, Resource
from lueur.platform.gcp.client import AuthorizedSession, Client
from lueur.platform.gcp.zone import list_project_zones

__all__ = ["explore_compute"]
logger = logging.getLogger("lueur.lib")


async def explore_compute(
    project: str, creds: Credentials | None = None
) -> list[Resource]:
    zones = await list_project_zones(project, creds)

    resources: list[Resource] = []

    if not zones:
        return resources

    async with Client("https://compute.googleapis.com", creds) as c:
        buckets = await explore_all_zones_instances(c, project, zones)
        resources.extend(buckets)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_all_zones_instances(
    c: AuthorizedSession,
    project: str,
    zones: list[str],
) -> list[Resource]:
    resources = []
    tasks: list[asyncio.Task] = []

    async with asyncio.TaskGroup() as tg:
        for zone in zones:
            tasks.append(
                tg.create_task(explore_zone_instances(c, project, zone))
            )

    for task in tasks:
        result = task.result()
        if result is None:
            continue
        resources.extend(result)

    return resources


async def explore_zone_instances(
    c: AuthorizedSession,
    project: str,
    zone: str,
) -> list[Resource]:
    response = await c.get(
        f"/compute/v1/projects/{project}/zones/{zone}/instances"
    )

    instances = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"Compute API access failure: {instances}")
        return []

    if "warning" in instances:
        w = instances["warning"]
        logger.warning(f"Error when exploiring GCP instances: {w}")
        return []

    if "items" not in instances:
        logger.warning(f"No compute instances found: {instances}")
        return []

    results = []

    for instance in instances["items"]:
        self_link = instance.get("selfLink")

        results.append(
            Resource(
                id=make_id(instance["id"]),
                meta=GCPMeta(
                    name=instance["name"],
                    display=instance["name"],
                    kind="instance",
                    platform="gcp",
                    project=project,
                    zone=instance.get("zone"),
                    self_link=self_link,
                    category="compute",
                ),
                struct=instance,
            )
        )

    return results
