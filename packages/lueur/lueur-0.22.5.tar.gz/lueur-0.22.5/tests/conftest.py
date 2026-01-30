import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.append(Path.cwd())


@pytest.fixture(scope="session")
def gcp_org_id() -> str:
    return "myorg"


@pytest.fixture(scope="session")
def gcp_project_number() -> str:
    return "608773013422"


@pytest.fixture(scope="session")
def gcp_project() -> str:
    return "dummy"


@pytest.fixture(scope="session")
def gcp_region() -> str:
    return "us-east1"


@pytest.fixture(scope="session")
def gcp_cloudrun_service_A() -> str:
    return "serviceA"


@pytest.fixture(scope="session")
def gcp_cloudrun_service_B() -> str:
    return "serviceB"


@pytest.fixture(scope="session")
def gcp_cloudrun_service_account_A(
    gcp_project_number: str, gcp_cloudrun_service_A: str
) -> str:
    return (
        f"{gcp_cloudrun_service_A}-yxvjljk5@{gcp_project_number}.iam.gserviceaccount.com",
    )


@pytest.fixture(scope="session")
def gcp_cloudrun_service_B() -> str:
    return "serviceB"


@pytest.fixture(scope="session")
def gcp_cloudrun_service_account_B(
    gcp_project_number: str, gcp_cloudrun_service_B: str
) -> str:
    return (
        f"{gcp_cloudrun_service_B}-pxwytzo5@{gcp_project_number}.iam.gserviceaccount.com",
    )


@pytest.fixture(scope="session")
def gcp_gke_cluster_name() -> str:
    return "serviceB"


@pytest.fixture(scope="session")
def gcp_sql_instance_name() -> str:
    return "demo"


@pytest.fixture(scope="session")
def gcp_sql_instance_user_name() -> str:
    return "demo"


@pytest.fixture(scope="session")
def gcp_sql_instance_database_name() -> str:
    return "demo"


@pytest.fixture(scope="session")
def gcp_cloudrun_services(
    gcp_project: str,
    gcp_region: str,
    gcp_cloudrun_service_A: str,
    gcp_cloudrun_service_account_A: str,
) -> list[dict[str, Any]]:
    return [
        {
            "name": f"projects/{gcp_project}/locations/{gcp_region}/services/{gcp_cloudrun_service_account_A}",
            "uid": "78617702-cd59-4f3a-b2bb-128c9a899664",
            "generation": "1314",
            "createTime": "2023-02-10T21:23:44.062037Z",
            "updateTime": "2024-06-23T21:06:57.505454Z",
            "creator": f"{gcp_cloudrun_service_A}@chaosiq-devops.iam.gserviceaccount.com",
            "lastModifier": f"{gcp_cloudrun_service_A}@chaosiq-devops.iam.gserviceaccount.com",
            "client": "terraform",
            "ingress": "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER",
            "launchStage": "GA",
            "template": {
                "scaling": {"maxInstanceCount": 30},
                "vpcAccess": {
                    "connector": f"projects/{gcp_project}/locations/{gcp_region}/connectors/api",
                    "egress": "PRIVATE_RANGES_ONLY",
                },
                "timeout": "60s",
                "serviceAccount": gcp_cloudrun_service_account_A,
                "containers": [
                    {
                        "image": f"gcp_cloudrun_service_account_A:9f19ab2cb8a3b4a62300ca35efcdb6486b2fd90b",
                        "resources": {
                            "limits": {"cpu": "1.0", "memory": "256Mi"},
                            "cpuIdle": True,
                            "startupCpuBoost": True,
                        },
                        "ports": [{"name": "http1", "containerPort": 8080}],
                        "startupProbe": {
                            "timeoutSeconds": 240,
                            "periodSeconds": 240,
                            "failureThreshold": 1,
                            "tcpSocket": {"port": 8080},
                        },
                    }
                ],
                "maxInstanceRequestConcurrency": 80,
            },
            "traffic": [
                {
                    "type": "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST",
                    "percent": 100,
                }
            ],
            "observedGeneration": "1314",
            "terminalCondition": {
                "type": "Ready",
                "state": "CONDITION_SUCCEEDED",
                "lastTransitionTime": "2024-06-23T21:07:06.717538Z",
            },
            "conditions": [
                {
                    "type": "RoutesReady",
                    "state": "CONDITION_SUCCEEDED",
                    "lastTransitionTime": "2024-06-23T21:07:06.684537Z",
                },
                {
                    "type": "ConfigurationsReady",
                    "state": "CONDITION_SUCCEEDED",
                    "lastTransitionTime": "2023-05-29T12:39:00.276862Z",
                },
            ],
            "latestReadyRevision": f"projects/{gcp_project}/locations/{gcp_region}/services/{gcp_cloudrun_service_A}/revisions/{gcp_cloudrun_service_A}-01314-6nm",
            "latestCreatedRevision": f"projects/{gcp_project}/locations/{gcp_region}/services/{gcp_cloudrun_service_A}/revisions/{gcp_cloudrun_service_A}-01314-6nm",
            "trafficStatuses": [
                {
                    "type": "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST",
                    "percent": 100,
                }
            ],
            "uri": f"https://{gcp_cloudrun_service_A}-h2oyppsxyz-ew.a.run.app",
            "etag": '"CPGc4rMGELC7gvEB/cHJvamVjdHMvc3RhZ2luZzEwMDIyMDIzL2xvY2F0aW9ucy9ldXJvcGUtd2VzdDEvc2VydmljZXMvcmVsaWFibHktZnJvbnRlbmQ"',
        }
    ]


@pytest.fixture(scope="session")
def gcp_cloudrun_connectors(
    gcp_project: str,
    gcp_region: str,
) -> list[dict[str, Any]]:
    return [
        {
            "name": f"projects/{gcp_project}/locations/{gcp_region}/connectors/api",
            "network": f"{gcp_project}-vpc",
            "ipCidrRange": "10.8.0.0/28",
            "state": "READY",
            "minThroughput": 200,
            "maxThroughput": 300,
            "connectedProjects": ["{gcp_project}"],
            "machineType": "e2-micro",
            "minInstances": 2,
            "maxInstances": 3,
            "createTime": "2023-02-10T17:56:37.239876Z",
            "lastRestartTime": "2024-06-25T13:55:19.639192Z",
        }
    ]


