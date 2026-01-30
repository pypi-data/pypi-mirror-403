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

__all__ = ["explore_gateway"]
logger = logging.getLogger("lueur.lib")


async def explore_gateway(credentials: dict[str, Any] | None) -> list[Resource]:
    resources = []

    async with Client(client.CoreV1Api, credentials=credentials) as c:
        namespaces = await list_all_namespaces(c)

    async with Client(client.CustomObjectsApi, credentials=credentials) as c:
        for ns in namespaces:
            gateways = await explore_namespaced_gateways(c, ns, "v1")
            resources.extend(gateways)

            # gateways = await explore_namespaced_gateways(c, ns, "v1beta1")
            # resources.extend(gateways)

            gateways = await explore_namespaced_http_routes(c, ns, "v1")
            resources.extend(gateways)

            # gateways = await explore_namespaced_http_routes(c, ns, "v1beta1")
            # resources.extend(gateways)

    return resources


###############################################################################
# Private functions
###############################################################################
async def list_all_namespaces(c: AsyncClient) -> list[str]:
    response = await c.execute("list_namespace")

    namespaces = msgspec.json.decode(response.data)

    return [ns["metadata"]["name"] for ns in namespaces["items"]]


async def explore_namespaced_gateways(
    c: AsyncClient, ns: str, api_version: str = "v1"
) -> list[Resource]:
    f = "list_namespaced_custom_object"
    response = await c.execute(
        f,
        group="gateway.networking.k8s.io",
        version=api_version,
        plural="gateways",
        namespace=ns,
    )

    if response.status == 403:
        logger.warning("Kubernetes API server failed authentication")
        return []

    if response.status == 404:
        logger.warning(
            f"Kubernetes Gateways ({api_version}) not found in ns '{ns}'"
        )
        return []

    gateways = msgspec.json.decode(response.data)

    if "items" not in gateways:
        logger.warning(f"No gateways found: {gateways}")
        return []

    results = []
    for gw in gateways["items"]:
        meta = gw["metadata"]
        spec = gw["spec"]

        results.append(
            Resource(
                id=make_id(meta["uid"]),
                meta=K8SMeta(
                    name=f"{spec['gatewayClassName']}/{meta['name']}",
                    display=meta["name"],
                    kind="gateway",
                    platform="k8s",
                    ns=meta["namespace"],
                    category="loadbalancer",
                ),
                struct=filter_out_keys(
                    gw, keys=[["metadata", "managedFields"]]
                ),
            )
        )

    return results


async def explore_namespaced_http_routes(
    c: AsyncClient, ns: str, api_version: str = "v1"
) -> list[Resource]:
    f = "list_namespaced_custom_object"
    response = await c.execute(
        f,
        group="gateway.networking.k8s.io",
        version=api_version,
        plural="httproutes",
        namespace=ns,
    )

    if response.status == 403:
        logger.warning(
            f"Kubernetes HTTPRoutes ({api_version}) not found in ns '{ns}'"
        )
        return []

    if response.status == 404:
        logger.warning(f"Kubernetes API server '{f}' not found")
        return []

    routes = msgspec.json.decode(response.data)

    if "items" not in routes:
        logger.warning(f"No gateway routes found: {routes}")
        return []

    results = []
    for route in routes["items"]:
        meta = route["metadata"]

        results.append(
            Resource(
                id=make_id(meta["uid"]),
                meta=K8SMeta(
                    name=f"{meta['namespace']}/{meta['name']}",
                    display=meta["name"],
                    kind="httproute",
                    platform="k8s",
                    ns=meta["namespace"],
                    category="loadbalancer",
                ),
                struct=route,
            )
        )

    return results


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    for annotation in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='gateway'].struct.metadata.annotations['networking.gke.io/backend-services']",  # noqa E501
    ):
        r_id = annotation.parent.parent.parent.parent.obj["id"]  # type: ignore
        name = annotation.value.rsplit("/", 1)[-1]  # type: ignore

        p = f"$.resources[?@.meta.kind=='service' && @.struct.cloudRun.serviceName=='{name}']"  # noqa E501
        for svc in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="service",
                    path=svc.path,
                    pointer=str(svc.pointer()),
                    id=svc.obj["id"],
                ),
            )

            svc_name = svc.obj["meta"]["name"]

            p = f"$.resources[?@.meta.kind=='slo' && match(@.meta.name, '{svc_name}/serviceLevelObjectives/.*')]"  # noqa E501
            for slo in iter_resource(serialized, p):
                add_link(
                    d,
                    r_id,
                    Link(
                        direction="out",
                        kind="slo",
                        path=slo.path,
                        pointer=str(slo.pointer()),
                        id=slo.obj["id"],
                    ),
                )

    for urlmap in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='gateway'].struct.metadata.annotations['networking.gke.io/url-maps']",  # noqa E501
    ):
        r_id = urlmap.parent.parent.parent.parent.obj["id"]  # type: ignore
        name = urlmap.value.rsplit("/", 1)[-1]  # type: ignore

        p = f"$.resources[?@.meta.kind=='global-urlmap' && @.meta.name=='{name}']"  # noqa E501
        for urlmap in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="global-urlmap",
                    path=urlmap.path,
                    pointer=str(urlmap.pointer()),
                    id=urlmap.obj["id"],
                ),
            )

    for gw_name in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='httproute' && @.meta.platform=='k8s'].struct.spec.parentRefs[?@.kind=='Gateway'].name",  # noqa E501
    ):
        r_id = gw_name.parent.parent.parent.parent.parent.obj["id"]  # type: ignore
        name = gw_name.value

        p = f"$.resources[?@.meta.kind=='gateway' && @.meta.platform=='k8s' && @.meta.name=='{name}']"  # noqa E501
        for gw in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="in",
                    kind="gateway",
                    path=gw.path,
                    pointer=str(gw.pointer()),
                    id=gw.obj["id"],
                ),
            )

    for gw_name in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='gateway' && @.meta.platform=='k8s'].meta.name",  # noqa E501
    ):
        r_id = gw_name.parent.parent.obj["id"]  # type: ignore
        name = gw_name.value

        p = f"$.resources[?@.meta.kind=='httproute' && @.meta.platform=='k8s'].struct.spec.parentRefs[?@.kind=='Gateway' && @.name=='{name}']"  # noqa E501
        for httproute in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="httproute",
                    path=httproute.path,
                    pointer=str(httproute.pointer()),
                    id=httproute.obj["id"],
                ),
            )

    for service_refs in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='httproute' && @.meta.platform=='k8s'].struct.spec.rules.*.backendRefs[?@.kind=='Service']",  # noqa E501
    ):
        r_id = service_refs.parent.parent.parent.parent.parent.parent.obj["id"]  # type: ignore
        svc_ref = service_refs.obj
        svc_name = svc_ref["name"]
        svc_ns = svc_ref["namespace"]

        p = f"$.resources[?@.meta.kind=='service' && @.meta.platform=='k8s' && @.meta.ns=='{svc_ns}' && @.meta.name=='{svc_name}']"  # noqa E501
        for svc in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="service",
                    path=svc.path,
                    pointer=str(svc.pointer()),
                    id=svc.obj["id"],
                ),
            )
