"""
Unit tests for telegram_rag_bot.main.track_usage callback.

Tests cover:
- track_usage logs structured data correctly
- track_usage fail-silent behavior (doesn't crash on errors)
- HTTP POST to Platform API (v0.9.0+)
- Retry logic with exponential backoff
- 429 Quota Exceeded handling
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from typing import TypedDict
import aiohttp


# Type stub for UsageData (matches orchestrator v0.7.6)
class UsageData(TypedDict):
    """Usage data from Router (tokens, cost, latency, success status)."""

    provider_name: str
    model: str
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    cost: float
    latency_ms: int
    success: bool


@pytest.mark.asyncio
async def test_track_usage_logs_correctly():
    """Test that track_usage logs structured data."""
    from telegram_rag_bot.main import track_usage

    data: UsageData = {
        "provider_name": "gigachat",
        "model": "GigaChat-Pro",
        "total_tokens": 150,
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "cost": 0.45,
        "latency_ms": 1200,
        "success": True,
    }

    with patch("telegram_rag_bot.main.logger.info") as mock_logger:
        await track_usage(data)

        # Verify logger called with correct message
        mock_logger.assert_called_once()
        call_args = mock_logger.call_args
        assert call_args[0][0] == "llm_usage_tracked"

        # Verify structured data
        usage = call_args[1]["extra"]["usage"]
        assert usage["provider"] == "gigachat"
        assert usage["total_tokens"] == 150
        assert usage["cost_rub"] == 0.45
        assert usage["success"] is True


@pytest.mark.asyncio
async def test_track_usage_fail_silent():
    """Test that track_usage doesn't crash on errors."""
    from telegram_rag_bot.main import track_usage

    data: UsageData = {
        "provider_name": "gigachat",
        "model": "GigaChat-Pro",
        "total_tokens": 150,
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "cost": 0.45,
        "latency_ms": 1200,
        "success": True,
    }

    with (
        patch("telegram_rag_bot.main.logger.info", side_effect=Exception("Test error")),
        patch("telegram_rag_bot.main.logger.warning") as mock_warning,
    ):
        # Should NOT raise exception
        await track_usage(data)

        # Verify warning was logged
        mock_warning.assert_called_once()
        assert "Usage tracking callback failed" in mock_warning.call_args[0][0]


# === HTTP POST tests (v0.9.0+) ===


