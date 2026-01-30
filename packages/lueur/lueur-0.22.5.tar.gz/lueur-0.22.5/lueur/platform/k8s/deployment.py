# mypy: disable-error-code="call-arg,index"
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

__all__ = ["explore_deployment"]
logger = logging.getLogger("lueur.lib")


async def explore_deployment(
    credentials: dict[str, Any] | None,
) -> list[Resource]:
    resources = []

    async with Client(client.AppsV1Api, credentials=credentials) as c:
        pods = await explore_deployments(c)
        resources.extend(pods)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_deployments(c: AsyncClient) -> list[Resource]:
    f = "list_deployment_for_all_namespaces"
    response = await c.execute(f)

    if response.status == 403:
        logger.warning("Kubernetes API server failed authentication")
        return []

    if response.status == 404:
        logger.warning(f"Kubernetes API server '{f}' not found")
        return []

    deployments = msgspec.json.decode(response.data)

    if "items" not in deployments:
        logger.warning(f"No deployments found: {deployments}")
        return []

    results = []
    for deployment in deployments["items"]:
        meta = deployment["metadata"]
        results.append(
            Resource(
                id=make_id(meta["uid"]),
                meta=K8SMeta(
                    name=meta["name"],
                    display=meta["name"],
                    kind="deployment",
                    platform="k8s",
                    ns=meta["namespace"],
                    category="compute",
                ),
                struct=filter_out_keys(
                    deployment, keys=[["metadata", "managedFields"]]
                ),
            )
        )

    return results


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    for deployment in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='deployment' && @.meta.platform=='k8s'].meta.name",  # noqa: E501
    ):
        r_id = deployment.parent.parent.obj["id"]  # type: ignore
        name: str = deployment.value  # type: ignore
        ns = deployment.parent.parent.obj["meta"]["ns"]  # type: ignore

        add_rs_links(d, serialized, r_id, name, ns)


def add_rs_links(
    d: Discovery,
    serialized: dict[str, Any],
    deployment_resource_id: str,
    deployment_name: str,
    deployment_ns: str,
) -> None:
    p = f"$.resources[?@.meta.kind=='replicaset'].struct.metadata.ownerReferences[?@.kind=='Deployment' && @.name=='{deployment_name}']"  # noqa E501
    for ownerRef in iter_resource(serialized, p):
        rs = ownerRef.parent.parent.parent.parent  # type: ignore
        add_link(
            d,
            deployment_resource_id,
            Link(
                direction="out",
                kind="replicaset",
                id=rs.obj["id"],  # type: ignore
                path=rs.path,  # type: ignore
                pointer=str(rs.pointer()),  # type: ignore
            ),
        )

        rs_name = rs.obj["meta"]["name"]  # type: ignore

        add_pod_links(
            d, serialized, deployment_resource_id, rs_name, deployment_ns
        )


def add_pod_links(
    d: Discovery,
    serialized: dict[str, Any],
    deployment_resource_id: str,
    rs_name: str,
    rs_ns: str,
) -> None:
    p = f"$.resources[?@.meta.kind=='pod'].struct.metadata.ownerReferences[?@.kind=='ReplicaSet' && @.name=='{rs_name}']"  # noqa E501
    for ownerRef in iter_resource(serialized, p):
        po = ownerRef.parent.parent.parent.parent  # type: ignore
        add_link(
            d,
            deployment_resource_id,
            Link(
                direction="out",
                kind="pod",
                id=po.obj["id"],  # type: ignore
                path=po.path,  # type: ignore
                pointer=str(po.pointer()),  # type: ignore
            ),
        )

        node_ip = po.obj["struct"]["status"]["hostIP"]  # type: ignore
        pod_id = po.obj["id"]  # type: ignore

        add_node_links(d, serialized, deployment_resource_id, node_ip)
        add_service_links(d, serialized, deployment_resource_id, pod_id, rs_ns)


def add_node_links(
    d: Discovery,
    serialized: dict[str, Any],
    deployment_resource_id: str,
    node_ip: str,
) -> None:
    p = f"$.resources[?@.meta.kind=='node'].struct.status.addresses[?@address=='{node_ip}']"  # noqa E501
    for addr in iter_resource(serialized, p):
        node = addr.parent.parent.parent.parent  # type: ignore
        add_link(
            d,
            deployment_resource_id,
            Link(
                direction="out",
                kind="node",
                id=node.obj["id"],  # type: ignore
                path=node.path,  # type: ignore
                pointer=str(node.pointer()),  # type: ignore
            ),
        )


def add_service_links(
    d: Discovery,
    serialized: dict[str, Any],
    deployment_resource_id: str,
    pod_id: str,
    pod_ns: str,
) -> None:
    for svc in iter_resource(
        serialized,
        f"$.resources[?@.meta.kind=='service' && @.meta.platform=='k8s' && @.meta.ns=='{pod_ns}']",  # noqa: E501
    ):
        selectors = svc.obj["struct"]["spec"].get("selector")
        if not selectors:
            continue

        labels = " && ".join(
            [
                f"@.struct.metadata.labels.['{k}']=='{v}'"
                for k, v in selectors.items()
            ]
        )  # noqa: E501

        p = f"$.resources[?@.id=='{pod_id}' && @.meta.kind=='pod' && @.meta.ns=='{pod_ns}' && {labels}]"  # noqa: E501
        for pod in iter_resource(serialized, p):
            add_link(
                d,
                deployment_resource_id,
                Link(
                    direction="out",
                    kind="service",
                    id=svc.obj["id"],
                    path=svc.path,
                    pointer=str(svc.pointer()),
                ),
            )

            break

        svc_name = svc.obj["meta"]["name"]

        p = f"$.resources[?@.meta.kind=='httproute'].struct.spec.rules.*.backendRefs[?@.kind=='Service' && @.name=='{svc_name}']"  # noqa: E501
        for httproute in iter_resource(serialized, p):
            httproute = httproute.parent.parent.parent.parent.parent.parent  # type: ignore

            add_link(
                d,
                deployment_resource_id,
                Link(
                    direction="out",
                    kind="httproute",
                    id=httproute.obj["id"],
                    path=httproute.path,
                    pointer=str(httproute.pointer()),
                ),
            )

            for gw in httproute.obj["struct"]["spec"]["parentRefs"]:
                if gw["kind"] != "Gateway":
                    continue

                gw_name = gw["name"]
                p = f"$.resources[?@.meta.kind=='gateway' && @.meta.display=='{gw_name}']"  # noqa: E501
                for gw in iter_resource(serialized, p):
                    add_link(
                        d,
                        deployment_resource_id,
                        Link(
                            direction="out",
                            kind="gateway",
                            id=gw.obj["id"],
                            path=gw.path,
                            pointer=str(gw.pointer()),
                        ),
                    )

            break
