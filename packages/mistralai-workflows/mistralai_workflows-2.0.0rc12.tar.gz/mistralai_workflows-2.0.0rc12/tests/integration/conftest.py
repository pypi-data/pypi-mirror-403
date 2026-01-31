import os

import httpx
import pytest


@pytest.fixture
def api_client() -> httpx.AsyncClient:
    abraxas_url = os.getenv("ABRAXAS_URL", "https://api.globalaegis.net")
    api_key = os.getenv("MISTRAL_API_KEY")

    return httpx.AsyncClient(
        base_url=abraxas_url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        timeout=120.0,
    )
