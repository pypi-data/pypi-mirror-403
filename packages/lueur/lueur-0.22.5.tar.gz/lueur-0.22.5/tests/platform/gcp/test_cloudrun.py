from typing import Any

import msgspec
import pytest
import respx

from lueur.platform.gcp.cloudrun import explore_cloudrun, expand_links

from tests.platform.gcp.utils import patch_auth


@respx.mock
@pytest.mark.asyncio
async def test_explore_cloudrun(
    gcp_project: str,
    gcp_region: str,
    gcp_cloudrun_services: list[dict[str, Any]],
    gcp_cloudrun_connectors: list[dict[str, Any]],
) -> None:
    respx.post(
        "https://oauth2.googleapis.com/token",
    ).respond(content=msgspec.json.encode({"access_token": "xyz"}))

    respx.get(
        f"https://run.googleapis.com/v2/projects/{gcp_project}/locations/{gcp_region}/services",
    ).respond(content=msgspec.json.encode({"services": gcp_cloudrun_services}))

    respx.get(
        f"https://vpcaccess.googleapis.com/v1beta1/projects/{gcp_project}/locations/{gcp_region}/connectors",
    ).respond(
        content=msgspec.json.encode({"connectors": gcp_cloudrun_connectors})
    )

    with patch_auth():
        resources = await explore_cloudrun(gcp_project, gcp_region)

    assert len(resources) == 2
