# mypy: disable-error-code="arg-type,attr-defined,index,union-attr"
import asyncio
import logging
from typing import Any, cast

import msgspec
from google.oauth2._service_account_async import Credentials

from lueur.links import add_link
from lueur.make_id import make_id
from lueur.models import Discovery, GCPMeta, Link, Resource
from lueur.platform.gcp.client import AuthorizedSession, Client
from lueur.platform.gcp.zone import list_project_zones
from lueur.rules import iter_resource

__all__ = ["explore_lb"]
logger = logging.getLogger("lueur.lib")


async def explore_lb(
    project: str, location: str | None = None, creds: Credentials | None = None
) -> list[Resource]:
    resources = []

    async with Client("https://compute.googleapis.com", creds) as c:
        tasks: list[asyncio.Task] = []

        async with asyncio.TaskGroup() as tg:
            if not location:
                tasks.append(tg.create_task(explore_global_urlmaps(c, project)))
                tasks.append(
                    tg.create_task(explore_global_backend_services(c, project))
                )
                tasks.append(
                    tg.create_task(explore_global_backend_groups(c, project))
                )
                tasks.append(
                    tg.create_task(explore_zonal_backend_groups(c, project))
                )
            else:
                tasks.append(
                    tg.create_task(
                        explore_regional_urlmaps(c, project, location)
                    )
                )
                tasks.append(
                    tg.create_task(
                        explore_regional_backend_services(c, project, location)
                    )
                )
                tasks.append(
                    tg.create_task(
                        explore_regional_backend_groups(c, project, location)
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
async def explore_global_urlmaps(
    c: AuthorizedSession, project: str
) -> list[Resource]:
    response = await c.get(
        f"/compute/v1/projects/{project}/global/urlMaps",
        params={"returnPartialSuccess": True},
    )

    urlmaps = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"URLMap API access failure: {urlmaps}")
        return []

    if "items" not in urlmaps:
        logger.warning(f"No global urlmaps found: {urlmaps}")
        return []

    results = []
    for urlmap in urlmaps.get("items", []):
        results.append(
            Resource(
                id=make_id(urlmap["id"]),
                meta=GCPMeta(
                    name=urlmap["name"],
                    display=urlmap["name"],
                    kind="global-urlmap",
                    project=project,
                    platform="gcp",
                    category="loadbalancer",
                ),
                struct=urlmap,
            )
        )

    return results


async def explore_global_backend_services(
    c: AuthorizedSession, project: str
) -> list[Resource]:
    response = await c.get(
        f"/compute/v1/projects/{project}/global/backendServices",
        params={"returnPartialSuccess": True},
    )

    backend_services = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(
            f"Backend services API access failure: {backend_services}"
        )
        return []

    if "items" not in backend_services:
        logger.warning(f"No global backend services found: {backend_services}")
        return []

    results = []
    for backend_service in backend_services.get("items", []):
        name = backend_service["name"]
        display = name
        self_link = backend_service.get("selfLink")

        results.append(
            Resource(
                id=make_id(backend_service["id"]),
                meta=GCPMeta(
                    name=name,
                    display=display,
                    kind="global-backend-service",
                    project=project,
                    platform="gcp",
                    self_link=self_link,
                    category="loadbalancer",
                ),
                struct=backend_service,
            )
        )

    return results


async def explore_global_backend_groups(
    c: AuthorizedSession, project: str
) -> list[Resource]:
    response = await c.get(
        f"/compute/v1/projects/{project}/global/networkEndpointGroups",
        params={"returnPartialSuccess": True},
    )

    backend_groups = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"Backend groups API access failure: {backend_groups}")
        return []

    if "items" not in backend_groups:
        logger.warning(f"No global backend groups found: {backend_groups}")
        return []

    results = []
    for backend_group in backend_groups.get("items", []):
        name = backend_group["name"]
        display = name
        region = backend_group.get("region")
        zone = backend_group.get("zone")
        self_link = backend_group.get("selfLink")
        if zone:
            _, zone = zone.rsplit("/", 1)

        results.append(
            Resource(
                id=make_id(backend_group["id"]),
                meta=GCPMeta(
                    name=name,
                    display=display,
                    kind="global-neg",
                    project=project,
                    region=region,
                    zone=zone,
                    platform="gcp",
                    self_link=self_link,
                    category="loadbalancer",
                ),
                struct=backend_group,
            )
        )

    return results


