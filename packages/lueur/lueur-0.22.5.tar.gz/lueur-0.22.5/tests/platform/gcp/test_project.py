import msgspec
import pytest
import respx

from lueur.make_id import make_id
from lueur.models import GCPProject
from lueur.platform.gcp.project import (
    list_organization_projects,
    list_all_projects,
)

from tests.platform.gcp.utils import patch_auth


@respx.mock
@pytest.mark.asyncio
async def test_list_organization_projects(
    gcp_org_id: str, gcp_project: str
) -> None:
    respx.post(
        "https://oauth2.googleapis.com/token",
    ).respond(content=msgspec.json.encode({"access_token": "xyz"}))

    respx.get(
        f"https://cloudresourcemanager.googleapis.com/v3/projects",
        params={"parent": f"organizations/{gcp_org_id}"},
    ).respond(
        content=msgspec.json.encode({"projects": [{"name": gcp_project}]})
    )

    with patch_auth():
        assert await list_organization_projects(gcp_org_id) == [gcp_project]


@respx.mock
@pytest.mark.asyncio
async def test_list_all_projects(gcp_org_id: str, gcp_project: str) -> None:
    respx.post(
        "https://oauth2.googleapis.com/token",
    ).respond(content=msgspec.json.encode({"access_token": "xyz"}))

    respx.get(
        f"https://cloudresourcemanager.googleapis.com/v3/projects:search",
        params={"query": "state:ACTIVE"},
    ).respond(
        content=msgspec.json.encode(
            {
                "projects": [
                    {
                        "parent": f"organizations/{gcp_org_id}",
                        "name": gcp_project,
                        "displayName": "my org",
                    }
                ]
            }
        )
    )

    with patch_auth():
        assert await list_all_projects() == [
            GCPProject(
                organization=f"organizations/{gcp_org_id}",
                id=make_id(gcp_project),
                name="my org",
            )
        ]