@pytest.fixture(scope="session")
def gcp_gke_clusters(
    gcp_project: str,
    gcp_region: str,
    gcp_gke_cluster_name: str,
) -> list[dict[str, Any]]:
    return [
        {
            "name": gcp_gke_cluster_name,
            "nodeConfig": {
                "machineType": "e2-medium",
                "diskSizeGb": 100,
                "oauthScopes": [
                    "https://www.googleapis.com/auth/cloud-platform"
                ],
                "metadata": {"disable-legacy-endpoints": "true"},
                "imageType": "COS_CONTAINERD",
                "labels": {"env": "demo"},
                "serviceAccount": f"gke-demo@{gcp_project}.iam.gserviceaccount.com",
                "diskType": "pd-balanced",
                "workloadMetadataConfig": {"mode": "GKE_METADATA"},
                "shieldedInstanceConfig": {"enableIntegrityMonitoring": True},
                "resourceLabels": {"env": "demo"},
                "windowsNodeConfig": {},
            },
            "masterAuth": {
                "clientCertificateConfig": {},
                "clusterCaCertificate": "...",
            },
            "loggingService": "logging.googleapis.com/kubernetes",
            "monitoringService": "monitoring.googleapis.com/kubernetes",
            "network": "k8s-dummy",
            "clusterIpv4Cidr": "10.21.0.0/14",
            "addonsConfig": {
                "httpLoadBalancing": {},
                "horizontalPodAutoscaling": {},
                "kubernetesDashboard": {"disabled": True},
                "networkPolicyConfig": {"disabled": True},
                "dnsCacheConfig": {},
                "gcePersistentDiskCsiDriverConfig": {"enabled": True},
                "gcpFilestoreCsiDriverConfig": {"enabled": True},
                "gcsFuseCsiDriverConfig": {},
            },
            "subnetwork": "k8s-dummy",
            "nodePools": [
                {
                    "name": "pool-2",
                    "config": {
                        "machineType": "e2-medium",
                        "diskSizeGb": 100,
                        "oauthScopes": [
                            "https://www.googleapis.com/auth/cloud-platform"
                        ],
                        "metadata": {"disable-legacy-endpoints": "true"},
                        "imageType": "COS_CONTAINERD",
                        "labels": {"env": "demo"},
                        "serviceAccount": f"gke-demo@{gcp_project}.iam.gserviceaccount.com",
                        "diskType": "pd-balanced",
                        "workloadMetadataConfig": {"mode": "GKE_METADATA"},
                        "shieldedInstanceConfig": {
                            "enableIntegrityMonitoring": True
                        },
                        "resourceLabels": {"env": "demo"},
                        "windowsNodeConfig": {},
                    },
                    "initialNodeCount": 1,
                    "autoscaling": {
                        "enabled": True,
                        "maxNodeCount": 1,
                        "locationPolicy": "BALANCED",
                    },
                    "management": {"autoUpgrade": True, "autoRepair": True},
                    "maxPodsConstraint": {"maxPodsPerNode": "110"},
                    "podIpv4CidrSize": 24,
                    "locations": [
                        f"{gcp_region}-c",
                        f"{gcp_region}-d",
                        f"{gcp_region}-b",
                    ],
                    "networkConfig": {
                        "podRange": "gke-{gcp_gke_cluster_name}-pods-8ba2b403",
                        "podIpv4CidrBlock": "10.21.0.0/14",
                        "enablePrivateNodes": False,
                        "podIpv4RangeUtilization": 0.003,
                    },
                    "selfLink": f"https://container.googleapis.com/v1/projects/{gcp_project}/locations/{gcp_region}/clusters/{gcp_gke_cluster_name}/nodePools/pool-2",
                    "version": "1.28.9-gke.1209000",
                    "instanceGroupUrls": [
                        f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/zones/{gcp_region}-c/instanceGroupManagers/gke-{gcp_gke_cluster_name}-pool-2-ff7287e7-grp",
                        f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/zones/{gcp_region}-d/instanceGroupManagers/gke-{gcp_gke_cluster_name}-pool-2-691ec5a9-grp",
                        f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/zones/{gcp_region}-b/instanceGroupManagers/gke-{gcp_gke_cluster_name}-pool-2-06a83df0-grp",
                    ],
                    "status": "RUNNING",
                    "upgradeSettings": {"maxSurge": 1, "strategy": "SURGE"},
                    "etag": "85bfa51c-efe1-4cc5-b723-7843f72e3dbb",
                },
                {
                    "name": "pool-3",
                    "config": {
                        "machineType": "n2-standard-2",
                        "diskSizeGb": 100,
                        "oauthScopes": [
                            "https://www.googleapis.com/auth/cloud-platform"
                        ],
                        "metadata": {"disable-legacy-endpoints": "true"},
                        "imageType": "COS_CONTAINERD",
                        "labels": {"env": "demo"},
                        "serviceAccount": f"demo-cluster@{gcp_project}.iam.gserviceaccount.com",
                        "diskType": "pd-balanced",
                        "workloadMetadataConfig": {"mode": "GKE_METADATA"},
                        "shieldedInstanceConfig": {
                            "enableIntegrityMonitoring": True
                        },
                        "advancedMachineFeatures": {
                            "enableNestedVirtualization": False
                        },
                        "resourceLabels": {"env": "demo"},
                        "windowsNodeConfig": {},
                    },
                    "initialNodeCount": 2,
                    "autoscaling": {
                        "enabled": True,
                        "maxNodeCount": 3,
                        "locationPolicy": "BALANCED",
                    },
                    "management": {"autoUpgrade": True, "autoRepair": True},
                    "maxPodsConstraint": {"maxPodsPerNode": "110"},
                    "podIpv4CidrSize": 24,
                    "locations": [
                        f"{gcp_region}-c",
                        f"{gcp_region}-d",
                        f"{gcp_region}-b",
                    ],
                    "networkConfig": {
                        "podRange": "gke-{gcp_gke_cluster_name}-pods-8ba2b403",
                        "podIpv4CidrBlock": "10.21.0.0/14",
                        "enablePrivateNodes": False,
                        "podIpv4RangeUtilization": 0.003,
                    },
                    "selfLink": f"https://container.googleapis.com/v1/projects/{gcp_project}/locations/{gcp_region}/clusters/{gcp_gke_cluster_name}/nodePools/pool-3",
                    "version": "1.28.9-gke.1209000",
                    "instanceGroupUrls": [
                        f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/zones/{gcp_region}-c/instanceGroupManagers/gke-{gcp_gke_cluster_name}-pool-3-ea9a9827-grp",
                        f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/zones/{gcp_region}-d/instanceGroupManagers/gke-{gcp_gke_cluster_name}-pool-3-a5ac3c22-grp",
                        f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/zones/{gcp_region}-b/instanceGroupManagers/gke-{gcp_gke_cluster_name}-pool-3-e1aa9d04-grp",
                    ],
                    "status": "RUNNING",
                    "upgradeSettings": {"maxSurge": 1, "strategy": "SURGE"},
                    "etag": "4fae315e-2b4c-4173-a724-126d2dfe99d0",
                    "queuedProvisioning": {},
                },
            ],
            "locations": [
                f"{gcp_region}-c",
                f"{gcp_region}-d",
                f"{gcp_region}-b",
            ],
            "resourceLabels": {"env": "demo"},
            "labelFingerprint": "d26e484d",
            "legacyAbac": {},
            "ipAllocationPolicy": {
                "useIpAliases": True,
                "clusterIpv4Cidr": "10.21.0.0/14",
                "servicesIpv4Cidr": "10.232.208.0/20",
                "clusterSecondaryRangeName": f"gke-{gcp_gke_cluster_name}-pods-8ba2b403",
                "servicesSecondaryRangeName": f"gke-{gcp_gke_cluster_name}-services-8ba2b403",
                "clusterIpv4CidrBlock": "10.21.0.0/14",
                "servicesIpv4CidrBlock": "10.232.208.0/20",
                "stackType": "IPV4",
                "podCidrOverprovisionConfig": {},
                "defaultPodIpv4RangeUtilization": 0.003,
            },
            "masterAuthorizedNetworksConfig": {
                "gcpPublicCidrsAccessEnabled": True
            },
            "maintenancePolicy": {
                "window": {
                    "recurringWindow": {
                        "window": {
                            "startTime": "2024-03-11T23:00:00Z",
                            "endTime": "2024-03-12T23:00:00Z",
                        },
                        "recurrence": "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA,SU",
                    }
                },
                "resourceVersion": "1c4b3335",
            },
            "binaryAuthorization": {"evaluationMode": "DISABLED"},
            "autoscaling": {
                "enableNodeAutoprovisioning": True,
                "resourceLimits": [
                    {"resourceType": "cpu", "minimum": "1", "maximum": "1"},
                    {"resourceType": "memory", "minimum": "1", "maximum": "1"},
                ],
                "autoscalingProfile": "BALANCED",
                "autoprovisioningNodePoolDefaults": {
                    "oauthScopes": [
                        "https://www.googleapis.com/auth/userinfo.email",
                        "https://www.googleapis.com/auth/cloud-platform",
                    ],
                    "serviceAccount": "default",
                    "upgradeSettings": {"maxSurge": 1, "strategy": "SURGE"},
                    "management": {"autoUpgrade": True, "autoRepair": True},
                    "diskSizeGb": 100,
                    "diskType": "pd-balanced",
                    "shieldedInstanceConfig": {
                        "enableIntegrityMonitoring": True
                    },
                    "imageType": "COS_CONTAINERD",
                },
                "autoprovisioningLocations": [
                    f"{gcp_region}-c",
                    f"{gcp_region}-d",
                    f"{gcp_region}-b",
                ],
            },
            "networkConfig": {
                "network": f"projects/{gcp_project}/global/networks/k8s-dummy",
                "subnetwork": f"projects/{gcp_project}/regions/{gcp_region}/subnetworks/k8s-dummy",
                "defaultSnatStatus": {},
                "datapathProvider": "ADVANCED_DATAPATH",
                "serviceExternalIpsConfig": {},
                "gatewayApiConfig": {"channel": "CHANNEL_STANDARD"},
            },
            "defaultMaxPodsConstraint": {"maxPodsPerNode": "110"},
            "authenticatorGroupsConfig": {},
            "privateClusterConfig": {
                "privateEndpoint": "10.0.10.20",
                "publicEndpoint": "104.155.86.88",
            },
            "databaseEncryption": {"state": "DECRYPTED"},
            "shieldedNodes": {"enabled": True},
            "releaseChannel": {"channel": "REGULAR"},
            "workloadIdentityConfig": {
                "workloadPool": f"{gcp_project}.svc.id.goog"
            },
            "costManagementConfig": {"enabled": True},
            "notificationConfig": {"pubsub": {}},
            "selfLink": f"https://container.googleapis.com/v1/projects/{gcp_project}/locations/{gcp_region}/clusters/{gcp_gke_cluster_name}",
            "zone": "{gcp_region}",
            "endpoint": "104.155.86.88",
            "initialClusterVersion": "1.27.8-gke.1067004",
            "currentMasterVersion": "1.28.9-gke.1209000",
            "currentNodeVersion": "1.28.9-gke.1209000",
            "createTime": "2024-03-13T16:51:17+00:00",
            "status": "RUNNING",
            "servicesIpv4Cidr": "10.232.208.0/20",
            "instanceGroupUrls": [
                f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/zones/{gcp_region}-c/instanceGroupManagers/gke-{gcp_gke_cluster_name}-pool-2-ff7287e7-grp",
                f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/zones/{gcp_region}-d/instanceGroupManagers/gke-{gcp_gke_cluster_name}-pool-2-691ec5a9-grp",
                f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/zones/{gcp_region}-b/instanceGroupManagers/gke-{gcp_gke_cluster_name}-pool-2-06a83df0-grp",
                f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/zones/{gcp_region}-c/instanceGroupManagers/gke-{gcp_gke_cluster_name}-pool-3-ea9a9827-grp",
                f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/zones/{gcp_region}-d/instanceGroupManagers/gke-{gcp_gke_cluster_name}-pool-3-a5ac3c22-grp",
                f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/zones/{gcp_region}-b/instanceGroupManagers/gke-{gcp_gke_cluster_name}-pool-3-e1aa9d04-grp",
            ],
            "currentNodeCount": 3,
            "location": gcp_region,
            "autopilot": {},
            "id": "8ba2b4038c744fa5bd026220abc6db5978a99ba6eb574f82958cedfb89bee63a",
            "nodePoolDefaults": {
                "nodeConfigDefaults": {
                    "loggingConfig": {"variantConfig": {"variant": "DEFAULT"}}
                }
            },
            "loggingConfig": {
                "componentConfig": {
                    "enableComponents": ["SYSTEM_COMPONENTS", "WORKLOADS"]
                }
            },
            "monitoringConfig": {
                "componentConfig": {"enableComponents": ["SYSTEM_COMPONENTS"]},
                "managedPrometheusConfig": {"enabled": True},
                "advancedDatapathObservabilityConfig": {},
            },
            "etag": "aa55d4ac-c142-4eb7-8819-f5a71eb1b34f",
            "securityPostureConfig": {
                "mode": "BASIC",
                "vulnerabilityMode": "VULNERABILITY_DISABLED",
            },
            "enterpriseConfig": {"clusterTier": "STANDARD"},
        }
    ]