async def explore_regional_urlmaps(
    c: AuthorizedSession, project: str, location: str
) -> list[Resource]:
    response = await c.get(
        f"/compute/v1/projects/{project}/regions/{location}/urlMaps",
        params={"returnPartialSuccess": True},
    )

    urlmaps = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"URLMap API access failure: {urlmaps}")
        return []

    if "items" not in urlmaps:
        logger.warning(f"No regional urlmaps found: {urlmaps}")
        return []

    results = []
    for urlmap in urlmaps.get("items", []):
        self_link = urlmap.get("selfLink")

        results.append(
            Resource(
                id=make_id(urlmap["id"]),
                meta=GCPMeta(
                    name=urlmap["name"],
                    display=urlmap["name"],
                    kind="regional-urlmap",
                    project=project,
                    region=location,
                    platform="gcp",
                    self_link=self_link,
                    category="loadbalancer",
                ),
                struct=urlmap,
            )
        )

    return results


async def explore_regional_backend_services(
    c: AuthorizedSession, project: str, location: str
) -> list[Resource]:
    response = await c.get(
        f"/compute/v1/projects/{project}/regions/{location}/backendServices",
        params={"returnPartialSuccess": True},
    )

    backend_services = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(
            f"Backend services API access failure: {backend_services}"
        )
        return []

    if "items" not in backend_services:
        logger.warning(
            f"No regional backend services found: {backend_services}"
        )
        return []

    results = []
    for backend_service in backend_services.get("items", []):
        name = backend_service["name"]
        region = backend_service["region"]
        self_link = backend_service.get("selfLink")
        display = name

        results.append(
            Resource(
                id=make_id(backend_service["id"]),
                meta=GCPMeta(
                    name=name,
                    display=display,
                    kind="regional-backend-service",
                    project=project,
                    region=region,
                    platform="gcp",
                    self_link=self_link,
                    category="loadbalancer",
                ),
                struct=backend_service,
            )
        )

    return results


async def explore_regional_backend_groups(
    c: AuthorizedSession, project: str, location: str
) -> list[Resource]:
    response = await c.get(
        f"/compute/v1/projects/{project}/regions/{location}/networkEndpointGroups",
        params={"returnPartialSuccess": True},
    )

    backend_groups = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"Backend groups API access failure: {backend_groups}")
        return []

    if "items" not in backend_groups:
        logger.warning(f"No regional backend groups found: {backend_groups}")
        return []

    results = []

    for backend_group in backend_groups.get("items", []):
        name = backend_group["name"]
        display = name
        self_link = backend_group.get("selfLink")
        zone = backend_group.get("zone")
        if zone:
            _, zone = zone.rsplit("/", 1)

        results.append(
            Resource(
                id=make_id(backend_group["id"]),
                meta=GCPMeta(
                    name=name,
                    display=display,
                    kind="regional-neg",
                    project=project,
                    region=location,
                    zone=zone,
                    platform="gcp",
                    self_link=self_link,
                    category="loadbalancer",
                ),
                struct=backend_group,
            )
        )

    return results


