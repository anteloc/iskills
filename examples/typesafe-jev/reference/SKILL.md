---
name: reference
description: 'API reference for TypeSafe: the HTTP API (request and response schemas, list models, request limits, compression and status codes), the Python SDK''s clients, types, retries, exceptions and constants, and the JavaScript SDK''s classes, interfaces, type aliases and helpers. Use when looking up an exact field, parameter, type, default, exception or status code rather than learning a task.'
---

# Reference

Lookup tables for the TypeSafe API and SDKs, for when you need an exact field, parameter, type, default, exception or status code rather than a walkthrough. Task guides are the sibling skills listed in the [root skill](../SKILL.md).

| You need | Open |
| --- | --- |
| Raw HTTP: `POST /v1/systemone` fields, question and answer JSON, assets, headers, `GET /v1/models`, request limits, compression, status codes | [http-api](http-api/SKILL.md) |
| Python `TypeSafeClient` / `AsyncTypeSafeClient` parameters, `system_one()` arguments, `RetryPolicy`, exceptions, constants | [python-clients](python-clients/SKILL.md) |
| Python `Choice`, `Score`, `Noul`, `Box`, `Image`, `SystemOneResponse` and answer classes | [python-types](python-types/SKILL.md) |
| JavaScript/TypeScript `TypeSafeClient`, config, `RetryPolicy`, error classes, interfaces, helpers, type aliases | [javascript-api](javascript-api/SKILL.md) |

The layers line up: both SDKs build the same JSON body as the HTTP API (`state`, `model`, `questions`, optional `assets`) and return the same answer fields. Naming differs by language: Python `system_one()`, `Choice(...)`, `response.choices[...]`; JavaScript `systemOne()`, `choice(...)`, `response.answers.x`.

Defaults the two SDKs share: base URL `https://api.typesafe.ai`, model `jev-latest`, environment variables `TYPESAFE_API_KEY`, `TYPESAFE_BASE_URL`, `TYPESAFE_DEFAULT_MODEL`, `TYPESAFE_LOG_LEVEL`; 2 retries on 408, 429 and 5xx with backoff from 0.5 s to 5 s; zstd compression for bodies of 1 KiB or more. One difference: Python's `RetryPolicy.timeout` is a 30 s **total** retry budget, while JavaScript's `timeout` (10 s) applies per attempt with no total budget.

## Subskills

Read the one that matches your task:

- [http-api](http-api/SKILL.md): Reference for the TypeSafe HTTP API: `POST /v1/systemone` (request fields `state`, `model`, `questions`, assets; question objects for choice, score, noul and box; answer objects and `usage`), `GET /v1/models`, request rules (size limits, compression) and errors (HTTP status codes, 429 rate limits, retry-after). Use when calling the API without an SDK, debugging raw requests, or checking a field or status code.
- [python-clients](python-clients/SKILL.md): Reference for the Python SDK clients and support types: `TypeSafeClient` and `AsyncTypeSafeClient` (constructor arguments, `system_one()`, `models.list()`, `close()` / `aclose()`), `RetryPolicy` (attempts, retryable statuses, backoff), the exception hierarchy (`TypeSafeError`, `TypeSafeAPIError`, `TypeSafeRateLimitError`, `TypeSafeAPIConnectionError`, `TypeSafeAPITimeoutError`, ...), constants and environment variables (`API_KEY_ENV`, `BASE_URL_ENV`, `DEFAULT_MODEL`, `DEFAULT_TIMEOUT`), and common types. Use when checking a Python client parameter, retry setting, exception or default.
- [python-types](python-types/SKILL.md): Reference for the Python SDK's question, asset and answer types: `Choice`, `Score`, `Noul`, `Box`, `NoulCriteria`, question dictionaries and models, `Image` and `Asset` with `attach_assets`, `SystemOneResponse` (`answers`, `choices`, `scores`, `nouls`, `boxes`, `usage`, `model`), `ChoiceAnswer`, `ScoreAnswer`, `NoulAnswer`, `BoxAnswer`, `BoxCoordinates`, `Usage`, `ListModelsResponse` and response validation. Use when checking the exact fields of a Python question or answer object.
- [javascript-api](javascript-api/SKILL.md): Reference for the JavaScript SDK's exports: `TypeSafeClient` and `TypeSafeClientConfig`, `APIPromise`, the error classes (`TypeSafeError`, `APIError`, `RateLimitError`, `AuthenticationError`, `APIConnectionError`, `APITimeoutError`, ...), question and response interfaces (`ChoiceQuestion`, `ScoreQuestion`, `NoulQuestion`, `BoxQuestion`, `SystemOneRequest`, `SystemOneResult`, `Usage`, `ModelCard`), `RetryPolicy`, `RequestOptions`, type aliases (`Asset`, `ResultFor`, `ScoreOf`, `Compression`, ...), the `choice`, `score`, `noul`, `box`, `image` and `withAssets` helpers, and the `ENV`, `LOG_LEVELS` and `VERSION` constants. Use when checking an exact JavaScript or TypeScript type, option or error class.