@pytest.fixture(scope="session")
def gcp_gke_cluster_nodepools(
    gcp_project: str,
    gcp_region: str,
    gcp_gke_cluster_name: str,
) -> list[dict[str, Any]]:
    return [
        {
            "name": "pool-2",
            "config": {
                "machineType": "e2-medium",
                "diskSizeGb": 100,
                "oauthScopes": [
                    "https://www.googleapis.com/auth/cloud-platform"
                ],
                "metadata": {"disable-legacy-endpoints": "true"},
                "imageType": "COS_CONTAINERD",
                "labels": {"env": "demo"},
                "serviceAccount": f"gke-demo@{gcp_project}.iam.gserviceaccount.com",
                "diskType": "pd-balanced",
                "workloadMetadataConfig": {"mode": "GKE_METADATA"},
                "shieldedInstanceConfig": {"enableIntegrityMonitoring": True},
                "resourceLabels": {"env": "demo"},
                "windowsNodeConfig": {},
            },
            "initialNodeCount": 1,
            "autoscaling": {
                "enabled": True,
                "maxNodeCount": 1,
                "locationPolicy": "BALANCED",
            },
            "management": {"autoUpgrade": True, "autoRepair": True},
            "maxPodsConstraint": {"maxPodsPerNode": "110"},
            "podIpv4CidrSize": 24,
            "locations": [
                f"{gcp_region}-c",
                f"{gcp_region}-d",
                f"{gcp_region}-b",
            ],
            "networkConfig": {
                "podRange": "gke-{gcp_gke_cluster_name}-pods-8ba2b403",
                "podIpv4CidrBlock": "10.21.0.0/14",
                "enablePrivateNodes": False,
            },
            "selfLink": f"https://container.googleapis.com/v1/projects/{gcp_project}/locations/{gcp_region}/clusters/{gcp_gke_cluster_name}/nodePools/pool-2",
            "version": "1.28.9-gke.1209000",
            "instanceGroupUrls": [
                f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/zones/{gcp_region}-c/instanceGroupManagers/gke-{gcp_gke_cluster_name}-pool-2-ff7287e7-grp",
                f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/zones/{gcp_region}-d/instanceGroupManagers/gke-{gcp_gke_cluster_name}-pool-2-691ec5a9-grp",
                f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/zones/{gcp_region}-b/instanceGroupManagers/gke-{gcp_gke_cluster_name}-pool-2-06a83df0-grp",
            ],
            "status": "RUNNING",
            "upgradeSettings": {"maxSurge": 1, "strategy": "SURGE"},
            "etag": "85bfa51c-efe1-4cc5-b723-7843f72e3dbb",
        },
        {
            "name": "pool-3",
            "config": {
                "machineType": "n2-standard-2",
                "diskSizeGb": 100,
                "oauthScopes": [
                    "https://www.googleapis.com/auth/cloud-platform"
                ],
                "metadata": {"disable-legacy-endpoints": "true"},
                "imageType": "COS_CONTAINERD",
                "labels": {"env": "demo"},
                "serviceAccount": f"demo-cluster@{gcp_project}.iam.gserviceaccount.com",
                "diskType": "pd-balanced",
                "workloadMetadataConfig": {"mode": "GKE_METADATA"},
                "shieldedInstanceConfig": {"enableIntegrityMonitoring": True},
                "advancedMachineFeatures": {
                    "enableNestedVirtualization": False
                },
                "resourceLabels": {"env": "demo"},
                "windowsNodeConfig": {},
            },
            "initialNodeCount": 2,
            "autoscaling": {
                "enabled": True,
                "maxNodeCount": 3,
                "locationPolicy": "BALANCED",
            },
            "management": {"autoUpgrade": True, "autoRepair": True},
            "maxPodsConstraint": {"maxPodsPerNode": "110"},
            "podIpv4CidrSize": 24,
            "locations": [
                f"{gcp_region}-c",
                f"{gcp_region}-d",
                f"{gcp_region}-b",
            ],
            "networkConfig": {
                "podRange": f"gke-{gcp_gke_cluster_name}-pods-8ba2b403",
                "podIpv4CidrBlock": "10.21.0.0/14",
                "enablePrivateNodes": False,
            },
            "selfLink": f"https://container.googleapis.com/v1/projects/{gcp_project}/locations/{gcp_region}/clusters/{gcp_gke_cluster_name}/nodePools/pool-3",
            "version": "1.28.9-gke.1209000",
            "instanceGroupUrls": [
                f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/zones/{gcp_region}-c/instanceGroupManagers/gke-{gcp_gke_cluster_name}-pool-3-ea9a9827-grp",
                f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/zones/{gcp_region}-d/instanceGroupManagers/gke-{gcp_gke_cluster_name}-pool-3-a5ac3c22-grp",
                f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/zones/{gcp_region}-b/instanceGroupManagers/gke-{gcp_gke_cluster_name}-pool-3-e1aa9d04-grp",
            ],
            "status": "RUNNING",
            "upgradeSettings": {"maxSurge": 1, "strategy": "SURGE"},
            "etag": "4fae315e-2b4c-4173-a724-126d2dfe99d0",
            "queuedProvisioning": {},
        },
    ]


