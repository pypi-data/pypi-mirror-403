# mypy: disable-error-code="index,call-arg,union-attr"
import logging
from typing import Any

import httpx
import msgspec

from lueur.make_id import make_id
from lueur.models import Discovery, GrafanaMeta, Resource
from lueur.platform.grafana.client import Client

__all__ = ["explore_incident", "expand_links"]
logger = logging.getLogger("lueur.lib")


async def explore_incident(
    stack_url: str,
    token: str,
) -> list[Resource]:
    resources = []

    async with Client(stack_url, token) as c:
        incidents = await explore_incidents(c)
        resources.extend(incidents)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_incidents(c: httpx.AsyncClient) -> list[Resource]:
    response = await c.post(
        "/api/plugins/grafana-incident-app/resources/api/v1/IncidentsService.QueryIncidentPreviews",  # noqa: E501
        json={
            "cursor": {},
            "includeCustomFieldValues": True,
            "includeMembershipPreview": True,
            "query": {
                "limit": 30,
                "orderDirection": "ASC",
                "orderField": "createdTime",
            },
        },
    )

    if response.status_code == 403:
        logger.warning("Grafana API authentication failed")
        return []

    incidents = msgspec.json.decode(response.content)

    if "incidentPreviews" not in incidents:
        logger.warning(f"No Grafana incidents found: {incidents}")
        return []

    results = []
    for incident in incidents["incidentPreviews"]:
        results.append(
            Resource(
                id=make_id(
                    f"{incident['incidentID']}-{incident['createdTime']}"
                ),
                meta=GrafanaMeta(
                    name=incident["slug"],
                    display=incident["title"],
                    kind="incident",
                    platform="grafana",
                    category="observability",
                ),
                struct=incident,
            )
        )

    return results


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    pass
