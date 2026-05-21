from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_legacy_health(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_live(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


@pytest.mark.asyncio
async def test_health_ready_success(async_client: AsyncClient):
    # Mock settings to have a fake API key
    mock_settings = AsyncMock()
    mock_settings.mistral_api_key = "fake_key"

    # Mock the HTTPX async client get response
    mock_response = AsyncMock()
    mock_response.status_code = 200

    with patch("rag.api.routers.health.get_settings", return_value=mock_settings):
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            response = await async_client.get("/api/v1/health/ready")
            assert response.status_code == 200
            assert response.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_health_ready_unhealthy_mistral(async_client: AsyncClient):
    # Mock settings to have a fake API key
    mock_settings = AsyncMock()
    mock_settings.mistral_api_key = "fake_key"

    # Mock the HTTPX async client get response to return 500
    mock_response = AsyncMock()
    mock_response.status_code = 500

    with patch("rag.api.routers.health.get_settings", return_value=mock_settings):
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            response = await async_client.get("/api/v1/health/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["detail"]["status"] == "unready"
            assert "mistral_api" in data["detail"]["components"]
