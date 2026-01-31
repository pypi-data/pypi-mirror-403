import os
from pathlib import Path

import pytest
import responses

from arkindex import ArkindexClient


@pytest.fixture(scope="session")
def api_client():
    schema_url = os.environ.get("ARKINDEX_API_SCHEMA_URL")
    local_path = Path("schema.yml")
    if not schema_url and local_path.exists():
        with local_path.open("rb") as f:
            schema_url = "http://testserver/schema.yml"
            responses.add(
                responses.GET,
                schema_url,
                body=f.read(),
            )
    else:
        # Default to production API schema
        schema_url = (
            schema_url
            or "https://arkindex.teklia.com/api/v1/openapi/?format=openapi-json"
        )
        responses.add_passthru(schema_url)
    return ArkindexClient(base_url="http://testserver", schema_url=schema_url)
