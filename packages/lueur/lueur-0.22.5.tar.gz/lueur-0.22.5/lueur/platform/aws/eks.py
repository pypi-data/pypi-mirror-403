from concurrent.futures import ThreadPoolExecutor

from lueur.make_id import make_id
from lueur.models import AWSMeta, Resource
from lueur.platform.aws.client import Client

__all__ = ["explore_eks"]


def explore_eks(region: str) -> list[Resource]:
    resources = []

    clusters = explore_clusters(region)
    resources.extend(clusters)

    if not clusters:
        return resources

    futures = []
    with ThreadPoolExecutor(max_workers=len(clusters)) as executor:
        for c in clusters:
            futures.append(
                executor.submit(explore_nodegroups, region, c.meta.name)
            )

    for future in futures:
        resources.extend(future.result())

    return resources


###############################################################################
# Private functions
###############################################################################
def explore_clusters(region: str) -> list[Resource]:
    results = []

    with Client("eks", region) as c:
        clusters = c.list_clusters()

        for name in clusters["clusters"]:
            cluster = c.describe_cluster(name)
            results.append(
                Resource(
                    id=make_id(cluster["arn"]),
                    meta=AWSMeta(
                        name=cluster["name"],
                        display=cluster["name"],
                        kind="cluster",
                        platform="aws",
                        region=region,
                        category="compute",
                    ),
                    struct=cluster,
                )
            )

    return results


def explore_nodegroups(region: str, cluster_name: str) -> list[Resource]:
    with Client("eks", region) as c:
        nodegroups = c.list_nodegroups(clusterName=cluster_name)

        results = []

        for ngname in nodegroups["nodegroups"]:
            ng = c.describe_nodegroup(
                clusterName=cluster_name, nodegroupName=ngname
            )

            results.append(
                Resource(
                    id=make_id(ng["nodegroup"]["nodegroupArn"]),
                    meta=AWSMeta(
                        name=ngname,
                        display=ngname,
                        kind="nodegroup",
                        platform="aws",
                        region=region,
                        category="compute",
                    ),
                    struct=ng,
                )
            )

        return results
