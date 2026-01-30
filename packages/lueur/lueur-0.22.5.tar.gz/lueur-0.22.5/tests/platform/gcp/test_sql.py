from typing import Any

import msgspec
import pytest
import respx

from lueur.platform.gcp.sql import explore_sql

from tests.platform.gcp.utils import patch_auth


@respx.mock
@pytest.mark.asyncio
async def test_explore_sql(
    gcp_project: str,
    gcp_sql_instance_name: str,
    gcp_sql_instances: list[dict[str, Any]],
    gcp_sql_users: list[dict[str, Any]],
    gcp_sql_databases: list[dict[str, Any]],
) -> None:
    respx.post(
        "https://oauth2.googleapis.com/token",
    ).respond(content=msgspec.json.encode({"access_token": "xyz"}))

    respx.get(
        f"https://sqladmin.googleapis.com/v1/projects/{gcp_project}/instances",
    ).respond(content=msgspec.json.encode({"items": gcp_sql_instances}))

    respx.get(
        f"https://sqladmin.googleapis.com/v1/projects/{gcp_project}/instances/{gcp_sql_instance_name}/users",
    ).respond(content=msgspec.json.encode({"items": gcp_sql_users}))

    respx.get(
        f"https://sqladmin.googleapis.com/v1/projects/{gcp_project}/instances/{gcp_sql_instance_name}/databases",
    ).respond(content=msgspec.json.encode({"items": gcp_sql_databases}))

    with patch_auth():
        resources = await explore_sql(gcp_project)

    assert len(resources) == 3
