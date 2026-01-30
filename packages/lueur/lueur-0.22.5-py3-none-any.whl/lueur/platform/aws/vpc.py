# mypy: disable-error-code="index,union-attr"
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from lueur.links import add_link
from lueur.make_id import make_id
from lueur.models import AWSMeta, Discovery, Link, Resource
from lueur.platform.aws.client import Client
from lueur.rules import iter_resource

__all__ = ["explore_vpc", "expand_links"]


def explore_vpc(region: str) -> list[Resource]:
    resources = []

    vpcs = explore_vpcs(region)
    resources.extend(vpcs)

    if not vpcs:
        return resources

    futures = []
    with ThreadPoolExecutor(max_workers=len(vpcs)) as executor:
        for vpc in vpcs:
            futures.append(
                executor.submit(explore_subnets, region, vpc.meta.name)
            )

    for future in futures:
        resources.extend(future.result())

    return resources


###############################################################################
# Private functions
###############################################################################
def explore_vpcs(region: str) -> list[Resource]:
    results = []

    with Client("ec2", region) as c:
        vpcs = c.describe_vpcs()

        for vpc in vpcs["Vpcs"]:
            results.append(
                Resource(
                    id=make_id(vpc["VpcId"]),
                    meta=AWSMeta(
                        name=vpc["VpcId"],
                        display=vpc["VpcId"],
                        kind="vpc",
                        platform="aws",
                        region=region,
                        category="network",
                    ),
                    struct=vpc,
                )
            )

    return results


def explore_subnets(region: str, vpc_id: str) -> list[Resource]:
    with Client("ec2", region) as c:
        subnets = c.describe_subnets(
            Filters=[
                {
                    "Name": "vpc-id",
                    "Values": [
                        vpc_id,
                    ],
                },
            ],
        )

    results = []
    for subnet in subnets["Subnets"]:
        results.append(
            Resource(
                id=make_id(subnet["SubnetId"]),
                meta=AWSMeta(
                    name=subnet["SubnetId"],
                    display=subnet["SubnetId"],
                    kind="subnet",
                    platform="aws",
                    region=region,
                    category="network",
                ),
                struct=subnet,
            )
        )

    return results


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    for vpc_name in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='vpc'].meta.name",
    ):
        r_id = vpc_name.parent.parent.obj["id"]
        vpc_id = vpc_name.value
        p = f"$.resources[?@.meta.kind=='subnet' && @.struct.VpcId=='{vpc_id}']"
        for listener in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="subnet",
                    path=listener.path,
                    pointer=str(listener.pointer()),
                    id=listener.obj["id"],
                ),
            )
