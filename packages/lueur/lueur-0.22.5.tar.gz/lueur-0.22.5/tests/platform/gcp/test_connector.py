from typing import Any

import msgspec
import pytest
import respx

from lueur.platform.gcp.connector import explore_connector

from tests.platform.gcp.utils import patch_auth


@respx.mock
@pytest.mark.asyncio
async def test_explore_connector(
    gcp_project: str,
    gcp_region: str,
) -> None:
    respx.post(
        "https://oauth2.googleapis.com/token",
    ).respond(content=msgspec.json.encode({"access_token": "xyz"}))

    respx.get(
        f"https://connectors.googleapis.com/v1/projects/{gcp_project}/locations/{gcp_region}/providers",
    ).respond(content=msgspec.json.encode({"providers": []}))

    respx.get(
        f"https://connectors.googleapis.com/v1/projects/{gcp_project}/locations/{gcp_region}/connectors",
    ).respond(content=msgspec.json.encode({"connectors": []}))

    respx.get(
        f"https://connectors.googleapis.com/v1/projects/{gcp_project}/locations/{gcp_region}/connections",
    ).respond(content=msgspec.json.encode({"connectors": []}))

    with patch_auth():
        resources = await explore_connector(gcp_project, gcp_region)
