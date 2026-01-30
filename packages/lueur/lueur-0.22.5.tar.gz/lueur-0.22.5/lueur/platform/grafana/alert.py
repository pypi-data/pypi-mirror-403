# mypy: disable-error-code="index,call-arg,union-attr"
import logging
from typing import Any

import httpx
import msgspec

from lueur.make_id import make_id
from lueur.models import Discovery, GrafanaMeta, Resource
from lueur.platform.grafana.client import Client

__all__ = ["explore_alert_rule", "expand_links"]
logger = logging.getLogger("lueur.lib")


async def explore_alert_rule(
    stack_url: str,
    token: str,
) -> list[Resource]:
    resources = []

    async with Client(stack_url, token) as c:
        rules = await explore_alert_rules(c)
        resources.extend(rules)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_alert_rules(c: httpx.AsyncClient) -> list[Resource]:
    response = await c.get("/api/v1/provisioning/alert-rules")

    if response.status_code == 403:
        logger.warning("Grafana API authentication failed")
        return []

    rules = msgspec.json.decode(response.content)

    results = []
    for rule in rules:
        results.append(
            Resource(
                id=make_id(rule["uid"]),
                meta=GrafanaMeta(
                    name=rule["title"],
                    display=rule["title"],
                    kind="alert-rule",
                    platform="grafana",
                    category="observability",
                ),
                struct=rule,
            )
        )

    return results


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    pass
