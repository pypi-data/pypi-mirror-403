from lueur.make_id import make_id
from lueur.models import AWSMeta, Resource
from lueur.platform.aws.client import Client

__all__ = ["explore_ec2"]


def explore_ec2(region: str) -> list[Resource]:
    resources = []

    instances = explore_instances(region)
    resources.extend(instances)

    return resources


###############################################################################
# Private functions
###############################################################################
def explore_instances(region: str) -> list[Resource]:
    results = []

    with Client("ec2", region) as c:
        instances = c.describe_instances()

        for reservations in instances["Reservations"]:
            for instance in reservations["Instances"]:
                results.append(
                    Resource(
                        id=make_id(instance["InstanceId"]),
                        meta=AWSMeta(
                            name=instance["InstanceId"],
                            display=instance["InstanceId"],
                            kind="instance",
                            platform="aws",
                            region=region,
                            category="compute",
                        ),
                        struct=instance,
                    )
                )

    return results
