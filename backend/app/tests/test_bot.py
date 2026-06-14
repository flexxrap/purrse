import hashlib
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

_BOT_TOKEN = "test-bot-token"
_WEBHOOK_SECRET = hashlib.sha256(_BOT_TOKEN.encode()).hexdigest()


@pytest.fixture
async def client():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        yield c


@pytest.mark.asyncio
async def test_webhook_no_secret(client):
    resp = await client.post("/bot/webhook", json={"update_id": 1})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_webhook_wrong_secret(client):
    resp = await client.post(
        "/bot/webhook",
        json={"update_id": 1},
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_webhook_valid_secret_unknown_update(client):
    with patch("app.services.bot_service.handle_update", new_callable=AsyncMock) as mock_handle:
        resp = await client.post(
            "/bot/webhook",
            json={"update_id": 1},
            headers={"X-Telegram-Bot-Api-Secret-Token": _WEBHOOK_SECRET},
        )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    mock_handle.assert_awaited_once()


@pytest.mark.asyncio
async def test_webhook_start_command(client):
    update = {
        "update_id": 2,
        "message": {
            "message_id": 1,
            "from": {"id": 12345, "is_bot": False, "first_name": "Test"},
            "chat": {"id": 12345, "type": "private"},
            "text": "/start",
        },
    }
    with patch("app.services.telegram_service.send_message", new_callable=AsyncMock) as mock_send:
        resp = await client.post(
            "/bot/webhook",
            json=update,
            headers={"X-Telegram-Bot-Api-Secret-Token": _WEBHOOK_SECRET},
        )
    assert resp.status_code == 200
    assert mock_send.await_count == 2  # welcome message + persistent reply keyboard

    welcome_args = mock_send.call_args_list[0]
    assert welcome_args[0][0] == 12345  # telegram_id
    assert "purrse" in welcome_args[0][1]  # welcome text
    assert welcome_args[1].get("reply_markup", {}).get("inline_keyboard")  # has WebApp button

    keyboard_args = mock_send.call_args_list[1]
    assert keyboard_args[0][0] == 12345  # telegram_id
    assert keyboard_args[1].get("reply_markup", {}).get("keyboard")  # persistent reply keyboard


@pytest.mark.asyncio
async def test_webhook_stats_user_not_found(client):
    update = {
        "update_id": 3,
        "message": {
            "message_id": 2,
            "from": {"id": 99999, "is_bot": False, "first_name": "NoUser"},
            "chat": {"id": 99999, "type": "private"},
            "text": "/stats",
        },
    }
    with patch("app.services.telegram_service.send_message", new_callable=AsyncMock) as mock_send:
        resp = await client.post(
            "/bot/webhook",
            json=update,
            headers={"X-Telegram-Bot-Api-Secret-Token": _WEBHOOK_SECRET},
        )
    assert resp.status_code == 200
    mock_send.assert_awaited_once()
    assert "не найден" in mock_send.call_args[0][1]
