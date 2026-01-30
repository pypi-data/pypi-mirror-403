# mypy: disable-error-code="union-attr"
import logging

import msgspec
from google.oauth2._service_account_async import Credentials

from lueur.make_id import make_id
from lueur.models import GCPMeta, Resource
from lueur.platform.gcp.client import AuthorizedSession, Client

__all__ = ["explore_firewalls"]
logger = logging.getLogger("lueur.lib")


async def explore_firewalls(
    project: str, location: str | None = None, creds: Credentials | None = None
) -> list[Resource]:
    resources = []

    async with Client("https://compute.googleapis.com", creds) as c:
        firewalls = await explore_global_firewalls(c, project)
        resources.extend(firewalls)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_global_firewalls(
    c: AuthorizedSession, project: str
) -> list[Resource]:
    response = await c.get(f"/compute/v1/projects/{project}/global/firewalls")

    firewalls = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"Firewall API access failure: {firewalls}")
        return []

    if "items" not in firewalls:
        logger.warning(f"No global firewalls found: {firewalls}")
        return []

    results = []
    for firewall in firewalls.get("items", []):
        self_link = firewall["selfLink"]
        name = firewall["name"]
        display = name

        results.append(
            Resource(
                id=make_id(firewall["id"]),
                meta=GCPMeta(
                    name=name,
                    display=display,
                    kind="global-firewalls",
                    project=project,
                    self_link=self_link,
                    platform="gcp",
                    category="security",
                ),
                struct=firewall,
            )
        )

    return results
