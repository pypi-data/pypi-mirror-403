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

__all__ = ["explore_replicaset"]
logger = logging.getLogger("lueur.lib")


async def explore_replicaset(
    credentials: dict[str, Any] | None,
) -> list[Resource]:
    resources = []

    async with Client(client.AppsV1Api, credentials=credentials) as c:
        rs = await explore_replicasets(c)
        resources.extend(rs)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_replicasets(c: AsyncClient) -> list[Resource]:
    f = "list_replica_set_for_all_namespaces"
    response = await c.execute(f)

    if response.status == 403:
        logger.warning("Kubernetes API server failed authentication")
        return []

    if response.status == 404:
        logger.warning(f"Kubernetes API server '{f}' not found")
        return []

    replicasets = msgspec.json.decode(response.data)

    if "items" not in replicasets:
        logger.warning(f"No replicasets found: {replicasets}")
        return []

    results = []
    for rs in replicasets["items"]:
        meta = rs["metadata"]
        results.append(
            Resource(
                id=make_id(meta["uid"]),
                meta=K8SMeta(
                    name=meta["name"],
                    display=meta["name"],
                    kind="replicaset",
                    platform="k8s",
                    ns=meta["namespace"],
                    category="compute",
                ),
                struct=filter_out_keys(
                    rs, keys=[["metadata", "managedFields"]]
                ),
            )
        )

    return results


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    for rs in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='replicaset' && @.meta.platform=='k8s'].meta.name",  # noqa: E501
    ):
        r_id = rs.parent.parent.obj["id"]  # type: ignore
        name = rs.value

        p = f"$.resources[?@.meta.kind=='pod'].struct.metadata.ownerReferences[?@.kind=='ReplicaSet' && @.name=='{name}']"  # noqa E501
        for ownerRef in iter_resource(serialized, p):
            pod = ownerRef.parent.parent.parent.parent  # type: ignore
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="pod",
                    path=pod.path,  # type: ignore
                    pointer=str(pod.pointer()),  # type: ignore
                    id=pod.obj["id"],  # type: ignore
                ),
            )
