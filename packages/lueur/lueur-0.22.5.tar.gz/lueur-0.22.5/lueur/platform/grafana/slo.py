# mypy: disable-error-code="index,call-arg,union-attr"
import logging
from typing import Any

import httpx
import msgspec

from lueur.links import add_link
from lueur.make_id import make_id
from lueur.models import Discovery, GrafanaMeta, Link, Resource
from lueur.platform.grafana.client import Client
from lueur.rules import iter_resource

__all__ = ["explore_slo", "expand_links"]
logger = logging.getLogger("lueur.lib")


async def explore_slo(
    stack_url: str,
    token: str,
) -> list[Resource]:
    resources = []

    async with Client(stack_url, token) as c:
        slos = await explore_slos(c)
        resources.extend(slos)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_slos(c: httpx.AsyncClient) -> list[Resource]:
    response = await c.get("/api/plugins/grafana-slo-app/resources/v1/slo")

    if response.status_code == 403:
        logger.warning("Grafana API authentication failed")
        return []

    slos = msgspec.json.decode(response.content)

    if "slos" not in slos:
        logger.warning(f"No Grafana SLO found: {slos}")
        return []

    results = []
    for slo in slos["slos"]:
        results.append(
            Resource(
                id=make_id(slo["uuid"]),
                meta=GrafanaMeta(
                    name=slo["name"],
                    display=slo["name"],
                    kind="slo",
                    platform="grafana",
                    category="observability",
                ),
                struct=slo,
            )
        )

    return results


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    for team_name in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='slo' && @.meta.platform=='grafana'].struct.labels[?@.key=='team_name'].value",  # noqa: E501
    ):
        r_id = team_name.parent.parent.parent.parent.obj["id"]
        name = team_name.value

        p = f"$.resources[?@.meta.kind=='team' && @.meta.platform=='grafana' && @.meta.name=='{name}']"  # noqa: E501
        for team in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="team",
                    path=team.path,
                    pointer=str(team.pointer()),
                    id=team.obj["id"],
                ),
            )

    for slo in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='slo' && @.meta.platform=='grafana']",  # noqa: E501
    ):
        r_id = slo.obj["id"]
        slo = slo.value  # type: ignore

        p = f"$.resources[?@.meta.kind=='team' && @.meta.platform=='grafana' && @.meta.name=='{name}']"  # noqa: E501
        for team in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="team",
                    path=team.path,
                    pointer=str(team.pointer()),
                    id=team.obj["id"],
                ),
            )
