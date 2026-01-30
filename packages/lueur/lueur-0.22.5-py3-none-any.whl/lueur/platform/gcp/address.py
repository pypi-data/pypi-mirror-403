# mypy: disable-error-code="union-attr"
import logging

import msgspec
from google.oauth2._service_account_async import Credentials

from lueur.make_id import make_id
from lueur.models import GCPMeta, Resource
from lueur.platform.gcp.client import AuthorizedSession, Client

__all__ = ["explore_addresses"]
logger = logging.getLogger("lueur.lib")


async def explore_addresses(
    project: str, location: str | None = None, creds: Credentials | None = None
) -> list[Resource]:
    resources = []

    async with Client("https://compute.googleapis.com", creds) as c:
        if location:
            addresses = await explore_regional_addresses(c, project, location)
            resources.extend(addresses)
        else:
            addresses = await explore_global_addresses(c, project)
            resources.extend(addresses)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_global_addresses(
    c: AuthorizedSession,
    project: str,
) -> list[Resource]:
    response = await c.get(f"/compute/v1/projects/{project}/global/addresses")

    addresses = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"Global Address API access failure: {addresses}")
        return []

    if "items" not in addresses:
        logger.warning(f"No global addresses found: {addresses}")
        return []

    results = []
    for address in addresses.get("items", []):
        self_link = address["selfLink"]
        name = address["name"]
        display = name

        results.append(
            Resource(
                id=make_id(address["id"]),
                meta=GCPMeta(
                    name=name,
                    display=display,
                    kind="global-addresses",
                    project=project,
                    self_link=self_link,
                    platform="gcp",
                    category="loadbalancer",
                ),
                struct=address,
            )
        )

    return results


async def explore_regional_addresses(
    c: AuthorizedSession, project: str, location: str
) -> list[Resource]:
    response = await c.get(
        f"/compute/v1/projects/{project}/regions/{location}/addresses"
    )

    addresses = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"Regional Address API access failure: {addresses}")
        return []

    if "items" not in addresses:
        logger.warning(f"No regional addresses found: {addresses}")
        return []

    results = []
    for address in addresses.get("items", []):
        self_link = address["selfLink"]
        name = address["name"]
        display = name

        results.append(
            Resource(
                id=make_id(address["id"]),
                meta=GCPMeta(
                    name=name,
                    display=display,
                    kind="regional-addresses",
                    project=project,
                    region=location,
                    self_link=self_link,
                    platform="gcp",
                    category="loadbalancer",
                ),
                struct=address,
            )
        )

    return results
