# mypy: disable-error-code="call-arg"
import logging
from typing import Any

import msgspec
from kubernetes import client

from lueur.make_id import make_id
from lueur.models import K8SMeta, Resource
from lueur.platform.k8s.client import AsyncClient, Client
from lueur.resource import filter_out_keys

__all__ = ["explore_network_policy"]
logger = logging.getLogger("lueur.lib")


async def explore_network_policy(
    credentials: dict[str, Any] | None,
) -> list[Resource]:
    resources = []

    async with Client(client.NetworkingV1Api, credentials=credentials) as c:
        policies = await explore_network_policies(c)
        resources.extend(policies)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_network_policies(c: AsyncClient) -> list[Resource]:
    f = "list_network_policy_for_all_namespaces"
    response = await c.execute(f)

    if response.status == 403:
        logger.warning("Kubernetes API server failed authentication")
        return []

    if response.status == 404:
        logger.warning(f"Kubernetes API server '{f}' not found")
        return []

    policies = msgspec.json.decode(response.data)

    if "items" not in policies:
        logger.warning(f"No network policies found: {policies}")
        return []

    results = []
    for policy in policies["items"]:
        meta = policy["metadata"]
        results.append(
            Resource(
                id=make_id(meta["uid"]),
                meta=K8SMeta(
                    name=meta["name"],
                    display=meta["name"],
                    kind="network-policy",
                    platform="k8s",
                    namespace=meta.get("namespace"),
                    category="security",
                ),
                struct=filter_out_keys(
                    policy, keys=[["metadata", "managedFields"]]
                ),
            )
        )

    return results