@pytest.fixture(scope="session")
def gcp_global_securities(
    gcp_project: str,
    gcp_region: str,
    gcp_gke_cluster_name: str,
) -> list[dict[str, Any]]:
    return [
        {
            "kind": "compute#securityPolicy",
            "id": "2953638056173439792",
            "creationTimestamp": "2023-02-10T13:23:43.497-08:00",
            "name": "cloud-armor-waf-policy",
            "rules": [
                {
                    "kind": "compute#securityPolicyRule",
                    "description": "",
                    "priority": 1000,
                    "match": {
                        "expr": {
                            "expression": "evaluatePreconfiguredWaf('sqli-v33-stable', {'sensitivity': 1}) || evaluatePreconfiguredWaf('sqli-v33-stable', {'sensitivity': 2})"
                        }
                    },
                    "action": "deny(403)",
                    "preview": False,
                    "headerAction": {},
                },
                {
                    "kind": "compute#securityPolicyRule",
                    "description": "",
                    "priority": 1001,
                    "match": {
                        "expr": {
                            "expression": "evaluatePreconfiguredWaf('xss-v33-stable', {'sensitivity': 1})"
                        }
                    },
                    "action": "deny(403)",
                    "preview": False,
                    "headerAction": {},
                },
                {
                    "kind": "compute#securityPolicyRule",
                    "description": "",
                    "priority": 1002,
                    "match": {
                        "expr": {
                            "expression": "evaluatePreconfiguredExpr('lfi-v33-stable')"
                        }
                    },
                    "action": "deny(403)",
                    "preview": False,
                    "headerAction": {},
                },
                {
                    "kind": "compute#securityPolicyRule",
                    "description": "",
                    "priority": 1003,
                    "match": {
                        "expr": {
                            "expression": "evaluatePreconfiguredWaf('rce-v33-stable', {'sensitivity': 1}) || evaluatePreconfiguredWaf('rce-v33-stable', {'sensitivity': 3})"
                        }
                    },
                    "action": "deny(403)",
                    "preview": False,
                    "headerAction": {},
                },
                {
                    "kind": "compute#securityPolicyRule",
                    "description": "",
                    "priority": 1004,
                    "match": {
                        "expr": {
                            "expression": "evaluatePreconfiguredExpr('rfi-v33-stable')"
                        }
                    },
                    "action": "deny(403)",
                    "preview": False,
                    "headerAction": {},
                },
                {
                    "kind": "compute#securityPolicyRule",
                    "description": "",
                    "priority": 1005,
                    "match": {
                        "expr": {
                            "expression": "evaluatePreconfiguredExpr('scannerdetection-v33-stable')"
                        }
                    },
                    "action": "deny(403)",
                    "preview": False,
                    "headerAction": {},
                },
                {
                    "kind": "compute#securityPolicyRule",
                    "description": "",
                    "priority": 1006,
                    "match": {
                        "expr": {
                            "expression": "evaluatePreconfiguredExpr('protocolattack-v33-stable')"
                        }
                    },
                    "action": "deny(403)",
                    "preview": False,
                    "headerAction": {},
                },
                {
                    "kind": "compute#securityPolicyRule",
                    "description": "",
                    "priority": 1008,
                    "match": {
                        "expr": {
                            "expression": "evaluatePreconfiguredExpr('cve-canary')"
                        }
                    },
                    "action": "deny(403)",
                    "preview": False,
                    "headerAction": {},
                },
                {
                    "kind": "compute#securityPolicyRule",
                    "description": "Default allow all rule",
                    "priority": 2147483647,
                    "match": {
                        "versionedExpr": "SRC_IPS_V1",
                        "config": {"srcIpRanges": ["*"]},
                    },
                    "action": "allow",
                    "preview": False,
                    "headerAction": {},
                },
            ],
            "fingerprint": "C80RqDu3TxA=",
            "selfLink": "https://www.googleapis.com/compute/v1/projects/{gcp_project}/global/securityPolicies/cloud-armor-waf-policy",
            "type": "CLOUD_ARMOR",
            "labelFingerprint": "43WpSiB8rYM=",
        }
    ]


