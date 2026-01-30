from typing import Any

import msgspec
import pytest
import respx

from lueur.platform.gcp.monitoring import explore_monitoring

from tests.platform.gcp.utils import patch_auth


@respx.mock
@pytest.mark.asyncio
async def test_explore_monitoring(
    gcp_project: str,
    gcp_project_number: str,
    gcp_region: str,
    gcp_gke_cluster_name: str,
    gcp_monitoring_services: list[dict[str, Any]],
    gcp_monitoring_slo: list[dict[str, Any]],
    gcp_monitoring_alert_policies: list[dict[str, Any]],
    gcp_monitoring_notification_channels: list[dict[str, Any]],
) -> None:
    respx.post(
        "https://oauth2.googleapis.com/token",
    ).respond(content=msgspec.json.encode({"access_token": "xyz"}))

    respx.get(
        f"https://monitoring.googleapis.com/v3/projects/{gcp_project}/services",
    ).respond(
        content=msgspec.json.encode({"services": gcp_monitoring_services})
    )

    respx.get(
        f"https://monitoring.googleapis.com/v3/projects/{gcp_project_number}/services/ist:{gcp_project}-location-{gcp_region}-{gcp_gke_cluster_name}-default-demo/serviceLevelObjectives",
    ).respond(
        content=msgspec.json.encode(
            {"serviceLevelObjectives": [gcp_monitoring_slo[0]]}
        )
    )

    respx.get(
        f"https://monitoring.googleapis.com/v3/projects/{gcp_project_number}/services/demo-service/serviceLevelObjectives",
    ).respond(
        content=msgspec.json.encode(
            {"serviceLevelObjectives": [gcp_monitoring_slo[1]]}
        )
    )

    respx.get(
        f"https://monitoring.googleapis.com/v3/projects/{gcp_project}/alertPolicies",
    ).respond(
        content=msgspec.json.encode(
            {"alertPolicies": gcp_monitoring_alert_policies}
        )
    )

    respx.get(
        f"https://monitoring.googleapis.com/v3/projects/{gcp_project}/notificationChannels",
    ).respond(
        content=msgspec.json.encode(
            {"notificationChannels": gcp_monitoring_notification_channels}
        )
    )

    respx.get(
        f"https://monitoring.googleapis.com/v3/projects/{gcp_project}/groups",
    ).respond(content=msgspec.json.encode({"group": []}))

    with patch_auth():
        resources = await explore_monitoring(gcp_project)

    assert len(resources) == 6
