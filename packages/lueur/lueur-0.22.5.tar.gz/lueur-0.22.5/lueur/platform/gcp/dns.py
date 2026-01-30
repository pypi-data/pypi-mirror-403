# mypy: disable-error-code="index,union-attr"
import asyncio
import logging

import msgspec
from google.oauth2._service_account_async import Credentials

from lueur.make_id import make_id
from lueur.models import GCPMeta, Resource
from lueur.platform.gcp.client import AuthorizedSession, Client

__all__ = ["explore_dns"]
logger = logging.getLogger("lueur.lib")


async def explore_dns(
    project: str, creds: Credentials | None = None
) -> list[Resource]:
    resources = []

    async with Client("https://dns.googleapis.com", creds) as c:
        zones = await explore_managedzones(c, project)

        tasks: list[asyncio.Task] = []

        async with asyncio.TaskGroup() as tg:
            for zone in zones:
                tasks.append(
                    tg.create_task(
                        explore_recordsets(c, project, zone.meta.name)
                    )
                )

        for task in tasks:
            result = task.result()
            if result is None:
                continue
            resources.extend(result)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_managedzones(
    c: AuthorizedSession, project: str
) -> list[Resource]:
    response = await c.get(f"/dns/v1/projects/{project}/managedZones")

    managedZones = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"DNS API access failure: {managedZones}")
        return []

    if "managedZones" not in managedZones:
        logger.warning(f"No managedZones found: {managedZones}")
        return []

    results = []
    for managedZone in managedZones["managedZones"]:
        results.append(
            Resource(
                id=make_id(managedZone["id"]),
                meta=GCPMeta(
                    name=managedZone["name"],
                    display=managedZone["dnsName"],
                    kind="managedzone",
                    platform="gcp",
                    project=project,
                    category="dns",
                ),
                struct=managedZone,
            )
        )

    return results


async def explore_recordsets(
    c: AuthorizedSession, project: str, zone: str
) -> list[Resource]:
    response = await c.get(
        f"/dns/v1/projects/{project}/managedZones/{zone}/rrsets"
    )

    recordsets = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"DNS API access failure: {recordsets}")
        return []

    if "rrsets" not in recordsets:
        logger.warning(f"No recordsets found: {recordsets}")
        return []

    results = []
    for recordset in recordsets["rrsets"]:
        results.append(
            Resource(
                id=make_id(recordset["name"]),
                meta=GCPMeta(
                    name=recordset["name"],
                    display=recordset["name"],
                    kind="recordset",
                    platform="gcp",
                    project=project,
                    category="dns",
                ),
                struct=recordset,
            )
        )

    return results