@pytest.fixture(scope="session")
def gcp_vpc_networks(
    gcp_project: str,
    gcp_region: str,
) -> list[dict[str, Any]]:
    return [
        {
            "kind": "compute#network",
            "id": "8198762671780854345",
            "creationTimestamp": "2023-08-18T03:25:27.855-07:00",
            "name": f"{gcp_project}-demo-vpc",
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/global/networks/{gcp_project}-demo-vpc",
            "selfLinkWithId": f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/global/networks/8198762671780854345",
            "autoCreateSubnetworks": False,
            "subnetworks": [
                f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/regions/{gcp_region}/subnetworks/{gcp_project}-demo-subnet"
            ],
            "peerings": [
                {
                    "name": "servicenetworking-googleapis-com",
                    "network": "https://www.googleapis.com/compute/v1/projects/e36e7da775b77ab11p-tp/global/networks/servicenetworking",
                    "state": "ACTIVE",
                    "stateDetails": "[2023-08-22T03:19:16.069-07:00]: Connected.",
                    "autoCreateRoutes": True,
                    "exportCustomRoutes": False,
                    "importCustomRoutes": False,
                    "exchangeSubnetRoutes": True,
                    "exportSubnetRoutesWithPublicIp": False,
                    "importSubnetRoutesWithPublicIp": False,
                    "stackType": "IPV4_ONLY",
                }
            ],
            "routingConfig": {"routingMode": "GLOBAL"},
            "networkFirewallPolicyEnforcementOrder": "AFTER_CLASSIC_FIREWALL",
        },
        {
            "kind": "compute#network",
            "id": "276817910687905639",
            "creationTimestamp": "2023-02-10T09:56:14.453-08:00",
            "name": f"{gcp_project}-vpc",
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/global/networks/{gcp_project}-vpc",
            "selfLinkWithId": f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/global/networks/276817910687905639",
            "autoCreateSubnetworks": False,
            "subnetworks": [
                f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/regions/{gcp_region}/subnetworks/{gcp_project}-subnet",
            ],
            "peerings": [
                {
                    "name": "servicenetworking-googleapis-com",
                    "network": "https://www.googleapis.com/compute/v1/projects/xa321698e3390dfc6p-tp/global/networks/servicenetworking",
                    "state": "ACTIVE",
                    "stateDetails": "[2023-02-10T09:59:15.029-08:00]: Connected.",
                    "autoCreateRoutes": True,
                    "exportCustomRoutes": True,
                    "importCustomRoutes": False,
                    "exchangeSubnetRoutes": True,
                    "exportSubnetRoutesWithPublicIp": False,
                    "importSubnetRoutesWithPublicIp": False,
                    "stackType": "IPV4_ONLY",
                }
            ],
            "routingConfig": {"routingMode": "GLOBAL"},
            "networkFirewallPolicyEnforcementOrder": "AFTER_CLASSIC_FIREWALL",
        },
    ]