@pytest.mark.asyncio
async def test_create_track_usage_callback_http_post_success():
    """Test that HTTP POST is sent successfully when callback_url is set."""
    from telegram_rag_bot.main import create_track_usage_callback

    # Mock aiohttp session
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_session.post.return_value = mock_response

    # Create callback
    callback = create_track_usage_callback(
        tenant_id="550e8400-e29b-41d4-a716-446655440000",
        callback_url="https://platform.example.com",
        platform_key_id="987fcdeb-51a2-...",
        http_session=mock_session,
    )

    data: UsageData = {
        "provider_name": "gigachat_primary",
        "model": "GigaChat-Pro",
        "total_tokens": 450,
        "prompt_tokens": 150,
        "completion_tokens": 300,
        "cost": 0.0135,
        "latency_ms": 1234,
        "success": True,
    }

    with patch("telegram_rag_bot.main.logger") as mock_logger:
        await callback(data)

        # Verify HTTP POST was called
        mock_session.post.assert_called_once()
        call_kwargs = mock_session.post.call_args[1]
        assert call_kwargs["timeout"].total == 2.0
        assert call_kwargs["headers"]["Content-Type"] == "application/json"

        # Verify payload
        payload = call_kwargs["json"]
        assert payload["tenant_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert payload["provider"] == "gigachat_primary"  # НЕ нормализовать
        assert payload["model"] == "GigaChat-Pro"
        assert payload["tokens"] == 450
        assert payload["prompt_tokens"] == 150
        assert payload["completion_tokens"] == 300
        assert payload["cost"] == 0.0135
        assert payload["latency_ms"] == 1234
        assert payload["success"] is True
        assert payload["platform_key_id"] == "987fcdeb-51a2-..."
        assert "timestamp" in payload  # Проверить наличие timestamp

        # Verify URL
        url = mock_session.post.call_args[0][0]
        assert url == "https://platform.example.com/api/v1/usage/report"

        # Verify logging
        mock_logger.info.assert_called_once()  # Structured log
        mock_logger.debug.assert_called_once()  # Success log


@pytest.mark.asyncio
async def test_create_track_usage_callback_backward_compatible():
    """Test backward compatibility: if callback_url is None → only logging."""
    from telegram_rag_bot.main import create_track_usage_callback

    # Create callback without callback_url
    callback = create_track_usage_callback(
        tenant_id="",
        callback_url=None,
        platform_key_id=None,
        http_session=None,
    )

    data: UsageData = {
        "provider_name": "gigachat",
        "model": "GigaChat-Pro",
        "total_tokens": 150,
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "cost": 0.45,
        "latency_ms": 1200,
        "success": True,
    }

    with patch("telegram_rag_bot.main.logger.info") as mock_logger:
        await callback(data)

        # Verify only logging (no HTTP POST)
        mock_logger.assert_called_once()
        assert mock_logger.call_args[0][0] == "llm_usage_tracked"


@pytest.mark.asyncio
async def test_send_usage_to_platform_retry_logic():
    """Test retry logic: 3 attempts with exponential backoff."""
    from telegram_rag_bot.main import _send_usage_to_platform

    # Mock aiohttp session
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_response = AsyncMock()
    mock_response.status = 500  # Server error → retry
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_session.post.return_value = mock_response

    data: UsageData = {
        "provider_name": "gigachat",
        "model": "GigaChat-Pro",
        "total_tokens": 150,
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "cost": 0.45,
        "latency_ms": 1200,
        "success": True,
    }

    with (
        patch("telegram_rag_bot.main.logger") as mock_logger,
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        await _send_usage_to_platform(
            data,
            tenant_id="550e8400-...",
            callback_url="https://platform.example.com",
            platform_key_id=None,
            session=mock_session,
        )

        # Verify 3 attempts were made
        assert mock_session.post.call_count == 3

        # Verify exponential backoff: sleep(0.5), sleep(1.0)
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0][0][0] == 0.5  # First backoff
        assert mock_sleep.call_args_list[1][0][0] == 1.0  # Second backoff

        # Verify warning was logged (all retries failed)
        mock_logger.warning.assert_called()
        assert "unreachable after 3 retries" in mock_logger.warning.call_args[0][0]


@pytest.mark.asyncio
async def test_send_usage_to_platform_429_no_retry():
    """Test 429 handling: NO retry, ERROR log."""
    from telegram_rag_bot.main import _send_usage_to_platform

    # Mock aiohttp session
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_response = AsyncMock()
    mock_response.status = 429  # Quota exceeded
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_session.post.return_value = mock_response

    data: UsageData = {
        "provider_name": "gigachat",
        "model": "GigaChat-Pro",
        "total_tokens": 150,
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "cost": 0.45,
        "latency_ms": 1200,
        "success": True,
    }

    with patch("telegram_rag_bot.main.logger") as mock_logger:
        await _send_usage_to_platform(
            data,
            tenant_id="550e8400-...",
            callback_url="https://platform.example.com",
            platform_key_id=None,
            session=mock_session,
        )

        # Verify only 1 attempt (NO retry)
        assert mock_session.post.call_count == 1

        # Verify ERROR log
        mock_logger.error.assert_called_once()
        assert "Quota exceeded (429)" in mock_logger.error.call_args[0][0]


@pytest.mark.asyncio
async def test_send_usage_to_platform_platform_key_id_null():
    """Test that platform_key_id=None is sent as null in JSON."""
    from telegram_rag_bot.main import _send_usage_to_platform

    # Mock aiohttp session
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_session.post.return_value = mock_response

    data: UsageData = {
        "provider_name": "gigachat",
        "model": "GigaChat-Pro",
        "total_tokens": 150,
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "cost": 0.45,
        "latency_ms": 1200,
        "success": True,
    }

    await _send_usage_to_platform(
        data,
        tenant_id="550e8400-...",
        callback_url="https://platform.example.com",
        platform_key_id=None,  # BYOK tier
        session=mock_session,
    )

    # Verify payload contains platform_key_id as None
    payload = mock_session.post.call_args[1]["json"]
    assert payload["platform_key_id"] is None


@pytest.mark.asyncio
async def test_send_usage_to_platform_empty_tenant_id():
    """Test that empty tenant_id skips HTTP POST."""
    from telegram_rag_bot.main import _send_usage_to_platform

    mock_session = AsyncMock(spec=aiohttp.ClientSession)

    data: UsageData = {
        "provider_name": "gigachat",
        "model": "GigaChat-Pro",
        "total_tokens": 150,
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "cost": 0.45,
        "latency_ms": 1200,
        "success": True,
    }

    with patch("telegram_rag_bot.main.logger.warning") as mock_warning:
        await _send_usage_to_platform(
            data,
            tenant_id="",  # Empty tenant_id
            callback_url="https://platform.example.com",
            platform_key_id=None,
            session=mock_session,
        )

        # Verify HTTP POST was NOT called
        mock_session.post.assert_not_called()

        # Verify warning was logged
        mock_warning.assert_called_once()
        assert "tenant_id is empty" in mock_warning.call_args[0][0]


@pytest.mark.asyncio
async def test_send_usage_to_platform_network_error_retry():
    """Test that network errors trigger retry."""
    from telegram_rag_bot.main import _send_usage_to_platform

    # Mock aiohttp session that raises exception
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_session.post.side_effect = aiohttp.ClientError("Connection failed")

    data: UsageData = {
        "provider_name": "gigachat",
        "model": "GigaChat-Pro",
        "total_tokens": 150,
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "cost": 0.45,
        "latency_ms": 1200,
        "success": True,
    }

    with (
        patch("telegram_rag_bot.main.logger") as mock_logger,
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        await _send_usage_to_platform(
            data,
            tenant_id="550e8400-...",
            callback_url="https://platform.example.com",
            platform_key_id=None,
            session=mock_session,
        )

        # Verify 3 attempts were made
        assert mock_session.post.call_count == 3

        # Verify backoff was used
        assert mock_sleep.call_count == 2
