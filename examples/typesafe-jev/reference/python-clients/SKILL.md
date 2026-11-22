---
name: python-clients
description: 'Reference for the Python SDK clients and support types: `TypeSafeClient` and `AsyncTypeSafeClient` (constructor arguments, `system_one()`, `models.list()`, `close()` / `aclose()`), `RetryPolicy` (attempts, retryable statuses, backoff), the exception hierarchy (`TypeSafeError`, `TypeSafeAPIError`, `TypeSafeRateLimitError`, `TypeSafeAPIConnectionError`, `TypeSafeAPITimeoutError`, ...), constants and environment variables (`API_KEY_ENV`, `BASE_URL_ENV`, `DEFAULT_MODEL`, `DEFAULT_TIMEOUT`), and common types. Use when checking a Python client parameter, retry setting, exception or default.'
---

# Python SDK Clients

Compact reference for the `typesafe_sdk` clients, `RetryPolicy`, exceptions, constants and common types. Usage guidance is in [python-sdk](../../python-sdk/SKILL.md); question and answer types are in [python-types](../python-types/SKILL.md).

## TypeSafeClient / AsyncTypeSafeClient

```python
TypeSafeClient(
    *,
    api_key: str | None = None,
    model: str | None = None,
    retry: RetryPolicy | None = None,
    timeout: float | httpx2.Timeout | None = None,
    headers: Mapping[str, str] | None = None,
    transport: httpx2.BaseTransport | None = None,
    http_client: httpx2.Client | None = None,
    base_url: str | None = None,
    compression: Literal["zstd", False] | None = None,
)
```

`AsyncTypeSafeClient` takes the same arguments with `httpx2.AsyncBaseTransport` / `httpx2.AsyncClient`. Explicit options beat environment variables; empty or whitespace-only env values are ignored.

| Parameter | Notes |
| --- | --- |
| `api_key` | Required; falls back to `TYPESAFE_API_KEY`. Surrounding whitespace stripped; empty, internal whitespace, control or non-ASCII characters rejected. |
| `model` | Default model; falls back to `TYPESAFE_DEFAULT_MODEL`, then `jev-latest`. |
| `retry` | `RetryPolicy`; `RetryPolicy(max_retries=0)` disables retries. |
| `timeout` | Per HTTP operation; inherits `http_client.timeout` when one is supplied, else `DEFAULT_TIMEOUT` (10 s). |
| `headers` | Extra headers on every request (e.g. `{"TypeSafe-Danger-Zone-Images": "true"}`). |
| `transport` / `http_client` | Custom httpx2 transport or client; **mutually exclusive** (`ValueError`). Closed when the SDK client closes. |
| `base_url` | Falls back to `TYPESAFE_BASE_URL`, then `https://api.typesafe.ai`. |
| `compression` | `"zstd"` (default when available) or `False`. |

Raises `TypeSafeError` when the API key is missing or invalid, the timeout is invalid, or zstd is unavailable.

| Member | Notes |
| --- | --- |
| `system_one(state, questions, *, model=None, assets=None, retry=None, timeout=None, extra_headers=None, extra_body=None, response_model=None)` | Returns `SystemOneResponse`, or an instance of `response_model` (any Pydantic `BaseModel`). Async: `await client.system_one(...)`. |
| `models` | Cached property; `.list(*, retry=None, timeout=None, extra_headers=None)` → `ListModelsResponse`. Async: `AsyncModels`. |
| `attach_assets(assets: Asset \| Sequence[Asset])` | Context manager: within the block, any attached asset whose `str(asset)` appears in a request is sent. Raises `TypeSafeError` if a value isn't an asset. |
| `close()` / `aclose()` | Release network resources (including a supplied client). Both clients are context managers (`with` / `async with`). |

`system_one` parameters:

| Parameter | Notes |
| --- | --- |
| `state` | `Content`: text, an asset, a JSON object, or an array |
| `questions` | Non-empty mapping of names to question objects or raw dicts |
| `model` | Per-call override; `None` inherits the client default |
| `assets` | Assets keyed by the reference used in `state` or questions |
| `retry`, `timeout` | Per-call overrides (timeout in seconds) |
| `extra_headers` | Additional headers for this call |
| `extra_body` | Extra top-level body fields, shallow-merged **last-write-wins** over `state`, `model`, `questions`, `assets` |
| `response_model` | Pydantic type for the whole JSON response, including nested answer models |

`system_one` raises: `TypeSafeError` (invalid before sending: empty questions, unreadable asset), `TypeSafeAPIError` (unsuccessful response after retries), `TypeSafeAPIConnectionError` (can't connect or times out after retries), `TypeSafeAPIResponseValidationError` (body doesn't match the response model).

For `models.list`, `extra_headers` cannot override authentication, SDK identification or `Accept`.

## RetryPolicy

A dataclass. Pass on the client or per call.

