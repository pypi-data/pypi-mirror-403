# mypy: disable-error-code="union-attr"
import logging
from typing import Any

import msgspec
from google.oauth2._service_account_async import Credentials

from lueur.links import add_link
from lueur.make_id import make_id
from lueur.models import Discovery, GCPMeta, Link, Resource
from lueur.platform.gcp.client import AuthorizedSession, Client
from lueur.rules import iter_resource

__all__ = ["explore_cloudrun"]
logger = logging.getLogger("lueur.lib")


async def explore_cloudrun(
    project: str, location: str, creds: Credentials | None = None
) -> list[Resource]:
    resources = []

    async with Client("https://run.googleapis.com", creds) as c:
        services = await explore_services(c, project, location)
        resources.extend(services)

    async with Client("https://vpcaccess.googleapis.com", creds) as c:
        connectors = await explore_vpcaccess_connectors(c, project, location)
        resources.extend(connectors)

    return resources


###############################################################################
# Private functions
###############################################################################
async def explore_services(
    c: AuthorizedSession, project: str, location: str
) -> list[Resource]:
    response = await c.get(
        f"/v2/projects/{project}/locations/{location}/services"
    )

    services = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"Services API access failure: {services}")
        return []

    if "services" not in services:
        logger.warning(f"No services found: {services}")
        return []

    results = []
    for svc in services.get("services", []):
        name = svc["name"]
        display = name.rsplit("/", 1)[-1]
        self_link = svc.get("selfLink")

        results.append(
            Resource(
                id=make_id(svc["uid"]),
                meta=GCPMeta(
                    name=name,
                    display=display,
                    kind="cloudrun",
                    project=project,
                    region=location,
                    platform="gcp",
                    self_link=self_link,
                    category="compute",
                ),
                struct=svc,
            )
        )

    return results


async def explore_vpcaccess_connectors(
    c: AuthorizedSession, project: str, location: str
) -> list[Resource]:
    response = await c.get(
        f"/v1beta1/projects/{project}/locations/{location}/connectors"
    )

    connectors = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"VPC connectors API access failure: {connectors}")
        return []

    if "connectors" not in connectors:
        logger.warning(f"No VPC access connectors found: {connectors}")
        return []

    results = []
    for connector in connectors["connectors"]:
        name = connector["name"]
        display = name.rsplit("/", 1)[-1]
        self_link = connector.get("selfLink")

        results.append(
            Resource(
                id=make_id(connector["name"]),
                meta=GCPMeta(
                    name=name,
                    display=display,
                    kind="cloudrun-vpcaccess-connector",
                    project=project,
                    region=location,
                    platform="gcp",
                    self_link=self_link,
                    category="network",
                ),
                struct=connector,
            )
        )

    return results


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    for s in iter_resource(
        serialized, "$.resources[?@.meta.kind=='cloudrun'].meta.name"
    ):
        r_id = s.parent.parent.obj["id"]  # type: ignore
        name = s.value.rsplit("/", 1)[-1]  # type: ignore
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
                    id=svc.obj["id"],  # type: ignore
                ),
            )

            svc_name = svc.obj["meta"]["name"]  # type: ignore

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
                        id=slo.obj["id"],  # type: ignore
                    ),
                )

        p = f"$.resources[?@.meta.kind=='regional-neg' && @.struct.cloudRun.service=='{name}']"  # noqa E501
        for neg in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="regional-neg",
                    path=neg.path,
                    pointer=str(neg.pointer()),
                    id=neg.obj["id"],  # type: ignore
                ),
            )

        tpl = s.parent.parent.obj["struct"]["template"]  # type: ignore

        connector_name = tpl.get("vpcAccess", {}).get("connector")
        if connector_name:
            p = f"$.resources[?@.meta.kind=='cloudrun-vpcaccess-connector' && @.meta.name=='{connector_name}']"  # noqa E501
            for svc in iter_resource(serialized, p):
                add_link(
                    d,
                    r_id,
                    Link(
                        direction="out",
                        kind="cloudrun-vpcaccess-connector",
                        path=svc.path,
                        pointer=str(svc.pointer()),
                        id=svc.obj["id"],  # type: ignore
                    ),
                )

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
                            id=nk.obj["id"],  # type: ignore
                        ),
                    )

                subnet = nic["subnetwork"]
                p = f"$.resources[?@.meta.kind=='subnet' && @.meta.name=='{subnet}']"  # noqa E501
                for sn in iter_resource(serialized, p):
                    add_link(
                        d,
                        r_id,
                        Link(
                            direction="out",
                            kind="subnet",
                            path=sn.path,
                            pointer=str(sn.pointer()),
                            id=sn.obj["id"],  # type: ignore
                        ),
                    )

        for v in tpl.get("volumes", []):
            if v.get("name") != "cloudsql":
                continue

            for inst in v["cloudSqlInstance"].get("instances", []):
                p = f"$.resources[?@.meta.kind=='instance' && @.struct.connectionName=='{inst}']"  # noqa E501
                for svc in iter_resource(serialized, p):
                    add_link(
                        d,
                        r_id,
                        Link(
                            direction="out",
                            kind="instance",
                            path=svc.path,
                            pointer=str(svc.pointer()),
                            id=svc.obj["id"],  # type: ignore
                        ),
                    )

    for s in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='cloudrun-vpcaccess-connector'].struct.network",  # noqa E501
    ):
        r_id = s.parent.parent.obj["id"]  # type: ignore
        network = s.value.rsplit("/", 1)[-1]  # type: ignore
        p = f"$.resources[?@.meta.kind=='network' && @.meta.name=='{network}']"
        for svc in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="network",
                    path=svc.path,
                    pointer=str(svc.pointer()),
                    id=svc.obj["id"],  # type: ignore
                ),
            )
