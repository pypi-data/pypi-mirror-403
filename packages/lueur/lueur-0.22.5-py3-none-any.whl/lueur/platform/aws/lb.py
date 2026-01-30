# mypy: disable-error-code="assignment,attr-defined,index,union-attr"
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from lueur.links import add_link
from lueur.make_id import make_id
from lueur.models import AWSMeta, Discovery, Link, Resource
from lueur.platform.aws.client import Client
from lueur.rules import iter_resource

__all__ = ["explore_elbv2", "expand_links"]


def explore_elbv2(region: str) -> list[Resource]:
    resources = []

    lbs = explore_load_balancers(region)
    resources.extend(lbs)

    if not lbs:
        return resources

    futures = []
    with ThreadPoolExecutor(max_workers=len(lbs)) as executor:
        for lb in lbs:
            futures.append(
                executor.submit(explore_target_groups, region, lb.meta.name)
            )

            futures.append(
                executor.submit(explore_listeners, region, lb.meta.name)
            )

    for future in futures:
        resources.extend(future.result())

    return resources


###############################################################################
# Private functions
###############################################################################
def explore_load_balancers(region: str) -> list[Resource]:
    results = []

    with Client("elbv2", region) as c:
        lbs = c.describe_load_balancers()

        for lb in lbs["LoadBalancers"]:
            results.append(
                Resource(
                    id=make_id(lb["LoadBalancerArn"]),
                    meta=AWSMeta(
                        name=lb["LoadBalancerArn"],
                        display=lb["LoadBalancerName"],
                        kind="loadbalancer",
                        platform="aws",
                        region=region,
                        category="loadbalancer",
                    ),
                    struct=lb,
                )
            )

    return results


def explore_target_groups(region: str, lb_name: str) -> list[Resource]:
    with Client("elbv2", region) as c:
        tgs = c.describe_target_groups(
            LoadBalancerArn=lb_name,
        )

    results = []
    for tg in tgs["TargetGroups"]:
        results.append(
            Resource(
                id=make_id(tg["TargetGroupArn"]),
                meta=AWSMeta(
                    name=tg["TargetGroupArn"],
                    display=tg["TargetGroupName"],
                    kind="target-group",
                    platform="aws",
                    region=region,
                    category="loadbalancer",
                ),
                struct=tg,
            )
        )

    return results


def explore_listeners(region: str, lb_name: str) -> list[Resource]:
    with Client("elbv2", region) as c:
        listeners = c.describe_listeners(
            LoadBalancerArn=lb_name,
        )

    results = []
    for listener in listeners["Listeners"]:
        results.append(
            Resource(
                id=make_id(listener["ListenerArn"]),
                meta=AWSMeta(
                    name=listener["ListenerArn"],
                    display=listener["ListenerArn"],
                    kind="listener",
                    platform="aws",
                    region=region,
                    category="loadbalancer",
                ),
                struct=listener,
            )
        )

        results.extend(explore_rules(region, listener["ListenerArn"]))

    return results


def explore_rules(region: str, listener_arn: str) -> list[Resource]:
    with Client("elbv2", region) as c:
        rules = c.describe_rules(
            ListenerArn=listener_arn,
        )

    results = []
    for rule in rules["Rules"]:
        results.append(
            Resource(
                id=make_id(rule["RuleArn"]),
                meta=AWSMeta(
                    name=rule["RuleArn"],
                    display=rule["RuleArn"],
                    kind="listener-rule",
                    platform="aws",
                    region=region,
                    category="loadbalancer",
                ),
                struct=rule,
            )
        )

    return results


def expand_links(d: Discovery, serialized: dict[str, Any]) -> None:
    for lb_arn in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='loadbalancer'].meta.name",
    ):
        r_id = lb_arn.parent.parent.obj["id"]
        arn = lb_arn.value
        p = f"$.resources[?@.meta.kind=='listener' && @.struct.LoadBalancerArn=='{arn}']"  # noqa E501
        for listener in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="listener",
                    path=listener.path,
                    pointer=str(listener.pointer()),
                    id=listener.obj["id"],
                ),
            )

    for listener_arn in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='listener'].meta.name",
    ):
        r_id = listener_arn.parent.parent.obj["id"]
        arn = listener_arn.value
        prefix, suffix = arn.split("/", 1)
        rule_arn_prefix = f"{prefix}-rule/{suffix}"
        p = f"$.resources[?@.meta.kind=='listener-rule' && @.meta.name contains '{rule_arn_prefix}']"  # noqa E501
        for rule in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="listener-rule",
                    path=rule.path,
                    pointer=str(rule.pointer()),
                    id=rule.obj["id"],
                ),
            )

    for listener_rule_arn in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='listener-rule'].meta.name",
    ):
        r_id = listener_rule_arn.parent.parent.obj["id"]
        arn = listener_rule_arn.value
        prefix, suffix = arn.split("/", 1)
        listener_prefix = prefix.replace("listener-rule", "listener")
        listener_suffix, _ = suffix.rsplit("/", 1)
        listener_arn = f"{listener_prefix}/{listener_suffix}"
        p = f"$.resources[?@.meta.kind=='listener' && @.meta.name=='{listener_arn}']"  # noqa E501
        for listener in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="listener",
                    path=listener.path,
                    pointer=str(listener.pointer()),
                    id=listener.obj["id"],
                ),
            )

    for tg_arn in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='listener-rule'].struct.Actions.*.TargetGroupArn",  # noqa E501
    ):
        r_id = tg_arn.parent.parent.parent.parent.obj["id"]
        arn = tg_arn.value
        p = f"$.resources[?@.meta.kind=='target-group' && @.meta.name=='{arn}']"
        for tg in iter_resource(serialized, p):
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="target-group",
                    path=tg.path,
                    pointer=str(tg.pointer()),
                    id=tg.obj["id"],
                ),
            )

    for subnet_id in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='loadbalancer'].struct.AvailabilityZones.*.SubnetId",
    ):
        r_id = subnet_id.parent.parent.parent.parent.obj["id"]
        subnet_id = subnet_id.value
        p = f"$.resources[?@.meta.kind=='subnet' && @.meta.name=='{subnet_id}']"
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

    for lb_arn in iter_resource(
        serialized,
        "$.resources[?@.meta.kind=='target-group'].struct.LoadBalancerArns.*",
    ):
        tg = lb_arn.parent.parent.parent
        arn = lb_arn.value
        p = f"$.resources[?@.meta.kind=='loadbalancer' && @.meta.name=='{arn}']"
        for lb in iter_resource(serialized, p):
            r_id = lb.obj["id"]
            add_link(
                d,
                r_id,
                Link(
                    direction="out",
                    kind="target-group",
                    path=tg.path,
                    pointer=str(tg.pointer()),
                    id=tg.obj["id"],
                ),
            )