| Field | Default | Notes |
| --- | --- | --- |
| `max_retries` | `2` | Retries after the first attempt; `0` disables. |
| `backoff_initial` | `0.5` s | Doubled each attempt up to `backoff_max`; `0` disables backoff. |
| `backoff_max` | `5.0` s | `0` disables backoff. |
| `backoff_jitter` | `0.25` | Fraction randomly subtracted from each delay. |
| `http_statuses` | `{408, 429, 500–599}` | Statuses retried. |
| `respect_retry_after` | `True` | Honor `Retry-After` and `retry-after-ms`. |
| `api_connection_error` | `True` | Retry `TypeSafeAPIConnectionError`. |
| `api_timeout_error` | `True` | Retry `TypeSafeAPITimeoutError`. |
| `exceptions` | `set()` | Extra exception types to retry. |
| `predicate` | `None` | `Callable[[BaseException], bool]`; `True` triggers a retry. |
| `timeout` | `30.0` s | **Total** retry budget per call, including the first attempt and delays; `None` disables. Stops before a retry whose delay would reach the budget and re-raises the last error. |

```python
from typesafe_sdk import RetryPolicy, TypeSafeClient

client = TypeSafeClient(
    retry=RetryPolicy(
        max_retries=3, timeout=10.0, http_statuses={429, 500, 502, 503, 504}
    )
)
```

(Contrast with the JavaScript SDK, whose `timeout` is per attempt with no total budget.)

## Exceptions

| Exception | Bases | Meaning / attributes |
| --- | --- | --- |
| `TypeSafeError` | `Exception` | Base for all SDK failures |
| `TypeSafeAPIError` | `TypeSafeError` | Unsuccessful HTTP response: `status`, `body` (JSON, text or `None`), `headers`, `endpoint` (method and URL without credentials or query), `request_id` (`x-typesafe-request-id`) |
| `TypeSafeBadRequestError` | `TypeSafeAPIError` | 400 |
| `TypeSafeAuthenticationError` | `TypeSafeAPIError` | 401 |
| `TypeSafePermissionDeniedError` | `TypeSafeAPIError` | 403 |
| `TypeSafeNotFoundError` | `TypeSafeAPIError` | 404 |
| `TypeSafeUnprocessableEntityError` | `TypeSafeAPIError` | 422 |
| `TypeSafeRateLimitError` | `TypeSafeAPIError` | 429; `retry_after_ms` (or `None`) |
| `TypeSafeInternalServerError` | `TypeSafeAPIError` | 5xx |
| `TypeSafeAPIConnectionError` | `TypeSafeError`, `ConnectionError` | Failed without an HTTP response |
| `TypeSafeAPITimeoutError` | `TypeSafeAPIConnectionError`, `TimeoutError` | Exceeded the timeout; `timeout` |
| `TypeSafeAPIResponseValidationError` | `TypeSafeAPIError` | 2xx with missing or invalid data; `field_path` (e.g. `answers.tone.confidence`) |

```python
from typesafe_sdk import TypeSafeAPIError

try:
    client.system_one(state, questions)
except TypeSafeAPIError as error:
    print(error.status, error.request_id)
```

## Constants (`typesafe_sdk.constants`)

| Name | Value |
| --- | --- |
| `API_KEY_ENV` | `"TYPESAFE_API_KEY"` |
| `BASE_URL_ENV` | `"TYPESAFE_BASE_URL"` |
| `DEFAULT_MODEL_ENV` | `"TYPESAFE_DEFAULT_MODEL"` |
| `LOG_LEVEL_ENV` | `"TYPESAFE_LOG_LEVEL"` |
| `DEFAULT_BASE_URL` | `"https://api.typesafe.ai"` |
| `DEFAULT_MODEL` | `"jev-latest"` |
| `DEFAULT_TIMEOUT` | `10.0` (seconds per HTTP operation) |

## Common types

| Alias | Definition |
| --- | --- |
| `JSONValue` | `str \| int \| float \| bool \| Sequence[JSONValue \| None] \| Mapping[str, JSONValue \| None]` |
| `JSONContent` | `str \| Mapping[str, JSONValue \| None] \| Sequence[JSONValue \| None]` |
| `ContentValue` | Like `JSONValue` but may also hold an `Asset` |
| `Content` | `str \| Mapping[str, ContentValue \| None] \| Sequence[ContentValue \| None] \| Asset` (the `state` type) |

## Source docs

Verbatim copies, for details not covered above:

- [sdk/python/api.md](references/sdk-python-api.md)
- [sdk/python/api/clients/sync.md](references/sdk-python-api-clients-sync.md)
- [sdk/python/api/clients/async.md](references/sdk-python-api-clients-async.md)
- [sdk/python/api/retries.md](references/sdk-python-api-retries.md)
- [sdk/python/api/exceptions.md](references/sdk-python-api-exceptions.md)
- [sdk/python/api/constants.md](references/sdk-python-api-constants.md)
- [sdk/python/api/types/common.md](references/sdk-python-api-types-common.md)