async def explore_zonal_backend_groups(
    c: AuthorizedSession, project: str
) -> list[Resource]:
    zones = await list_project_zones(project)

    results: list[Resource] = []

    if not zones:
        return results

    tasks: list[asyncio.Task] = []

    async with asyncio.TaskGroup() as tg:
        for zone in zones:
            tasks.append(
                tg.create_task(
                    c.get(
                        f"/compute/v1/projects/{project}/zones/{zone}/networkEndpointGroups",
                        params={"returnPartialSuccess": True},
                    )
                )
            )

    for task in tasks:
        response = task.result()
        if response is None:
            continue

        backend_groups = msgspec.json.decode(response.content)

        if response.status_code == 403:
            logger.warning(
                f"Zonal backend groups API access failure: {backend_groups}"
            )
            continue

        if "items" not in backend_groups:
            logger.warning(f"No zonal backend groups found: {backend_groups}")
            continue

        for backend_group in backend_groups.get("items", []):
            name = backend_group["name"]
            display = name
            self_link = backend_group.get("selfLink")
            region = backend_group.get("region")
            if region:
                _, region = region.rsplit("/", 1)

            results.append(
                Resource(
                    id=make_id(backend_group["id"]),
                    meta=GCPMeta(
                        name=name,
                        display=display,
                        kind="zonal-neg",
                        project=project,
                        region=region,
                        zone=zone,
                        platform="gcp",
                        self_link=self_link,
                        category="loadbalancer",
                    ),
                    struct=backend_group,
                )
            )

    return results


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    for backend_service in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='global-backend-service'].meta.name",
    ):
        struct = backend_service.parent.parent.obj["struct"]
        for used_by in struct.get("usedBy", []):
            ref = used_by.get("reference")
            p = f"$.resources[?@.meta.kind=='global-urlmap' && @.struct.selfLink=='{ref}'].id"  # noqa E501
            for urlmap_id in iter_resource(serialized, p):
                bsvc = backend_service.parent.parent
                add_link(
                    d,
                    urlmap_id.value,
                    Link(
                        direction="out",
                        kind="global-backend-service",
                        path=bsvc.path,
                        pointer=str(bsvc.pointer()),
                        id=bsvc.obj["id"],
                    ),
                )

    for s in iter_resource(
        serialized, "$.resources[?@.meta.kind=='global-neg'].struct.subnetwork"
    ):
        r_id = s.parent.parent.obj["id"]
        subnet = s.value
        p = f"$.resources[?@.meta.kind=='subnet' && @.meta.self_link=='{subnet}']"  # noqa E501
        for subnet in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="subnet",
                    path=subnet.path,
                    pointer=str(subnet.pointer()),
                    id=subnet.obj["id"],
                ),
            )

    for s in iter_resource(
        serialized, "$.resources[?@.meta.kind=='zonal-neg'].struct.network"
    ):
        r_id = s.parent.parent.obj["id"]
        network = s.value
        p = f"$.resources[?@.meta.kind=='network' && @.meta.self_link=='{network}']"  # noqa E501
        for subnet in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="network",
                    path=subnet.path,
                    pointer=str(subnet.pointer()),
                    id=subnet.obj["id"],
                ),
            )

    for s in iter_resource(
        serialized, "$.resources[?@.meta.kind=='zonal-neg'].struct.subnetwork"
    ):
        r_id = s.parent.parent.obj["id"]
        subnet = s.value
        p = f"$.resources[?@.meta.kind=='subnet' && @.meta.self_link=='{subnet}']"  # noqa E501
        for subnet in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="subnet",
                    path=subnet.path,
                    pointer=str(subnet.pointer()),
                    id=subnet.obj["id"],
                ),
            )

    for s in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='global-backend-service'].struct.backends.*.group",  # noqa E501
    ):
        r_id = s.parent.parent.parent.parent.obj["id"]
        group = s.value
        p = f"$.resources[?@.meta.kind=='regional-neg' && @.struct.selfLink=='{group}'].struct.cloudRun.service"  # noqa E501
        for service in iter_resource(serialized, p):
            neg = service.parent.parent.parent.obj["meta"]
            project = neg["project"]
            location = neg["region"]

            cloudrun_name = f"projects/{project}/locations/{location}/services/{service.obj}"  # noqa E501
            p = f"$.resources[?@.meta.kind=='cloudrun' && @.meta.name=='{cloudrun_name}']"  # noqa E501
            for cloudrun in iter_resource(serialized, p):
                tpl = cloudrun.obj["struct"]["template"]
                nics = tpl.get("vpcAccess", {}).get("networkInterfaces")
                if nics:
                    for nic in nics:
                        network = nic["network"]
                        p = f"$.resources[?@.meta.kind=='network' && @.meta.name=='{network}']"  # noqa E501
                        for nk in iter_resource(serialized, p):
                            add_link(
                                d,
                                r_id,
                                Link(
                                    direction="out",
                                    kind="network",
                                    path=nk.path,
                                    pointer=str(nk.pointer()),
                                    id=nk.obj["id"],
                                ),
                            )

                        subnet = nic["subnetwork"]
                        p = f"$.resources[?@.meta.kind=='subnet' && @.meta.display=='{subnet}']"  # noqa E501
                        for sn in iter_resource(serialized, p):
                            add_link(
                                d,
                                r_id,
                                Link(
                                    direction="out",
                                    kind="subnet",
                                    path=sn.path,
                                    pointer=str(sn.pointer()),
                                    id=sn.obj["id"],
                                ),
                            )

        p = f"$.resources[?@.meta.kind=='zonal-neg' && @.struct.selfLink=='{group}']"  # noqa E501
        for zonal_neg in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="zonal-neg",
                    path=zonal_neg.path,
                    pointer=str(zonal_neg.pointer()),
                    id=zonal_neg.obj["id"],
                ),
            )

    for s in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='global-backend-service'].struct.securityPolicy",  # noqa E501
    ):
        r_id = s.parent.parent.obj["id"]
        secpolicy = s.value
        p = f"$.resources[?@.meta.kind=='global-securities' && @.meta.self_link=='{secpolicy}']"  # noqa E501
        for service in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="global-securities",
                    path=service.path,
                    pointer=str(service.pointer()),
                    id=service.obj["id"],
                ),
            )

        p = f"$.resources[?@.meta.kind=='regional-securities' && @.meta.self_link=='{secpolicy}']"  # noqa E501
        for service in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="regional-securities",
                    path=service.path,
                    pointer=str(service.pointer()),
                    id=service.obj["id"],
                ),
            )

    for s in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='regional-backend-service'].struct.securityPolicy",  # noqa E501
    ):
        r_id = cast(str, s.parent.parent.obj["id"])
        secpolicy = s.value
        p = f"$.resources[?@.meta.kind=='regional-securities' && @.meta.self_link=='{secpolicy}']"  # noqa E501
        for service in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="regional-securities",
                    path=service.path,
                    pointer=str(service.pointer()),
                    id=service.obj["id"],
                ),
            )

    for s in iter_resource(
        serialized, "$.resources[?@.meta.kind=='regional-neg'].struct.network"
    ):
        r_id = cast(str, s.parent.parent.obj["id"])
        network = s.value
        p = f"$.resources[?@.meta.kind=='network' && @.meta.self_link=='{network}']"  # noqa E501
        for subnet in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="network",
                    path=subnet.path,
                    pointer=str(subnet.pointer()),
                    id=subnet.obj["id"],
                ),
            )

    for svcneg in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='global-backend-service'].struct.backends.*.group",
    ):
        r_id = svcneg.parent.parent.parent.parent.obj["id"]
        neg = svcneg.value
        p = f"$.resources[?@.meta.kind=='regional-neg' && @.struct.selfLink=='{neg}'].struct.cloudRun.service"  # noqa E501
        for cloudrun_name in iter_resource(serialized, p):  # type: ignore
            svc_name = cloudrun_name.value
            p = f"$.resources[?@.meta.kind=='cloudrun' && @.meta.name contains '{svc_name}']"  # noqa E501
            for cloudrun in iter_resource(serialized, p):
                add_link(
                    d,
                    r_id,
                    Link(
                        direction="out",
                        kind="cloudrun",
                        path=cloudrun.path,
                        pointer=str(cloudrun.pointer()),
                        id=cloudrun.obj["id"],
                    ),
                )

                p = f"$.resources[?@.meta.kind=='service' && @.struct.cloudRun.serviceName=='{svc_name}']"  # noqa E501
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

                    full_svc_name = svc.obj["meta"]["name"]

                    p = f"$.resources[?@.meta.kind=='slo' && match(@.meta.name, '{full_svc_name}/serviceLevelObjectives/.*')]"  # noqa E501
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
        r_id = urlmap.parent.parent.parent.parent.obj["id"]
        name = urlmap.value.rsplit("/", 1)[-1]

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

    for host in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='global-urlmap'].struct.hostRules.*.hosts.*",  # noqa E501
    ):
        r_id = host.parent.parent.parent.parent.parent.obj["id"]
        h = host.value
        p = f"$.resources[?@.meta.kind=='dns'].struct.rrdatas[?@.name=='{h}']"  # noqa E501
        for recordset in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="dns",
                    path=recordset.path,
                    pointer=str(recordset.pointer()),
                    id=recordset.obj["id"],
                ),
            )
