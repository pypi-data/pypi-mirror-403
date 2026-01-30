import asyncio
import secrets
from typing import Any, Literal, Sequence, cast

from lueur.make_id import make_id
from lueur.models import Discovery, Meta
from lueur.platform.grafana.alert import (
    expand_links as alert_rules_expand_links,
)
from lueur.platform.grafana.alert import explore_alert_rule
from lueur.platform.grafana.incident import (
    expand_links as incident_expand_links,
)
from lueur.platform.grafana.incident import explore_incident
from lueur.platform.grafana.slo import expand_links as slo_expand_links
from lueur.platform.grafana.slo import explore_slo
from lueur.platform.grafana.team import expand_links as team_expand_links
from lueur.platform.grafana.team import explore_team

__all__ = ["explore", "expand_links"]

Targets = ("alert", "slo", "incident", "team")


async def explore(
    stack_url: str,
    token: str,
    include: Sequence[Literal["alert", "slo", "incident", "team"]]
    | None = None,
) -> Discovery:
    resources = []
    tasks: list[asyncio.Task] = []

    if include is None:
        include = cast(Sequence, Targets)

    async with asyncio.TaskGroup() as tg:
        if "slo" in include:
            tasks.append(tg.create_task(explore_slo(stack_url, token)))
        if "incident" in include:
            tasks.append(tg.create_task(explore_incident(stack_url, token)))
        if "alert" in include:
            tasks.append(tg.create_task(explore_alert_rule(stack_url, token)))
        if "team" in include:
            tasks.append(tg.create_task(explore_team(stack_url, token)))

    for task in tasks:
        result = task.result()
        if result is None:
            continue
        resources.extend(result)

    name = secrets.token_hex(8)

    return Discovery(
        id=make_id(name),
        resources=resources,
        meta=Meta(name=name, display="Grafana", kind="grafana", category=None),
    )


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    slo_expand_links(d, serialized)
    incident_expand_links(d, serialized)
    alert_rules_expand_links(d, serialized)
    team_expand_links(d, serialized)
