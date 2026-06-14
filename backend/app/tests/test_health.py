import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_security_headers(client):
    response = await client.get("/health")
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "max-age=31536000" in response.headers["strict-transport-security"]
    assert "default-src 'self'" in response.headers["content-security-policy"]


@pytest.mark.asyncio
async def test_unknown_host_rejected():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://evil.com") as c:
        response = await c.get("/health")
    assert response.status_code == 400
