# mypy: disable-error-code="func-returns-value"
import asyncio
import logging
from typing import Any, Literal, Sequence, cast

from google.oauth2._service_account_async import Credentials

from lueur.make_id import make_id
from lueur.models import Discovery, Meta
from lueur.platform.gcp.address import explore_addresses
from lueur.platform.gcp.cloudrun import expand_links as cloudrun_links
from lueur.platform.gcp.cloudrun import explore_cloudrun
from lueur.platform.gcp.compute import explore_compute
from lueur.platform.gcp.connector import explore_connector
from lueur.platform.gcp.dns import explore_dns
from lueur.platform.gcp.firewall import explore_firewalls
from lueur.platform.gcp.forwardingrule import explore_forwardingrules
from lueur.platform.gcp.gke import expand_links as gke_expand_links
from lueur.platform.gcp.gke import explore_gke
from lueur.platform.gcp.healthchecks import explore_health_checks
from lueur.platform.gcp.lb import expand_links as lb_expand_links
from lueur.platform.gcp.lb import explore_lb
from lueur.platform.gcp.memorystore import explore_memorystore
from lueur.platform.gcp.monitoring import expand_links as mon_expand_links
from lueur.platform.gcp.monitoring import explore_monitoring
from lueur.platform.gcp.securities import explore_securities
from lueur.platform.gcp.sql import expand_links as sql_expand_links
from lueur.platform.gcp.sql import explore_sql
from lueur.platform.gcp.storage import explore_storage
from lueur.platform.gcp.targetproxy import explore_target_proxies
from lueur.platform.gcp.vpc import expand_links as vpc_expand_links
from lueur.platform.gcp.vpc import explore_vpc

__all__ = ["explore", "expand_links"]
logger = logging.getLogger("lueur.lib")

Targets = (
    "addresses",
    "gke",
    "cloudrun",
    "lb",
    "connector",
    "securities",
    "firewalls",
    "forwardingrules",
    "health_checks",
    "target_proxies",
    "storage",
    "dns",
    "memorystore",
    "compute",
    "vpc",
    "monitoring",
)


async def explore(
    project: str,
    location: str | None = None,
    creds: Credentials | None = None,
    include: Sequence[
        Literal[
            "addresses",
            "gke",
            "cloudrun",
            "lb",
            "connector",
            "securities",
            "firewalls",
            "forwardingrules",
            "health_checks",
            "target_proxies",
            "storage",
            "dns",
            "memorystore",
            "compute",
            "vpc",
            "monitoring",
        ]
    ]
    | None = None,
    include_global: bool = True,
    include_regional: bool = True,
) -> Discovery:
    resources = []
    tasks: list[asyncio.Task] = []

    if include is None:
        include = cast(Sequence, Targets)

    async with asyncio.TaskGroup() as tg:
        if include_regional and location:
            if "addresses" in include:
                tasks.append(
                    tg.create_task(
                        explore_addresses(project, location, creds),
                        name="explore_addresses",
                    )
                )

            if "gke" in include:
                tasks.append(
                    tg.create_task(
                        explore_gke(project, location, creds),
                        name="explore_gke",
                    )
                )

            if "cloudrun" in include:
                tasks.append(
                    tg.create_task(
                        explore_cloudrun(project, location, creds),
                        name="explore_cloudrun",
                    )
                )

            if "lb" in include:
                tasks.append(
                    tg.create_task(
                        explore_lb(project, location, creds), name="explore_lb"
                    )
                )

            if "connector" in include:
                tasks.append(
                    tg.create_task(
                        explore_connector(project, location, creds),
                        name="explore_connector",
                    )
                )

            if "securities" in include:
                tasks.append(
                    tg.create_task(
                        explore_securities(project, location, creds),
                        name="explore_securities",
                    )
                )

            if "firewalls" in include:
                tasks.append(
                    tg.create_task(
                        explore_firewalls(project, location, creds),
                        name="explore_firewalls",
                    )
                )

            if "forwardingrules" in include:
                tasks.append(
                    tg.create_task(
                        explore_forwardingrules(project, location, creds),
                        name="explore_forwardingrules",
                    )
                )

            if "health_checks" in include:
                tasks.append(
                    tg.create_task(
                        explore_health_checks(project, location, creds),
                        name="explore_health_checks",
                    )
                )

            if "target_proxies" in include:
                tasks.append(
                    tg.create_task(
                        explore_target_proxies(project, location, creds),
                        name="explore_target_proxies",
                    )
                )
        elif include_global:
            if "addresses" in include:
                tasks.append(
                    tg.create_task(
                        explore_addresses(project, None, creds),
                        name="explore_global_addresses",
                    )
                )

            if "sql" in include:
                tasks.append(
                    tg.create_task(
                        explore_sql(project, creds), name="explore_global_sql"
                    )
                )

            if "lb" in include:
                tasks.append(
                    tg.create_task(
                        explore_lb(project, None, creds),
                        name="explore_global_lb",
                    )
                )

            if "vpc" in include:
                tasks.append(
                    tg.create_task(
                        explore_vpc(project, creds), name="explore_global_vpc"
                    )
                )

            if "monitoring" in include:
                tasks.append(
                    tg.create_task(
                        explore_monitoring(project, creds),
                        name="explore_global_monitoring",
                    )
                )

            if "securities" in include:
                tasks.append(
                    tg.create_task(
                        explore_securities(project, None, creds),
                        name="explore_global_securities",
                    )
                )

            if "firewalls" in include:
                tasks.append(
                    tg.create_task(
                        explore_firewalls(project, None, creds),
                        name="explore_global_firewalls",
                    )
                )

            if "health_checks" in include:
                tasks.append(
                    tg.create_task(
                        explore_health_checks(project, None, creds),
                        name="explore_global_health_checks",
                    )
                )

            if "target_proxies" in include:
                tasks.append(
                    tg.create_task(
                        explore_target_proxies(project, None, creds),
                        name="explore_global_target_proxies",
                    )
                )

            if "storage" in include:
                tasks.append(
                    tg.create_task(
                        explore_storage(project, creds),
                        name="explore_global_storage",
                    )
                )

            if "compute" in include:
                tasks.append(
                    tg.create_task(
                        explore_compute(project, creds),
                        name="explore_global_compute",
                    )
                )

            if "memorystore" in include:
                tasks.append(
                    tg.create_task(
                        explore_memorystore(project, creds),
                        name="explore_global_memorystore",
                    )
                )

            if "dns" in include:
                tasks.append(
                    tg.create_task(
                        explore_dns(project, creds),
                        name="explore_global_dns",
                    )
                )

        [t.add_done_callback(task_done) for t in tasks]

    for task in tasks:
        result = task.result()
        if result is None:
            continue
        resources.extend(result)

    name = f"{project}-{location}"

    return Discovery(
        id=make_id(name),
        resources=resources,
        meta=Meta(name=name, display=name, kind="gcp", category=None),
    )


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    cloudrun_links(d, serialized)
    vpc_expand_links(d, serialized)
    sql_expand_links(d, serialized)
    gke_expand_links(d, serialized)
    lb_expand_links(d, serialized)
    mon_expand_links(d, serialized)


###############################################################################
# Private functions
###############################################################################
def task_done(task: asyncio.Task) -> None:
    task.remove_done_callback(task_done)

    if task.cancelled():
        logger.warning(f"Task '{task.get_name()}' cancelled")
        return None

    x = task.exception()
    if x:
        logger.error(f"{x=}")
        return None
