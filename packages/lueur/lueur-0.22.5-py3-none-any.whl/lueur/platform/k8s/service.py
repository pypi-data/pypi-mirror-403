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

__all__ = ["explore_service", "expand_links"]
logger = logging.getLogger("lueur.lib")


async def explore_service(credentials: dict[str, Any] | None) -> list[Resource]:
    resources = []

    async with Client(client.CoreV1Api, credentials=credentials) as c:
        services = await explore_services(c)
        resources.extend(services)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_services(c: AsyncClient) -> list[Resource]:
    f = "list_service_for_all_namespaces"
    response = await c.execute(f)

    if response.status == 403:
        logger.warning("Kubernetes API server failed authentication")
        return []

    if response.status == 404:
        logger.warning(f"Kubernetes API server '{f}' not found")
        return []

    services = msgspec.json.decode(response.data)

    if "items" not in services:
        logger.warning(f"No services found: {services}")
        return []

    results = []
    for service in services["items"]:
        meta = service["metadata"]
        results.append(
            Resource(
                id=make_id(meta["uid"]),
                meta=K8SMeta(
                    name=meta["name"],
                    display=meta["name"],
                    kind="service",
                    platform="k8s",
                    ns=meta["namespace"],
                    category="network",
                ),
                struct=filter_out_keys(
                    service, keys=[["metadata", "managedFields"]]
                ),
            )
        )

    return results


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    for svc_name in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='service' && @.meta.platform=='k8s'].meta.name",  # noqa: E501
    ):
        svc = svc_name.parent.parent  # type: ignore
        r_id = svc.obj["id"]  # type: ignore
        ns = svc.obj["meta"]["ns"]  # type: ignore
        selectors = svc.obj["struct"]["spec"].get("selector")  # type: ignore
        if not selectors:
            continue

        labels = " && ".join(
            [
                f"@.struct.metadata.labels.['{k}']=='{v}'"
                for k, v in selectors.items()
            ]
        )  # noqa: E501
        p = f"$.resources[?@.meta.kind=='pod' && @.meta.ns=='{ns}' && {labels}]"

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
