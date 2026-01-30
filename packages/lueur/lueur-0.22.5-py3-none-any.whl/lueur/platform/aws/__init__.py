# mypy: disable-error-code="func-returns-value"
import logging
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

from lueur.make_id import make_id
from lueur.models import Discovery, Meta
from lueur.platform.aws.ec2 import explore_ec2
from lueur.platform.aws.ecr import explore_ecr
from lueur.platform.aws.eks import explore_eks
from lueur.platform.aws.lb import expand_links as lb_expand_links
from lueur.platform.aws.lb import explore_elbv2
from lueur.platform.aws.vpc import expand_links as vpc_expand_links
from lueur.platform.aws.vpc import explore_vpc

__all__ = ["explore", "expand_links"]
logger = logging.getLogger("lueur.lib")


def explore(region: str | None = None) -> Discovery:
    resources = []
    futures: list[Future] = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        if region:
            futures.append(executor.submit(explore_eks, region))
            futures.append(executor.submit(explore_ec2, region))
            futures.append(executor.submit(explore_ecr, region))
            futures.append(executor.submit(explore_elbv2, region))
            futures.append(executor.submit(explore_vpc, region))
        else:
            pass

        [f.add_done_callback(task_done) for f in futures]

    for future in futures:
        if future.exception():
            continue

        result = future.result()
        if result is None:
            continue

        resources.extend(result)

    name = f"aws-{region}"

    return Discovery(
        id=make_id(name),
        resources=resources,
        meta=Meta(name=name, display=name, kind="aws", category=None),
    )


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    vpc_expand_links(d, serialized)
    lb_expand_links(d, serialized)


###############################################################################
# Private functions
###############################################################################
def task_done(future: Future) -> None:
    if future.cancelled():
        logger.warning("Future cancelled")
        return

    x = future.exception()
    if x:
        logger.error(f"{x=}")
