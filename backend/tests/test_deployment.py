import os
import pytest
from httpx import AsyncClient

def test_docker_files_existence():
    """
    Ensure Dockerfile, .dockerignore and docker-compose.yml exist at root.
    """
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    assert os.path.exists(os.path.join(root_dir, "Dockerfile"))
    assert os.path.exists(os.path.join(root_dir, "docker-compose.yml"))
    assert os.path.exists(os.path.join(root_dir, ".dockerignore"))
    assert os.path.exists(os.path.join(root_dir, "backend", "Dockerfile"))
    assert os.path.exists(os.path.join(root_dir, "backend", "docker-compose.yml"))

@pytest.mark.asyncio
async def test_deployment_healthcheck_urls(client: AsyncClient):
    """
    Test endpoints consumed by Docker/Compose healthchecks.
    """
    # Liveness check used by Docker health check
    res = await client.get("/live")
    assert res.status_code == 200
    assert res.json()["status"] == "alive"

    # Readiness check
    res = await client.get("/ready")
    assert res.status_code == 200
    assert res.json()["status"] == "ready"

    # Full system health status endpoint
    res = await client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["database_connected"] is True
