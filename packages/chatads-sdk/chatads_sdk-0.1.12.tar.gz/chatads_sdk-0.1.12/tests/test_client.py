import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from chatads_sdk.client import (
    AsyncChatAdsClient,
    ChatAdsClient,
    _build_payload_from_kwargs,
    _compute_retry_delay,
)
from chatads_sdk.exceptions import ChatAdsAPIError
from chatads_sdk.models import FunctionItemPayload


def test_build_payload_from_kwargs_maps_aliases_and_extra_fields() -> None:
    payload = _build_payload_from_kwargs(
        "Try this product",
        {
            "pageUrl": "https://example.com",
            "country": "US",
            "customField": "foo",
        },
    )

    assert isinstance(payload, FunctionItemPayload)
    serialized = payload.to_payload()
    assert serialized["message"] == "Try this product"
    assert serialized["pageUrl"] == "https://example.com"
    assert serialized["country"] == "US"
    assert serialized["customField"] == "foo"


def test_analyze_message_posts_payload_and_parses_response() -> None:
    response_json = {
        "data": {
            "status": "filled",
            "offers": [
                {
                    "link_text": "gym equipment",
                    "search_term": "home gym set",
                    "confidence_score": 0.85,
                    "confidence_level": "high",
                    "url": "https://store.example.com/gym-set",
                    "resolution_source": "serper",
                    "category": "fitness",
                    "product": {
                        "title": "Gym Set",
                        "description": "Best gym set ever",
                    },
                }
            ],
            "requested": 1,
            "returned": 1,
            "extraction_source": "nlp",
        },
        "error": None,
        "meta": {
            "request_id": "req_123",
            "timestamp": "2026-01-06T12:00:00Z",
            "version": "1.0.0",
            "usage": {
                "monthly_requests": 1,
                "free_tier_limit": 100,
                "free_tier_remaining": 99,
                "is_free_tier": True,
                "daily_requests": 5,
                "daily_limit": 50,
            },
        },
    }
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        captured["body"] = json.loads(request.content.decode())
        captured["url"] = str(request.url)
        return httpx.Response(200, json=response_json)

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = ChatAdsClient(
        api_key="test-key",
        base_url="https://chatads.example.com",
        http_client=http_client,
    )
    try:
        response = client.analyze_message(
            "Buy now",
            country="US",
        )
    finally:
        http_client.close()

    assert captured["url"] == "https://chatads.example.com/v1/chatads/messages"
    assert captured["headers"]["x-api-key"] == "test-key"
    assert captured["body"]["message"] == "Buy now"
    assert captured["body"]["country"] == "US"

    assert response.success is True
    assert response.data is not None
    assert response.data.returned == 1
    assert len(response.data.offers) == 1
    offer = response.data.offers[0]
    assert offer.confidence_score == 0.85
    assert offer.confidence_level == "high"
    assert offer.product is not None and offer.product.title == "Gym Set"
    assert response.meta.request_id == "req_123"
    assert response.meta.version == "1.0.0"


def test_analyze_message_raises_api_error_when_error_present_and_raise_on_failure() -> None:
    response_json = {
        "data": None,
        "error": {
            "code": "RATE_LIMIT",
            "message": "Too many requests",
        },
        "meta": {"request_id": "req_999"},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=response_json)

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = ChatAdsClient(
        api_key="test-key",
        base_url="https://chatads.example.com",
        http_client=http_client,
        raise_on_failure=True,
    )
    try:
        with pytest.raises(ChatAdsAPIError) as excinfo:
            client.analyze_message("uh oh")
    finally:
        http_client.close()

    error = excinfo.value
    assert error.status_code == 200
    assert error.request_body["message"] == "uh oh"
    assert error.response is not None and error.response.error is not None
    assert error.response.error.code == "RATE_LIMIT"


def test_compute_retry_delay_prefers_retry_after_header() -> None:
    assert _compute_retry_delay(2, 0.1, "120") == 120.0

    retry_at = (datetime.now(timezone.utc) + timedelta(seconds=5)).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )
    delay = _compute_retry_delay(0, 0.1, retry_at)
    assert delay == pytest.approx(5, rel=0.2)


def test_client_retries_on_retryable_status() -> None:
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(
                500,
                json={
                    "data": None,
                    "error": {"code": "SERVER_ERROR", "message": "try later"},
                    "meta": {"request_id": "first"},
                },
            )
        return httpx.Response(
            200,
            json={
                "data": {"status": "no_offers_found", "offers": [], "requested": 1, "returned": 0},
                "error": None,
                "meta": {"request_id": "second"},
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = ChatAdsClient(
        api_key="test-key",
        base_url="https://chatads.example.com",
        http_client=http_client,
        max_retries=1,
        retry_backoff_factor=0.0,
    )
    try:
        response = client.analyze_message("retry me")
    finally:
        http_client.close()

    assert calls["count"] == 2
    assert response.meta.request_id == "second"


@pytest.mark.asyncio
async def test_async_analyze_message_posts_payload() -> None:
    response_json = {
        "data": {"status": "no_offers_found", "offers": [], "requested": 1, "returned": 0},
        "error": None,
        "meta": {"request_id": "async_req"},
    }
    captured = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(200, json=response_json)

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = AsyncChatAdsClient(
        api_key="async-key",
        base_url="https://chatads.example.com",
        http_client=http_client,
    )
    try:
        response = await client.analyze_message("hello async", country="US")
    finally:
        await http_client.aclose()

    assert captured["headers"]["x-api-key"] == "async-key"
    assert captured["body"]["country"] == "US"
    assert response.meta.request_id == "async_req"


@pytest.mark.asyncio
async def test_async_analyze_message_respects_raise_on_failure() -> None:
    response_json = {
        "data": None,
        "error": {"code": "BAD_INPUT", "message": "nope"},
        "meta": {"request_id": "async_fail"},
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=response_json)

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = AsyncChatAdsClient(
        api_key="async-key",
        base_url="https://chatads.example.com",
        http_client=http_client,
        raise_on_failure=True,
    )
    try:
        with pytest.raises(ChatAdsAPIError) as excinfo:
            await client.analyze_message("bad async call")
    finally:
        await http_client.aclose()

    assert excinfo.value.status_code == 200
    assert excinfo.value.response is not None
    assert excinfo.value.response.error is not None
    assert excinfo.value.response.error.code == "BAD_INPUT"
