# mypy: disable-error-code="call-arg,index"
import logging
from typing import Any, Literal

import httpx
import jsonpath
import msgspec

from lueur.links import add_link
from lueur.make_id import make_id
from lueur.models import Discovery, Link, Meta, Resource
from lueur.rules import iter_resource

__all__ = ["explore_flow_dependencies", "expand_links"]
logger = logging.getLogger("lueur.lib")


async def explore_flow_dependencies(k8packet_address: str) -> list[Resource]:
    resource = await explore_k8packet(k8packet_address)
    if not resource:
        return []

    return [resource]


###############################################################################
# Private functions
###############################################################################
async def explore_k8packet(k8packet_address: str) -> Resource | None:
    async with httpx.AsyncClient(base_url=k8packet_address) as c:
        response = await c.get("/nodegraph/api/graph/fields")

        if response.status_code == 404:
            logger.warning("k8spacket not found. Please install k8packet")
            return None

        fields = msgspec.json.decode(response.content)

        response = await c.get("/nodegraph/api/graph/data")

        if response.status_code == 404:
            logger.warning("k8spacket not found. Please install k8packet")
            return None

        graph = msgspec.json.decode(response.content)

        response = await c.get("/nodegraph/connections")

        if response.status_code == 404:
            logger.warning("k8spacket not found. Please install k8packet")
            return None

        conn = msgspec.json.decode(response.content)

        return Resource(
            id=make_id(k8packet_address),
            meta=Meta(
                name="flow-dependency",
                display="Flow Dependency",
                kind="dependency",
                platform="k8s",
                category="network",
            ),
            struct={"fields": fields, "graph": graph, "connections": conn},
        )


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    for dependency in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='dependency' && @.meta.platform=='k8s']",  # noqa: E501
    ):
        graph = dependency.value["struct"]["graph"]
        seen_resources = {}

        nodes = {}
        for node in graph["nodes"]:
            nodes[node["id"]] = node["title"]

        for edge in graph["edges"]:
            source_ip = edge["source"]
            target_ip = edge["target"]
            src_name = nodes.get(source_ip)
            dst_name = nodes.get(target_ip)

            if not src_name or not dst_name:
                continue

            if not src_name.startswith(("pod.", "svc.", "node.")):
                continue

            if not dst_name.startswith(("pod.", "svc.", "node.")):
                continue

            source_resource: jsonpath.JSONPathMatch | None = None
            source_type: Literal["pod", "node"] = "pod"
            if src_name.startswith("pod."):
                source_type = "pod"
                if source_ip not in seen_resources:
                    p = f"$.resources[?@.meta.kind=='pod' && @.struct.status.podIP=='{source_ip}']"  # noqa: E501
                    source_resource = next(  # type: ignore
                        iter_resource(serialized, p), None
                    )

                    if source_resource:
                        seen_resources[source_ip] = source_resource

                if not source_resource:
                    source_resource = seen_resources.get(source_ip)

            if src_name.startswith("node."):
                source_type = "node"
                if source_ip not in seen_resources:
                    p = f"$.resources[?@.meta.kind=='node'].struct.status.addresses[?@.address=='{source_ip}']"  # noqa: E501
                    source_resource = next(  # type: ignore
                        iter_resource(serialized, p), None
                    )

                    if source_resource:
                        source_resource = (
                            source_resource.parent.parent.parent.parent  # type: ignore
                        )
                        seen_resources[source_ip] = source_resource

                if not source_resource:
                    source_resource = seen_resources.get(source_ip)

            if not source_resource:
                continue

            if dst_name.startswith("pod."):
                target_pod = None
                if target_ip not in seen_resources:
                    p = f"$.resources[?@.meta.kind=='pod' && @.struct.status.podIP=='{target_ip}']"  # noqa: E501
                    target_pod = next(  # type: ignore
                        iter_resource(serialized, p), None
                    )

                    if target_pod:
                        seen_resources[target_ip] = target_pod

                if not target_pod:
                    target_pod = seen_resources.get(target_ip)

                if target_pod:
                    add_link(
                        d,
                        source_resource.obj["id"],
                        Link(
                            direction="out",
                            kind="pod",
                            path=target_pod.path,
                            pointer=str(target_pod.pointer()),
                            id=target_pod.obj["id"],
                        ),
                    )

                    add_link(
                        d,
                        target_pod.obj["id"],
                        Link(
                            direction="in",
                            kind=source_type,
                            path=source_resource.path,
                            pointer=str(source_resource.pointer()),
                            id=source_resource.obj["id"],
                        ),
                    )

            if dst_name.startswith("svc."):
                target_svc = None
                if target_ip not in seen_resources:
                    p = f"$.resources[?@.meta.kind=='service' && @.struct.spec.clusterIP=='{target_ip}']"  # noqa: E501
                    target_svc = next(  # type: ignore
                        iter_resource(serialized, p), None
                    )

                    if target_svc:
                        seen_resources[target_ip] = target_svc

                if not target_svc:
                    target_svc = seen_resources.get(target_ip)

                if target_svc:
                    add_link(
                        d,
                        target_svc.obj["id"],
                        Link(
                            direction="out",
                            kind="service",
                            path=source_resource.path,
                            pointer=str(source_resource.pointer()),
                            id=source_resource.obj["id"],
                        ),
                    )

                    add_link(
                        d,
                        target_svc.obj["id"],
                        Link(
                            direction="in",
                            kind="pod",
                            path=source_resource.path,
                            pointer=str(source_resource.pointer()),
                            id=source_resource.obj["id"],
                        ),
                    )
