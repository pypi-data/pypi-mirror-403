# mypy: disable-error-code="index,union-attr"
import asyncio
import logging
from typing import Any

import msgspec
from google.oauth2._service_account_async import Credentials

from lueur.links import add_link
from lueur.make_id import make_id
from lueur.models import Discovery, GCPMeta, Link, Resource
from lueur.platform.gcp.client import AuthorizedSession, Client
from lueur.rules import iter_resource

__all__ = ["explore_vpc", "expand_links"]
logger = logging.getLogger("lueur.lib")


async def explore_vpc(
    project: str, creds: Credentials | None = None
) -> list[Resource]:
    resources = []

    async with Client("https://compute.googleapis.com", creds) as c:
        networks = await explore_global_networks(c, project)
        resources.extend(networks)

        tasks: list[asyncio.Task] = []
        seen: list[str] = []

        async with asyncio.TaskGroup() as tg:
            for net in networks:
                for subnet in net.struct["subnetworks"]:
                    if subnet not in seen:
                        seen.append(subnet)
                        tasks.append(
                            tg.create_task(explore_subnet(c, project, subnet))
                        )

        for task in tasks:
            result = task.result()
            if result is None:
                continue
            resources.append(result)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_global_networks(
    c: AuthorizedSession, project: str
) -> list[Resource]:
    response = await c.get(f"/compute/v1/projects/{project}/global/networks")

    networks = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"Network API access failure: {networks}")
        return []

    if "items" not in networks:
        logger.warning(f"No global networks found: {networks}")
        return []

    results = []
    for net in networks["items"]:
        self_link = net["selfLink"]

        results.append(
            Resource(
                id=make_id(net["id"]),
                meta=GCPMeta(
                    name=net["name"],
                    display=net["name"],
                    kind="network",
                    project=project,
                    self_link=self_link,
                    platform="gcp",
                    category="network",
                ),
                struct=net,
            )
        )

    return results


async def explore_subnet(
    c: AuthorizedSession, project: str, subnet: str
) -> Resource | None:
    response = await c.get(subnet)

    sub = msgspec.json.decode(response.content)

    if "error" in sub:
        return None

    self_link = sub["selfLink"]

    return Resource(
        id=make_id(sub["id"]),
        meta=GCPMeta(
            name=sub["id"],
            display=sub["name"],
            kind="subnet",
            project=project,
            self_link=self_link,
            platform="gcp",
            category="network",
        ),
        struct=sub,
    )


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    for s in iter_resource(
        serialized, "$.resources[?@.meta.kind=='network'].meta.self_link"
    ):
        r_id = s.parent.parent.obj["id"]
        net = s.value
        p = f"$.resources[?@.meta.kind=='subnet' && @.struct.network=='{net}']"
        for subnet in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="subnet",
                    path=subnet.path,
                    pointer=str(subnet.pointer()),
                    id=subnet.obj["id"],
                ),
            )

        p = f"$.resources[?@.meta.kind=='global-neg' && @.struct.network=='{net}']"  # noqa E501
        for neg in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="global-neg",
                    path=neg.path,
                    pointer=str(neg.pointer()),
                    id=neg.obj["id"],
                ),
            )

        p = f"$.resources[?@.meta.kind=='regional-neg' && @.struct.network=='{net}']"  # noqa E501
        for neg in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="regional-neg",
                    path=neg.path,
                    pointer=str(neg.pointer()),
                    id=neg.obj["id"],
                ),
            )

    for s in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='network' && @.meta.name=='default']",
    ):
        r_id = s.obj["id"]
        p = "$.resources[?@.meta.kind=='regional-neg' && @.struct.network!='']"
        for neg in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="regional-neg",
                    path=neg.path,
                    pointer=str(neg.pointer()),
                    id=neg.obj["id"],
                ),
            )
