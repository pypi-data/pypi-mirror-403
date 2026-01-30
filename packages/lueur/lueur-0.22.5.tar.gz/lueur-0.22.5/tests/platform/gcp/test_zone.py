import msgspec
import pytest
import respx

from lueur.platform.gcp.zone import (
    list_project_zones,
    list_project_region_zones,
)

from tests.platform.gcp.utils import patch_auth


@respx.mock
@pytest.mark.asyncio
async def test_list_project_zones(gcp_project: str) -> None:
    respx.post(
        "https://oauth2.googleapis.com/token",
    ).respond(content=msgspec.json.encode({"access_token": "xyz"}))

    respx.get(
        f"https://compute.googleapis.com/compute/v1/projects/{gcp_project}/zones",
        params={"fields": "items.name"},
    ).respond(content=msgspec.json.encode({"items": [{"name": "us-east1-a"}]}))

    with patch_auth():
        assert await list_project_zones(gcp_project) == ["us-east1-a"]


@respx.mock
@pytest.mark.asyncio
async def test_list_project_region_zones(
    gcp_project: str, gcp_region: str
) -> None:
    respx.post(
        "https://oauth2.googleapis.com/token",
    ).respond(content=msgspec.json.encode({"access_token": "xyz"}))

    respx.get(
        f"https://compute.googleapis.com/compute/v1/projects/{gcp_project}/regions/{gcp_region}/zones",
        params={"fields": "items.name"},
    ).respond(content=msgspec.json.encode({"items": [{"name": "us-east1-a"}]}))

    with patch_auth():
        assert await list_project_region_zones(gcp_project, gcp_region) == [
            "us-east1-a"
        ]
