import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """
    Verifies that the API entry point returns operational status in an envelope.
    """
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "operational"
    assert "timestamp" in data["meta"]

@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """
    Verifies detailed database and resource health check routing.
    """
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert data["data"]["database_connected"] is True
    assert "system_metrics" in data["data"]

@pytest.mark.asyncio
async def test_system_status_endpoint(client: AsyncClient):
    """
    Verifies detailed system status endpoint response.
    """
    response = await client.get("/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert data["data"]["database_connected"] is True
    assert "system_metrics" in data["data"]

@pytest.mark.asyncio
async def test_ready_endpoint(client: AsyncClient):
    """
    Verifies readiness validation.
    """
    response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

@pytest.mark.asyncio
async def test_live_endpoint(client: AsyncClient):
    """
    Verifies web server liveness execution.
    """
    response = await client.get("/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}

@pytest.mark.asyncio
async def test_version_endpoint(client: AsyncClient):
    """
    Verifies software release tags.
    """
    response = await client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["version"] == "0.1.0"
