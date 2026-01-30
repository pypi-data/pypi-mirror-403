from typing import Any

import msgspec
import pytest
import respx

from lueur.platform.gcp.vpc import explore_vpc

from tests.platform.gcp.utils import patch_auth


@respx.mock
@pytest.mark.asyncio
async def test_explore_vpc(
    gcp_project: str,
    gcp_region: str,
    gcp_vpc_networks: list[dict[str, Any]],
    gcp_vpc_subnets: list[dict[str, Any]],
) -> None:
    respx.post(
        "https://oauth2.googleapis.com/token",
    ).respond(content=msgspec.json.encode({"access_token": "xyz"}))

    respx.get(
        f"https://compute.googleapis.com/compute/v1/projects/{gcp_project}/global/networks",
    ).respond(content=msgspec.json.encode({"items": gcp_vpc_networks}))

    respx.get(
        f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/regions/{gcp_region}/subnetworks/{gcp_project}-subnet",
    ).respond(content=msgspec.json.encode(gcp_vpc_subnets[2]))

    respx.get(
        f"https://www.googleapis.com/compute/v1/projects/{gcp_project}/regions/{gcp_region}/subnetworks/{gcp_project}-demo-subnet",
    ).respond(content=msgspec.json.encode(gcp_vpc_subnets[1]))

    with patch_auth():
        resources = await explore_vpc(gcp_project)
    assert len(resources) == 4