@pytest.fixture(scope="session")
def gcp_vpc_subnets(
    gcp_project: str,
    gcp_region: str,
    gcp_gke_cluster_name: str,
) -> list[dict[str, Any]]:
    return [
        {
            "kind": "compute#subnetwork",
            "id": "9081669609185438966",
            "creationTimestamp": "2024-03-07T07:17:05.764-08:00",
            "name": "k8s-dummy",
            "description": "",
            "network": f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/global/networks/k8s-dummy",
            "ipCidrRange": "10.0.10.0/24",
            "gatewayAddress": "10.0.10.1",
            "region": f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/regions/{gcp_region}",
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/regions/{gcp_region}/subnetworks/k8s-dummy",
            "privateIpGoogleAccess": True,
            "secondaryIpRanges": [
                {
                    "rangeName": f"gke-{gcp_gke_cluster_name}-pods-8ba2b403",
                    "ipCidrRange": "10.236.0.0/14",
                    "reservedInternalRange": f"https://networkconnectivity.googleapis.com/v1/projects/{gcp_project}/locations/global/internalRanges/gke-{gcp_gke_cluster_name}-pods-8ba2b403",
                },
                {
                    "rangeName": f"gke-{gcp_gke_cluster_name}-services-8ba2b403",
                    "ipCidrRange": "10.232.208.0/20",
                    "reservedInternalRange": f"https://networkconnectivity.googleapis.com/v1/projects/{gcp_project}/locations/global/internalRanges/gke-{gcp_gke_cluster_name}-services-8ba2b403",
                },
            ],
            "fingerprint": "dzixcuBWUFA=",
            "enableFlowLogs": False,
            "privateIpv6GoogleAccess": "DISABLE_GOOGLE_ACCESS",
            "purpose": "PRIVATE",
            "logConfig": {
                "enable": False,
                "aggregationInterval": "INTERVAL_5_SEC",
                "flowSampling": 0.5,
                "metadata": "INCLUDE_ALL_METADATA",
            },
            "stackType": "IPV4_ONLY",
        },
        {
            "kind": "compute#subnetwork",
            "id": "2343700906476575489",
            "creationTimestamp": "2023-08-18T03:25:50.276-07:00",
            "name": f"{gcp_project}-demo-subnet",
            "network": f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/global/networks/{gcp_project}-demo-vpc",
            "ipCidrRange": "10.10.11.0/24",
            "gatewayAddress": "10.10.11.1",
            "region": f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/regions/{gcp_region}",
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/regions/{gcp_region}/subnetworks/{gcp_project}-demo-subnet",
            "privateIpGoogleAccess": False,
            "fingerprint": "J9WCTYERFvs=",
            "enableFlowLogs": False,
            "privateIpv6GoogleAccess": "DISABLE_GOOGLE_ACCESS",
            "purpose": "PRIVATE",
            "logConfig": {
                "enable": False,
                "aggregationInterval": "INTERVAL_5_SEC",
                "flowSampling": 0.5,
                "metadata": "INCLUDE_ALL_METADATA",
            },
            "stackType": "IPV4_ONLY",
        },
        {
            "kind": "compute#subnetwork",
            "id": "47568586173111221787",
            "creationTimestamp": "2023-02-10T09:56:38.882-08:00",
            "name": f"{gcp_project}-subnet",
            "network": f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/global/networks/{gcp_project}-vpc",
            "ipCidrRange": "10.10.10.0/24",
            "gatewayAddress": "10.10.10.1",
            "region": f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/regions{gcp_region}",
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/regions/{gcp_region}/subnetworks/{gcp_project}-subnet",
            "privateIpGoogleAccess": False,
            "fingerprint": "cAOmFIA_hYt=",
            "enableFlowLogs": False,
            "privateIpv6GoogleAccess": "DISABLE_GOOGLE_ACCESS",
            "purpose": "PRIVATE",
            "logConfig": {
                "enable": False,
                "aggregationInterval": "INTERVAL_5_SEC",
                "flowSampling": 0.5,
                "metadata": "INCLUDE_ALL_METADATA",
            },
            "stackType": "IPV4_ONLY",
        },
    ]


