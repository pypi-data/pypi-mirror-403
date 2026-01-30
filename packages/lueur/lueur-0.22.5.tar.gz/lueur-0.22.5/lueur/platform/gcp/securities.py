# mypy: disable-error-code="union-attr"
import logging

import msgspec
from google.oauth2._service_account_async import Credentials

from lueur.make_id import make_id
from lueur.models import GCPMeta, Resource
from lueur.platform.gcp.client import AuthorizedSession, Client

__all__ = ["explore_securities"]
logger = logging.getLogger("lueur.lib")


async def explore_securities(
    project: str, location: str | None = None, creds: Credentials | None = None
) -> list[Resource]:
    resources = []

    async with Client("https://compute.googleapis.com", creds) as c:
        if not location:
            securities = await explore_global_securities(c, project)
            resources.extend(securities)
        else:
            securities = await explore_regional_securities(c, project, location)
            resources.extend(securities)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_global_securities(
    c: AuthorizedSession, project: str
) -> list[Resource]:
    response = await c.get(
        f"/compute/v1/projects/{project}/global/securityPolicies"
    )

    securities = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"Securities API access failure: {securities}")
        return []

    if "items" not in securities:
        logger.warning(f"No global securities found: {securities}")
        return []

    results = []
    for security in securities.get("items", []):
        self_link = security["selfLink"]
        name = security["name"]
        display = name

        results.append(
            Resource(
                id=make_id(security["id"]),
                meta=GCPMeta(
                    name=name,
                    display=display,
                    kind="global-securities",
                    project=project,
                    self_link=self_link,
                    platform="gcp",
                    category="security",
                ),
                struct=security,
            )
        )

    return results


async def explore_regional_securities(
    c: AuthorizedSession, project: str, location: str
) -> list[Resource]:
    response = await c.get(
        f"/compute/v1/projects/{project}/regions/{location}/securityPolicies"
    )

    securities = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"Securities API access failure: {securities}")
        return []

    if "items" not in securities:
        logger.warning(f"No regional securities found: {securities}")
        return []

    results = []
    for security in securities.get("items", []):
        self_link = security["selfLink"]
        name = security["name"]
        display = name

        results.append(
            Resource(
                id=make_id(security["id"]),
                meta=GCPMeta(
                    name=name,
                    display=display,
                    kind="regional-securities",
                    project=project,
                    self_link=self_link,
                    region=location,
                    platform="gcp",
                    category="security",
                ),
                struct=security,
            )
        )

    return results
