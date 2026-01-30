# mypy: disable-error-code="index,union-attr"
import asyncio
import logging
from typing import Any

import msgspec
from google.oauth2._service_account_async import Credentials

from lueur.links import add_link
from lueur.make_id import make_id
from lueur.models import Discovery, GCPMeta, Link, Resource
from lueur.platform.gcp.client import AuthorizedSession, Client
from lueur.rules import iter_resource

__all__ = ["explore_sql", "expand_links"]
logger = logging.getLogger("lueur.lib")


async def explore_sql(
    project: str, creds: Credentials | None = None
) -> list[Resource]:
    resources = []

    async with Client("https://sqladmin.googleapis.com", creds) as c:
        instances = await explore_instances(c, project)
        resources.extend(instances)

        tasks: list[asyncio.Task] = []

        async with asyncio.TaskGroup() as tg:
            for inst in instances:
                tasks.append(
                    tg.create_task(explore_users(c, project, inst.meta.name))
                )
                tasks.append(
                    tg.create_task(
                        explore_databases(c, project, inst.meta.name)
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
async def explore_instances(
    c: AuthorizedSession, project: str
) -> list[Resource]:
    response = await c.get(f"/v1/projects/{project}/instances")

    instances = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"CloudSQL API access failure: {instances}")
        return []

    if "items" not in instances:
        logger.warning(f"No CloudSQL instances found: {instances}")
        return []

    results = []
    for inst in instances["items"]:
        self_link = inst.get("selfLink")

        results.append(
            Resource(
                id=make_id(inst["selfLink"]),
                meta=GCPMeta(
                    name=inst["name"],
                    display=inst["name"],
                    kind="instance",
                    platform="gcp",
                    project=project,
                    self_link=self_link,
                    category="sql",
                ),
                struct=inst,
            )
        )

    return results


async def explore_users(
    c: AuthorizedSession, project: str, instance: str
) -> list[Resource]:
    response = await c.get(f"/v1/projects/{project}/instances/{instance}/users")

    users = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"CloudSQL API access failure: {users}")
        return []

    if "items" not in users:
        logger.warning(f"No CloudSQL users found: {users}")
        return []

    results = []
    for user in users["items"]:
        self_link = user.get("selfLink")

        results.append(
            Resource(
                id=make_id(f"{user['instance']}-{user['name']}"),
                meta=GCPMeta(
                    name=user["name"],
                    display=user["name"],
                    kind="user",
                    platform="gcp",
                    project=project,
                    self_link=self_link,
                    category="sql",
                ),
                struct=user,
            )
        )

    return results


async def explore_databases(
    c: AuthorizedSession, project: str, instance: str
) -> list[Resource]:
    response = await c.get(
        f"/v1/projects/{project}/instances/{instance}/databases"
    )

    databases = msgspec.json.decode(response.content)

    if response.status_code == 403:
        logger.warning(f"CloudSQL API access failure: {databases}")
        return []

    if "items" not in databases:
        logger.warning(f"No CloudSQL databases found: {databases}")
        return []

    results = []
    for database in databases["items"]:
        self_link = database.get("selfLink")

        results.append(
            Resource(
                id=make_id(f"{database['instance']}-{database['name']}"),
                meta=GCPMeta(
                    name=database["name"],
                    display=database["name"],
                    kind="database",
                    platform="gcp",
                    project=project,
                    self_link=self_link,
                    category="sql",
                ),
                struct=database,
            )
        )

    return results


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    for i in iter_resource(
        serialized, "$.resources[?@.meta.kind=='instance'].meta.name"
    ):
        r_id = i.parent.parent.obj["id"]
        name = i.value

        p = f"$.resources[?@.meta.kind=='user' && @.struct.instance=='{name}']"
        for user in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="user",
                    path=user.path,
                    pointer=str(user.pointer()),
                    id=user.obj["id"],
                ),
            )

        p = f"$.resources[?@.meta.kind=='database' && @.struct.instance=='{name}']"  # noqa E501
        for db in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="database",
                    path=db.path,
                    pointer=str(db.pointer()),
                    id=db.obj["id"],
                ),
            )

    for s in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='instance'].struct.settings.ipConfiguration.privateNetwork",  # noqa E501
    ):
        r_id = s.parent.parent.parent.parent.obj["id"]
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
                    id=svc.obj["id"],
                ),
            )

    for alertnc in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='alert-policy'].struct.notificationChannels.*",  # noqa E501
    ):
        r_id = alertnc.parent.parent.parent.obj["id"]
        conditions = alertnc.parent.parent.obj.get("conditions", [])

        for condition in conditions:
            ft = condition["conditionThreshold"]["filter"]
            if "cloudsql_database" in ft:
                for i in iter_resource(
                    serialized,
                    "$.resources[?@.meta.kind=='database'].meta.name",  # noqa E501
                ):
                    d_id = i.parent.parent.obj["id"]

                    add_link(
                        d,
                        d_id,
                        Link(
                            direction="out",
                            kind="alert-policy",
                            path=alertnc.path,
                            pointer=str(alertnc.pointer()),
                            id=alertnc.obj["id"],
                        ),
                    )

    slos = {}
    for slo in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='slo' && @.meta.platform=='gcp'].meta.name",  # noqa E501
    ):
        r_id = slo.parent.parent.obj["id"]
        slos[slo.value] = r_id
        sli = slo.parent.parent.obj["struct"]["serviceLevelIndicator"]
        window = sli.get("windowsBased")
        if window:
            bad_svc_filter = (
                window.get("goodTotalRatioThreshold", {})
                .get("performance", {})
                .get("goodTotalRatio", {})
                .get("badServiceFilter")
            )

            good_svc_filter = (
                window.get("goodTotalRatioThreshold", {})
                .get("performance", {})
                .get("goodTotalRatio", {})
                .get("goodServiceFilter")
            )

            if ("cloudsql_database" in bad_svc_filter) or (
                "cloudsql_database" in good_svc_filter
            ):  # noqa E501
                for i in iter_resource(
                    serialized,
                    "$.resources[?@.meta.kind=='database'].meta.name",  # noqa E501
                ):
                    d_id = i.parent.parent.obj["id"]
                    add_link(
                        d,
                        d_id,
                        Link(
                            direction="out",
                            kind="slo",
                            path=slo.path,
                            pointer=str(slo.pointer()),
                            id=slo.obj["id"],
                        ),
                    )