@pytest.fixture(scope="session")
def gcp_sql_instances(
    gcp_project: str,
    gcp_project_number: str,
    gcp_region: str,
    gcp_sql_instance_name: str,
) -> list[dict[str, Any]]:
    return [
        {
            "kind": "sql#instance",
            "state": "RUNNABLE",
            "databaseVersion": "POSTGRES_14",
            "settings": {
                "authorizedGaeApplications": [],
                "tier": "db-g1-small",
                "kind": "sql#settings",
                "availabilityType": "REGIONAL",
                "pricingPlan": "PER_USE",
                "replicationType": "SYNCHRONOUS",
                "activationPolicy": "ALWAYS",
                "ipConfiguration": {
                    "privateNetwork": f"projects/{gcp_project}/global/networks/{gcp_project}-demo-vpc",
                    "authorizedNetworks": [],
                    "sslMode": "TRUSTED_CLIENT_CERTIFICATE_REQUIRED",
                    "ipv4Enabled": False,
                    "requireSsl": True,
                    "enablePrivatePathForGoogleCloudServices": False,
                },
                "locationPreference": {
                    "zone": "{gcp_region}-b",
                    "kind": "sql#locationPreference",
                },
                "dataDiskType": "PD_SSD",
                "maintenanceWindow": {
                    "kind": "sql#maintenanceWindow",
                    "hour": 0,
                    "day": 0,
                },
                "backupConfiguration": {
                    "startTime": "09:00",
                    "kind": "sql#backupConfiguration",
                    "location": "eu",
                    "backupRetentionSettings": {
                        "retentionUnit": "COUNT",
                        "retainedBackups": 7,
                    },
                    "enabled": True,
                    "replicationLogArchivingEnabled": True,
                    "pointInTimeRecoveryEnabled": True,
                    "transactionLogRetentionDays": 7,
                    "transactionalLogStorageState": "CLOUD_STORAGE",
                },
                "insightsConfig": {},
                "connectorEnforcement": "NOT_REQUIRED",
                "settingsVersion": "92",
                "storageAutoResizeLimit": "0",
                "storageAutoResize": True,
                "dataDiskSizeGb": "10",
                "deletionProtectionEnabled": False,
            },
            "etag": "6b1b361752ce3be3d99c9a56bcfac9d0d7819769cc12eb3b66ad4e7550bb5bd6",
            "failoverReplica": {"available": True},
            "ipAddresses": [{"type": "PRIVATE", "ipAddress": "10.53.0.2"}],
            "serverCaCert": {
                "kind": "sql#sslCert",
                "certSerialNumber": "0",
                "cert": "...",
                "commonName": "...",
                "sha1Fingerprint": "4e1243bd22c66e76c2ba9eddc1f91394e57f9f83",
                "instance": gcp_sql_instance_name,
                "createTime": "2023-08-18T10:29:22.350Z",
                "expirationTime": "2033-08-15T10:30:22.350Z",
            },
            "instanceType": "CLOUD_SQL_INSTANCE",
            "project": gcp_project,
            "serviceAccountEmailAddress": f"p{gcp_project_number}-3iu1fg@gcp-sa-cloud-sql.iam.gserviceaccount.com",
            "backendType": "SECOND_GEN",
            "selfLink": f"https://sqladmin.googleapis.com/v1/projects/{gcp_project}/instances/{gcp_sql_instance_name}",
            "connectionName": f"{gcp_project}:{gcp_region}:{gcp_sql_instance_name}",
            "name": gcp_sql_instance_name,
            "region": "{gcp_region}",
            "gceZone": "{gcp_region}-b",
            "secondaryGceZone": "{gcp_region}-d",
            "databaseInstalledVersion": "POSTGRES_14_12",
            "maintenanceVersion": "POSTGRES_14_12.R20240514.00_04",
            "createTime": "2023-08-18T10:26:43.081Z",
            "sqlNetworkArchitecture": "NEW_NETWORK_ARCHITECTURE",
        }
    ]


@pytest.fixture(scope="session")
def gcp_sql_users(
    gcp_project: str,
    gcp_sql_instance_user_name: str,
    gcp_sql_instance_name: str,
) -> list[dict[str, Any]]:
    return [
        {
            "kind": "sql#user",
            "etag": "...",
            "name": gcp_sql_instance_user_name,
            "host": "",
            "instance": gcp_sql_instance_name,
            "project": gcp_project,
        }
    ]


@pytest.fixture(scope="session")
def gcp_sql_databases(
    gcp_project: str,
    gcp_sql_instance_name: str,
    gcp_sql_instance_database_name: str,
) -> list[dict[str, Any]]:
    return [
        {
            "kind": "sql#database",
            "charset": "UTF8",
            "collation": "en_US.UTF8",
            "etag": "...",
            "name": "postgres",
            "instance": gcp_sql_instance_name,
            "selfLink": f"https://sqladmin.googleapis.com/v1/projects/{gcp_project}/instances/{gcp_sql_instance_name}/databases/{gcp_sql_instance_database_name}",
            "project": gcp_project,
        }
    ]


@pytest.fixture(scope="session")
def gcp_monitoring_services(
    gcp_project: str,
    gcp_region: str,
    gcp_gke_cluster_name: str,
    gcp_project_number: str,
) -> list[dict[str, Any]]:
    return [
        {
            "name": f"projects/{gcp_project_number}/services/demo-service",
            "displayName": "Demo service",
            "cloudRun": {"serviceName": "demo", "location": gcp_region},
            "basicService": {
                "serviceType": "CLOUD_RUN",
                "serviceLabels": {
                    "location": gcp_region,
                    "service_name": "demo",
                },
            },
        },
        {
            "name": f"projects/{gcp_project_number}/services/ist:{gcp_project}-location-{gcp_region}-{gcp_gke_cluster_name}-default-demo",
            "displayName": "consumer",
            "telemetry": {
                "resourceName": f"//container.googleapis.com/projects/{gcp_project}/locations/{gcp_region}/clusters/{gcp_gke_cluster_name}/k8s/namespaces/default/services/demo"
            },
            "gkeService": {
                "projectId": gcp_project,
                "location": gcp_region,
                "clusterName": gcp_gke_cluster_name,
                "namespaceName": "default",
                "serviceName": "demo",
            },
            "basicService": {
                "serviceType": "GKE_SERVICE",
                "serviceLabels": {
                    "cluster_name": gcp_gke_cluster_name,
                    "location": gcp_region,
                    "namespace_name": "default",
                    "project_id": gcp_project,
                    "service_name": "demo",
                },
            },
        },
    ]


