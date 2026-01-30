# mypy: disable-error-code="union-attr"
import asyncio
import logging

import msgspec
from google.oauth2._service_account_async import Credentials

from lueur.make_id import make_id
from lueur.models import GCPMeta, Resource
from lueur.platform.gcp.client import AuthorizedSession, Client

__all__ = ["explore_target_proxies"]
logger = logging.getLogger("lueur.lib")


async def explore_target_proxies(
    project: str, location: str | None = None, creds: Credentials | None = None
) -> list[Resource]:
    resources = []

    tasks: list[asyncio.Task] = []

    async with Client("https://compute.googleapis.com", creds) as c:
        async with asyncio.TaskGroup() as tg:
            if location:
                tasks.append(
                    tg.create_task(
                        explore_regional_http_target_proxies(
                            c, project, location
                        )
                    )
                )
                tasks.append(
                    tg.create_task(
                        explore_regional_https_target_proxies(
                            c, project, location
                        )
                    )
                )
            else:
                tasks.append(
                    tg.create_task(
                        explore_global_http_target_proxies(c, project)
                    )
                )
                tasks.append(
                    tg.create_task(
                        explore_global_https_target_proxies(c, project)
                    )
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
async def explore_global_http_target_proxies(
    c: AuthorizedSession, project: str
) -> list[Resource]:
    response = await c.get(
        f"/compute/v1/projects/{project}/global/targetHttpProxies"
    )

    proxies = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"Target Proxy API access failure: {proxies}")
        return []

    if "items" not in proxies:
        logger.warning(f"No global HTTP proxies found: {proxies}")
        return []

    results = []
    for proxy in proxies.get("items", []):
        self_link = proxy["selfLink"]
        name = proxy["name"]
        display = name

        results.append(
            Resource(
                id=make_id(proxy["id"]),
                meta=GCPMeta(
                    name=name,
                    display=display,
                    kind="global-target-http-proxies",
                    project=project,
                    self_link=self_link,
                    platform="gcp",
                    category="loadbalancer",
                ),
                struct=proxy,
            )
        )

    return results


async def explore_regional_http_target_proxies(
    c: AuthorizedSession, project: str, location: str
) -> list[Resource]:
    response = await c.get(
        f"/compute/v1/projects/{project}/regions/{location}/targetHttpProxies"
    )

    proxies = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"Target Proxy API access failure: {proxies}")
        return []

    if "items" not in proxies:
        logger.warning(f"No regional HTTP proxies found: {proxies}")
        return []

    results = []
    for proxy in proxies.get("items", []):
        self_link = proxy["selfLink"]
        name = proxy["name"]
        display = name

        results.append(
            Resource(
                id=make_id(proxy["id"]),
                meta=GCPMeta(
                    name=name,
                    display=display,
                    kind="regional-target-http-proxies",
                    project=project,
                    region=location,
                    self_link=self_link,
                    platform="gcp",
                    category="loadbalancer",
                ),
                struct=proxy,
            )
        )

    return results


async def explore_global_https_target_proxies(
    c: AuthorizedSession, project: str
) -> list[Resource]:
    response = await c.get(
        f"/compute/v1/projects/{project}/global/targetHttpsProxies"
    )

    proxies = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"Target Proxy API access failure: {proxies}")
        return []

    if "items" not in proxies:
        logger.warning(f"No global HTTPs proxies found: {proxies}")
        return []

    results = []
    for proxy in proxies.get("items", []):
        self_link = proxy["selfLink"]
        name = proxy["name"]
        display = name

        results.append(
            Resource(
                id=make_id(proxy["id"]),
                meta=GCPMeta(
                    name=name,
                    display=display,
                    kind="global-target-https-proxies",
                    project=project,
                    self_link=self_link,
                    platform="gcp",
                    category="loadbalancer",
                ),
                struct=proxy,
            )
        )

    return results


async def explore_regional_https_target_proxies(
    c: AuthorizedSession, project: str, location: str
) -> list[Resource]:
    response = await c.get(
        f"/compute/v1/projects/{project}/regions/{location}/targetHttpsProxies"
    )

    proxies = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"Target Proxy API access failure: {proxies}")
        return []

    if "items" not in proxies:
        logger.warning(f"No regional HTTPs proxies found: {proxies}")
        return []

    results = []
    for proxy in proxies.get("items", []):
        self_link = proxy["selfLink"]
        name = proxy["name"]
        display = name

        results.append(
            Resource(
                id=make_id(proxy["id"]),
                meta=GCPMeta(
                    name=name,
                    display=display,
                    kind="regional-target-https-proxies",
                    project=project,
                    region=location,
                    self_link=self_link,
                    platform="gcp",
                    category="loadbalancer",
                ),
                struct=proxy,
            )
        )

    return results
