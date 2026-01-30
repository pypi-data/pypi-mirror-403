# mypy: disable-error-code="index,call-arg,union-attr"
import asyncio
import logging
from typing import Any

import httpx
import msgspec

from lueur.links import add_link
from lueur.make_id import make_id
from lueur.models import Discovery, GrafanaMeta, Link, Resource
from lueur.platform.grafana.client import Client
from lueur.rules import iter_resource

__all__ = ["explore_team", "expand_links"]
logger = logging.getLogger("lueur.lib")


async def explore_team(
    stack_url: str,
    token: str,
) -> list[Resource]:
    resources = []

    tasks: list[asyncio.Task] = []

    async with Client(stack_url, token) as c:
        teams = await explore_teams(c)
        resources.extend(teams)

        async with asyncio.TaskGroup() as tg:
            for team in teams:
                tasks.append(
                    tg.create_task(explore_team_members(c, team.struct["uid"]))
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
async def explore_teams(c: httpx.AsyncClient) -> list[Resource]:
    response = await c.get("/api/teams/search")

    if response.status_code == 403:
        logger.warning("Grafana API authentication failed")
        return []

    teams = msgspec.json.decode(response.content)

    if "teams" not in teams:
        logger.warning(f"No Grafana teams group found: {teams}")
        return []

    results = []
    for team in teams["teams"]:
        results.append(
            Resource(
                id=make_id(f"{team['id']}-{team['orgId']}"),
                meta=GrafanaMeta(
                    name=team["name"],
                    display=team["name"],
                    kind="team",
                    platform="grafana",
                    category="observability",
                ),
                struct=team,
            )
        )

    return results


async def explore_team_members(
    c: httpx.AsyncClient, team_id: int
) -> list[Resource]:
    response = await c.get(f"/api/teams/{team_id}/members")

    if response.status_code == 403:
        logger.warning("Grafana API authentication failed")
        return []

    members = msgspec.json.decode(response.content)

    results = []
    for member in members:
        results.append(
            Resource(
                id=make_id(f"{member['userId']}-{team_id}"),
                meta=GrafanaMeta(
                    name=member["email"],
                    display=member["email"],
                    kind="team-member",
                    platform="grafana",
                    category="observability",
                ),
                struct=member,
            )
        )

    return results


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    for team_id in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='team' && @.meta.platform=='grafana'].struct.uid",  # noqa: E501
    ):
        r_id = team_id.parent.parent.obj["id"]
        uid = team_id.value

        p = f"$.resources[?@.meta.kind=='team-member' && @.struct.teamUID=='{uid}']"  # noqa E501
        for member in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="team-member",
                    path=member.path,
                    pointer=str(member.pointer()),
                ),
            )

    for team_id in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='team-member' && @.meta.platform=='grafana'].struct.teamUID",  # noqa: E501
    ):
        r_id = team_id.parent.parent.obj["id"]
        uid = team_id.value

        p = f"$.resources[?@.meta.kind=='team' && @.struct.uid=='{uid}']"
        for team in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="team",
                    path=team.path,
                    pointer=str(team.pointer()),
                ),
            )
