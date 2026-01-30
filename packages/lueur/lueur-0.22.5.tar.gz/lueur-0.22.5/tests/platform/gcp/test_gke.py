from typing import Any

import msgspec
import pytest
import respx

from lueur.platform.gcp.gke import explore_gke

from tests.platform.gcp.utils import patch_auth


@respx.mock
@pytest.mark.asyncio
async def test_explore_connector(
    gcp_project: str,
    gcp_region: str,
    gcp_gke_cluster_name: str,
    gcp_gke_clusters: list[dict[str, Any]],
    gcp_gke_cluster_nodepools: list[dict[str, Any]],
) -> None:
    respx.post(
        "https://oauth2.googleapis.com/token",
    ).respond(content=msgspec.json.encode({"access_token": "xyz"}))

    respx.get(
        f"https://container.googleapis.com/v1/projects/{gcp_project}/locations/{gcp_region}/clusters",
    ).respond(content=msgspec.json.encode({"clusters": gcp_gke_clusters}))

    respx.get(
        f"https://container.googleapis.com/v1/projects/{gcp_project}/locations/{gcp_region}/clusters/{gcp_gke_cluster_name}/nodePools",
    ).respond(
        content=msgspec.json.encode({"nodePools": gcp_gke_cluster_nodepools})
    )

    with patch_auth():
        resources = await explore_gke(gcp_project, gcp_region)
