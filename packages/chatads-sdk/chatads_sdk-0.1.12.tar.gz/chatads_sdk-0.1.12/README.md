# ChatAds Python SDK

A tiny, dependency-light wrapper around the ChatAds `/v1/chatads/messages` endpoint. It mirrors the response payloads returned by the FastAPI service so you can drop it into CLIs, serverless functions, or orchestration tools.

Learn more at [ChatAds](https://www.getchatads.com).

## Installation

```bash
pip install chatads-sdk
```

The package is published on [PyPI](https://pypi.org/project/chatads-sdk/). Install from source only if you're developing locally.

## Quickstart

```python
from chatads_sdk import ChatAdsClient, AsyncChatAdsClient, FunctionItemPayload

# Synchronous usage
with ChatAdsClient(
    api_key="YOUR_X_API_KEY",
    base_url="https://api.getchatads.com",
    raise_on_failure=True,
    max_retries=2,
    retry_backoff_factor=0.75,
) as client:
    payload = FunctionItemPayload(
        message="Looking for a CRM to close more deals",
        country="US",
    )
    result = client.analyze(payload)
    if result.success and result.data and result.data.Returned > 0:
        offer = result.data.Offers[0]
        print(offer.LinkText, offer.URL)
    else:
        print("No match")

# Async usage
async with AsyncChatAdsClient(
    api_key="YOUR_X_API_KEY",
    base_url="https://api.getchatads.com",
    max_retries=3,
) as async_client:
    result = await async_client.analyze_message(
        "Need data warehousing ideas",
        country="US",
    )
    print(result.raw)
```

## Request Options

The `FunctionItemPayload` supports these fields:

| Field | Type | Description |
|-------|------|-------------|
| `message` | str (required) | Message to analyze (1-5000 chars) |
| `ip` | str | IPv4/IPv6 address for country detection (max 45 characters) |
| `country` | str | Country code (e.g., 'US'). If provided, skips IP-based country detection |
| `quality` | str | Variable for playing around with keyword quality, link accuracy, and response times. 'fast' = quickest, but less likely to find a working affiliate link (~150ms), 'standard' = strong keyword quality and decent link matching (~1.4s), 'best' = strong keyword and strong matching (~2.5s). |

## Response Structure

```python
result.success              # bool - True if request succeeded
result.data.Offers          # List[Offer] - Array of affiliate offers
result.data.Requested       # int - Number of offers requested
result.data.Returned        # int - Number of offers returned
result.error                # ChatAdsError or None (code, message, details)
result.meta.request_id      # Unique request identifier
result.meta.usage           # UsageInfo with quota information
result.raw                  # Full raw JSON response

# Response data has:
result.data.Status          # "filled", "partial_fill", "no_offers_found", or "internal_error"

# Each Offer has:
offer.LinkText              # Text to use for the affiliate link
offer.URL                   # Affiliate URL (always populated)
offer.IntentLevel           # Intent level classification
offer.Category              # Detected product category (optional)
```

## Error Handling

Non-2xx responses raise `ChatAdsAPIError` with:
- `status_code` - HTTP status code
- `response.error.code` - Error code (e.g., `DAILY_QUOTA_EXCEEDED`, `RATE_LIMITED`)
- `response.error.message` - Human-readable message
- `retry_after` - Seconds to wait (for 429 responses)

Set `raise_on_failure=True` to also raise on 200 responses with `success=false`.

**Retryable status codes** (automatic with `max_retries>0`):
- `408` Request Timeout
- `429` Rate Limited
- `500`, `502`, `503`, `504` Server errors

## Notes

- Retries are opt-in. Provide `max_retries>0` to automatically retry transport errors and retryable status codes. The client honors `Retry-After` headers and falls back to exponential backoff.
- `base_url` must point to your HTTPS deployment (the client rejects plaintext URLs so API keys are never transmitted insecurely).
- The default hosted environment lives at `https://api.getchatads.com`; use your own domain if you're proxying ChatAds behind something else.
- `FunctionItemPayload` matches the server-side `FunctionItem` pydantic model. Keyword arguments passed to `ChatAdsClient.analyze_message()` accept either snake_case or camelCase keys.
- Reserved payload keys (e.g., `message`, `pageUrl`) cannot be overridden through `extra_fields`; doing so raises `ValueError` to prevent silent mutations.
- `debug=True` enables structured request/response logging, but payload contents are redacted automatically so you don't leak PII into logs.

## CLI Smoke Test

For a super-quick check, either edit the config block at the top of `run_sdk_smoke.py` or set:

```bash
export CHATADS_API_KEY="..."
export CHATADS_BASE_URL="https://api.getchatads.com"
export CHATADS_MESSAGE="Looking for ergonomic office chairs"
# Optional extras
export CHATADS_IP="1.2.3.4"
export CHATADS_COUNTRY="US"
```

Then run:

```bash
python run_sdk_smoke.py
```

It prints the raw JSON response or surfaces a `ChatAdsAPIError` with status/error fields so you can see exactly what the API returned.
