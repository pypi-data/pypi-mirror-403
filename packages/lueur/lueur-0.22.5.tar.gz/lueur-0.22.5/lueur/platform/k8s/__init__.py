import asyncio
import logging
import secrets
from typing import Any, Literal, Sequence, cast

from lueur.make_id import make_id
from lueur.models import Discovery, Meta
from lueur.platform.k8s.dependency import (
    expand_links as dependency_expand_links,
)
from lueur.platform.k8s.dependency import explore_flow_dependencies
from lueur.platform.k8s.deployment import (
    expand_links as deployment_expand_links,
)
from lueur.platform.k8s.deployment import explore_deployment
from lueur.platform.k8s.gateway import expand_links as gateway_expand_links
from lueur.platform.k8s.gateway import explore_gateway
from lueur.platform.k8s.ingress import explore_ingress
from lueur.platform.k8s.network_policy import explore_network_policy
from lueur.platform.k8s.node import expand_links as node_expand_links
from lueur.platform.k8s.node import explore_node
from lueur.platform.k8s.pod import expand_links as pod_expand_links
from lueur.platform.k8s.pod import explore_pod
from lueur.platform.k8s.replicaset import (
    expand_links as replicaset_expand_links,
)
from lueur.platform.k8s.replicaset import explore_replicaset
from lueur.platform.k8s.service import expand_links as svc_expand_links
from lueur.platform.k8s.service import explore_service

__all__ = ["explore", "expand_links"]
logger = logging.getLogger("lueur.lib")


Targets = (
    "node",
    "pod",
    "replicaset",
    "deployment",
    "ingress",
    "service",
    "network_policy",
    "gateway",
    "dependency",
)


async def explore(
    include: Sequence[
        Literal[
            "node",
            "pod",
            "replicaset",
            "deployment",
            "ingress",
            "service",
            "network_policy",
            "gateway",
            "dependency",
        ]
    ]
    | None = None,
    dependency_endpoint: str | None = None,
    credentials: dict[str, Any] | None = None,
) -> Discovery:
    resources = []
    tasks: list[asyncio.Task] = []

    if include is None:
        include = cast(Sequence, Targets)

    async with asyncio.TaskGroup() as tg:
        try:
            if "node" in include:
                tasks.append(
                    tg.create_task(explore_node(credentials=credentials))
                )
        except Exception:
            logger.error("Failed to explore Kubernetes nodes", exc_info=True)

        try:
            if "pod" in include:
                tasks.append(
                    tg.create_task(explore_pod(credentials=credentials))
                )
        except Exception:
            logger.error("Failed to explore Kubernetes pods", exc_info=True)

        try:
            if "replicaset" in include:
                tasks.append(
                    tg.create_task(explore_replicaset(credentials=credentials))
                )
        except Exception:
            logger.error(
                "Failed to explore Kubernetes replicasets", exc_info=True
            )

        try:
            if "deployment" in include:
                tasks.append(
                    tg.create_task(explore_deployment(credentials=credentials))
                )
        except Exception:
            logger.error(
                "Failed to explore Kubernetes deployments", exc_info=True
            )

        try:
            if "ingress" in include:
                tasks.append(
                    tg.create_task(explore_ingress(credentials=credentials))
                )
        except Exception:
            logger.error(
                "Failed to explore Kubernetes ingresses", exc_info=True
            )

        try:
            if "service" in include:
                tasks.append(
                    tg.create_task(explore_service(credentials=credentials))
                )
        except Exception:
            logger.error("Failed to explore Kubernetes services", exc_info=True)

        try:
            if "network_policy" in include:
                tasks.append(
                    tg.create_task(
                        explore_network_policy(credentials=credentials)
                    )
                )
        except Exception:
            logger.error(
                "Failed to explore Kubernetes network policies", exc_info=True
            )

        try:
            if "gateway" in include:
                tasks.append(
                    tg.create_task(explore_gateway(credentials=credentials))
                )
        except Exception:
            logger.error("Failed to explore Kubernetes gateways", exc_info=True)

        try:
            if dependency_endpoint and "dependency" in include:
                tasks.append(
                    tg.create_task(
                        explore_flow_dependencies(dependency_endpoint)
                    )
                )
        except Exception:
            logger.error(
                "Failed to explore Kubernetes dependencies", exc_info=True
            )

    for task in tasks:
        result = task.result()
        if result is None:
            continue
        resources.extend(result)

    name = secrets.token_hex(8)

    return Discovery(
        id=make_id(name),
        resources=resources,
        meta=Meta(name=name, display="Kubernetes", kind="k8s", category=None),
    )


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    deployment_expand_links(d, serialized)
    gateway_expand_links(d, serialized)
    node_expand_links(d, serialized)
    pod_expand_links(d, serialized)
    svc_expand_links(d, serialized)
    replicaset_expand_links(d, serialized)
    dependency_expand_links(d, serialized)