@pytest.fixture(scope="session")
def gcp_monitoring_slo(
    gcp_project: str,
    gcp_region: str,
    gcp_project_number: str,
    gcp_gke_cluster_name: str,
) -> list[dict[str, Any]]:
    return [
        {
            "name": f"projects/{gcp_project_number}/services/demo-service/serviceLevelObjectives/ePaA7SMgBHqIeTyyiQyrZg",
            "serviceLevelIndicator": {
                "requestBased": {
                    "goodTotalRatio": {
                        "goodServiceFilter": f'resource.labels.project_id = "{gcp_project}" AND resource.type = "cloud_run_revision" AND resource.labels.location = "{gcp_region}" AND resource.labels.service_name = "demo" AND metric.type = "run.googleapis.com/request_count" AND metric.labels.response_code_class = "2xx"',
                        "badServiceFilter": f'resource.labels.project_id = "{gcp_project}" AND resource.type = "cloud_run_revision" AND resource.labels.location = "{gcp_region}" AND resource.labels.service_name = "demo" AND metric.type = "run.googleapis.com/request_count" AND metric.labels.response_code_class = "5xx"',
                    }
                }
            },
            "goal": 0.95,
            "calendarPeriod": "WEEK",
            "displayName": "95% - Availability - Calendar week",
        },
        {
            "name": f"projects/{gcp_project_number}/services/demo-service/serviceLevelObjectives/ly7qEQ1yRUaRMnGhT8Us8b",
            "serviceLevelIndicator": {
                "requestBased": {
                    "distributionCut": {
                        "distributionFilter": f'resource.labels.project_id = "{gcp_project}" AND resource.type = "cloud_run_revision" AND resource.labels.location = "{gcp_region}" AND resource.labels.service_name = "demo" AND metric.type = "run.googleapis.com/request_latencies" AND metric.labels.response_code_class = "2xx"',
                        "range": {"min": "-Infinity", "max": 250},
                    }
                }
            },
            "goal": 0.95,
            "calendarPeriod": "WEEK",
            "displayName": "95% - Latency - Calendar week",
        },
        {
            "name": f"projects/{gcp_project_number}/services/ist:{gcp_project}-location-{gcp_region}-{gcp_gke_cluster_name}-default-demo/serviceLevelObjectives/PO1ph13MYbCQaTgXIwUYLg",
            "serviceLevelIndicator": {
                "windowsBased": {
                    "goodTotalRatioThreshold": {
                        "performance": {
                            "distributionCut": {
                                "distributionFilter": 'metric.type="loadbalancing.googleapis.com/https/total_latencies" resource.type="https_lb_rule" metric.labels.response_code="200" resource.labels.backend_name="k8s1-f2804333-default-demo-8080-7ype3f1a" resource.labels.backend_target_name="gkegw1-wwbg-default-demo-8080-k9o8ddmf9emo"',
                                "range": {"min": -9007199254740991, "max": 400},
                            }
                        },
                        "threshold": 0.95,
                    },
                    "windowPeriod": "60s",
                }
            },
            "goal": 0.98,
            "calendarPeriod": "DAY",
            "displayName": "98% - Consumer E2E Latency - Calendar day",
        },
    ]


@pytest.fixture(scope="session")
def gcp_monitoring_alert_policies(
    gcp_project: str,
    gcp_region: str,
    gcp_project_number: str,
    gcp_gke_cluster_name: str,
) -> list[dict[str, Any]]:
    return [
        {
            "name": f"projects/{gcp_project}/alertPolicies/15766192705010179244",
            "displayName": "Burn rate on 98% - Consumer E2E Latency - Calendar day",
            "combiner": "OR",
            "creationRecord": {
                "mutateTime": "2024-05-30T19:32:01.159000572Z",
                "mutatedBy": "me@example.com",
            },
            "mutationRecord": {
                "mutateTime": "2024-05-30T20:06:57.817712837Z",
                "mutatedBy": "me@example.com",
            },
            "conditions": [
                {
                    "conditionThreshold": {
                        "filter": f'select_slo_burn_rate("projects/{gcp_project_number}/services/ist:{gcp_project}-location-{gcp_region}-{gcp_gke_cluster_name}-default-demo/serviceLevelObjectives/PO1ph13MYbCQaTgXIwUYLg", "60s")',
                        "comparison": "COMPARISON_GT",
                        "thresholdValue": 10,
                        "duration": "0s",
                        "trigger": {"count": 1},
                        "aggregations": [
                            {
                                "alignmentPeriod": "300s",
                                "perSeriesAligner": "ALIGN_MAX",
                            }
                        ],
                    },
                    "displayName": "Burn rate on 98% - Consumer E2E Latency - Calendar day",
                    "name": f"projects/{gcp_project}/alertPolicies/15766192705010179244/conditions/4203981762528173346",
                }
            ],
            "notificationChannels": [
                f"projects/{gcp_project}/notificationChannels/15347963261329368790"
            ],
            "enabled": True,
        }
    ]


@pytest.fixture(scope="session")
def gcp_monitoring_notification_channels(
    gcp_project: str,
    gcp_region: str,
    gcp_project_number: str,
    gcp_gke_cluster_name: str,
) -> list[dict[str, Any]]:
    return [
        {
            "type": "slack",
            "displayName": "Boom",
            "labels": {
                "auth_token": "....",
                "team": "Team",
                "channel_name": "#alerts",
            },
            "name": f"projects/{gcp_project}]/notificationChannels/15347963261329368790",
            "enabled": True,
            "creationRecord": {"mutateTime": "2024-05-21T12:50:59.495660677Z"},
            "mutationRecords": [
                {"mutateTime": "2024-05-21T12:50:59.495660677Z"}
            ],
        }
    ]
