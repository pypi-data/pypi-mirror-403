import msgspec
import pytest
import respx

from lueur.platform.gcp.region import list_project_regions

from tests.platform.gcp.utils import patch_auth


@respx.mock
@pytest.mark.asyncio
async def test_list_project_regions(gcp_project: str) -> None:
    respx.post(
        "https://oauth2.googleapis.com/token",
    ).respond(content=msgspec.json.encode({"access_token": "xyz"}))

    respx.get(
        f"https://compute.googleapis.com/compute/v1/projects/{gcp_project}/regions",
        params={"fields": "items.name"},
    ).respond(content=msgspec.json.encode({"items": [{"name": "us-east1"}]}))

    with patch_auth():
        assert await list_project_regions(gcp_project) == ["us-east1"]
