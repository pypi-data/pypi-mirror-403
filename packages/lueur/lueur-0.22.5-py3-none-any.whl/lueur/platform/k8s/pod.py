# mypy: disable-error-code="call-arg"
import logging
from typing import Any

import msgspec
from kubernetes import client

from lueur.links import add_link
from lueur.make_id import make_id
from lueur.models import Discovery, K8SMeta, Link, Resource
from lueur.platform.k8s.client import AsyncClient, Client
from lueur.resource import filter_out_keys
from lueur.rules import iter_resource

__all__ = ["explore_pod"]
logger = logging.getLogger("lueur.lib")


async def explore_pod(credentials: dict[str, Any] | None) -> list[Resource]:
    resources = []

    async with Client(client.CoreV1Api, credentials=credentials) as c:
        pods = await explore_pods(c)
        resources.extend(pods)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_pods(c: AsyncClient) -> list[Resource]:
    f = "list_pod_for_all_namespaces"
    response = await c.execute(f)

    if response.status == 403:
        logger.warning("Kubernetes API server failed authentication")
        return []

    if response.status == 404:
        logger.warning(f"Kubernetes API server '{f}' not found")
        return []

    pods = msgspec.json.decode(response.data)

    if "items" not in pods:
        logger.warning(f"No pods found: {pods}")
        return []

    results = []
    for pod in pods["items"]:
        meta = pod["metadata"]
        results.append(
            Resource(
                id=make_id(meta["uid"]),
                meta=K8SMeta(
                    name=meta["name"],
                    display=meta["name"],
                    kind="pod",
                    platform="k8s",
                    ns=meta["namespace"],
                    category="compute",
                ),
                struct=filter_out_keys(
                    pod, keys=[["metadata", "managedFields"]]
                ),
            )
        )

    return results


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    for pod_name in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='pod' && @.meta.platform=='k8s'].meta.name",
    ):
        resource = pod_name.parent.parent.obj  # type: ignore
        r_id = resource["id"]  # type: ignore
        node_name = resource["struct"]["spec"]["nodeName"]  # type: ignore

        p = f"$.resources[?@.meta.kind=='node' && @.meta.name=='{node_name}']"
        for node in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="node",
                    path=node.path,
                    pointer=str(node.pointer()),
                    id=node.obj["id"],  # type: ignore
                ),
            )
