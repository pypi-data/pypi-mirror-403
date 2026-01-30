# mypy: disable-error-code="index,call-arg,union-attr"
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

__all__ = ["explore_node"]
logger = logging.getLogger("lueur.lib")


async def explore_node(credentials: dict[str, Any] | None) -> list[Resource]:
    resources = []

    async with Client(client.CoreV1Api, credentials=credentials) as c:
        nodes = await explore_nodes(c)
        resources.extend(nodes)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_nodes(c: AsyncClient) -> list[Resource]:
    f = "list_node"
    response = await c.execute(f)

    if response.status == 403:
        logger.warning("Kubernetes API server failed authentication")
        return []

    if response.status == 404:
        logger.warning(f"Kubernetes API server '{f}' not found")
        return []

    nodes = msgspec.json.decode(response.data)

    if "items" not in nodes:
        logger.warning(f"No nodes found: {nodes}")
        return []

    results = []
    for node in nodes["items"]:
        meta = node["metadata"]
        results.append(
            Resource(
                id=make_id(meta["uid"]),
                meta=K8SMeta(
                    name=meta["name"],
                    display=meta["name"],
                    kind="node",
                    platform="k8s",
                    category="compute",
                ),
                struct=filter_out_keys(
                    node, keys=[["metadata", "managedFields"]]
                ),
            )
        )

    return results


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    for np in iter_resource(
        serialized, "$.resources[?@.meta.kind=='nodepool'].meta.name"
    ):
        r_id = np.parent.parent.obj["id"]
        name = np.value
        p = f"$.resources[?@.meta.kind=='node' && @.struct.metadata.labels.['cloud.google.com/gke-nodepool']=='{name}']"  # noqa E501
        for k8snode in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="node",
                    path=k8snode.path,
                    pointer=str(k8snode.pointer()),
                    id=k8snode.obj["id"],
                ),
            )

    for node_name in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='node' && @.meta.platform=='k8s'].meta.name",
    ):
        resource = node_name.parent.parent.obj
        r_id = resource["id"]
        node_name = node_name.value  # type: ignore

        p = f"$.resources[?@.meta.kind=='pod' && @.meta.platform=='k8s' && @.struct.spec.nodeName=='{node_name}']"  # noqa: E501
        for pod in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="pod",
                    path=pod.path,
                    pointer=str(pod.pointer()),
                    id=pod.obj["id"],
                ),
            )
