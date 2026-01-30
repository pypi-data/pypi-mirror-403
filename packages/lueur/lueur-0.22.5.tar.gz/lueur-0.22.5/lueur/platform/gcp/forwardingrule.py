# mypy: disable-error-code="union-attr"
import logging

import msgspec
from google.oauth2._service_account_async import Credentials

from lueur.make_id import make_id
from lueur.models import GCPMeta, Resource
from lueur.platform.gcp.client import AuthorizedSession, Client

__all__ = ["explore_forwardingrules"]
logger = logging.getLogger("lueur.lib")


async def explore_forwardingrules(
    project: str, location: str | None = None, creds: Credentials | None = None
) -> list[Resource]:
    resources = []

    async with Client("https://compute.googleapis.com", creds) as c:
        if location:
            rules = await explore_regional_forwardingrules(c, project, location)
            resources.extend(rules)
        else:
            rules = await explore_global_forwardingrules(c, project)
            resources.extend(rules)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_global_forwardingrules(
    c: AuthorizedSession, project: str
) -> list[Resource]:
    response = await c.get(
        f"/compute/v1/projects/{project}/global/forwardingRules"
    )

    rules = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"Forwadingrules API access failure: {rules}")
        return []

    if "items" not in rules:
        logger.warning(f"No global forwadingrules found: {rules}")
        return []

    results = []
    for rule in rules.get("items", []):
        self_link = rule["selfLink"]
        name = rule["name"]
        display = name

        results.append(
            Resource(
                id=make_id(rule["id"]),
                meta=GCPMeta(
                    name=name,
                    display=display,
                    kind="global-forwarding-rules",
                    project=project,
                    self_link=self_link,
                    platform="gcp",
                    category="network",
                ),
                struct=rule,
            )
        )

    return results


async def explore_regional_forwardingrules(
    c: AuthorizedSession, project: str, location: str
) -> list[Resource]:
    response = await c.get(
        f"/compute/v1/projects/{project}/regions/{location}/forwardingRules"
    )

    rules = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"Forwadingrules API access failure: {rules}")
        return []

    if "items" not in rules:
        logger.warning(f"No regional forwadingrules found: {rules}")
        return []

    results = []
    for rule in rules.get("items", []):
        self_link = rule["selfLink"]
        name = rule["name"]
        display = name

        results.append(
            Resource(
                id=make_id(rule["id"]),
                meta=GCPMeta(
                    name=name,
                    display=display,
                    kind="regional-forwarding-rules",
                    project=project,
                    self_link=self_link,
                    region=location,
                    platform="gcp",
                    category="network",
                ),
                struct=rule,
            )
        )

    return results
