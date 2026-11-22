---
name: javascript-api
description: 'Reference for the JavaScript SDK''s exports: `TypeSafeClient` and `TypeSafeClientConfig`, `APIPromise`, the error classes (`TypeSafeError`, `APIError`, `RateLimitError`, `AuthenticationError`, `APIConnectionError`, `APITimeoutError`, ...), question and response interfaces (`ChoiceQuestion`, `ScoreQuestion`, `NoulQuestion`, `BoxQuestion`, `SystemOneRequest`, `SystemOneResult`, `Usage`, `ModelCard`), `RetryPolicy`, `RequestOptions`, type aliases (`Asset`, `ResultFor`, `ScoreOf`, `Compression`, ...), the `choice`, `score`, `noul`, `box`, `image` and `withAssets` helpers, and the `ENV`, `LOG_LEVELS` and `VERSION` constants. Use when checking an exact JavaScript or TypeScript type, option or error class.'
---

# JavaScript SDK API

Compact reference for every export of `@typesafe-ai/sdk` (`VERSION` = `"0.7.0"`). Usage and examples are in [javascript-sdk](../../javascript-sdk/SKILL.md). Each verbatim page is in `references/` (named like `sdk-javascript-api-classes-TypeSafeClient.md`).

## TypeSafeClient

`new TypeSafeClient(config?: TypeSafeClientConfig)`. Throws when the API key is missing, config is invalid, the runtime is unsupported, or the requested compression is unavailable.

| Member | Type / notes |
| --- | --- |
| `systemOne<Q>(request: SystemOneRequest<Q>, options?: RequestOptions)` | `APIPromise<SystemOneResult<Q>>`. All failures reject the promise; the call never throws. |
| `models` | `Models`: `list(options?)` → `APIPromise<ModelCard[]>` |
| `baseURL`, `compression`, `defaultHeaders`, `defaultModel`, `fetch`, `logger`, `logLevel`, `retry`, `timeout` | Read-only resolved settings |

**`TypeSafeClientConfig`** (explicit > env var > default; empty env values ignored):

| Option | Default |
| --- | --- |
| `apiKey` | `TYPESAFE_API_KEY` (required) |
| `baseURL` | `TYPESAFE_BASE_URL`, then `https://api.typesafe.ai` |
| `defaultModel` | `TYPESAFE_DEFAULT_MODEL`, then `jev-latest` |
| `compression` | `"zstd"` on Node.js 22.15+, else `false`; bodies under 1 KiB always uncompressed |
| `timeout` | `10000` ms per attempt, no total retry budget |
| `retry` | `Partial<RetryPolicy>` |
| `defaultHeaders` | `{}`; per-call headers take precedence |
| `logLevel` | `TYPESAFE_LOG_LEVEL`, then `warn`; `info` = request summaries, `debug` = + headers and bodies (credential headers redacted, bodies not) |
| `logger` | Prefixed `console` |
| `fetch` | Global `fetch` |
| `dangerouslyAllowBrowser` | `false`; `true` exposes the API key to page users |

**`RequestOptions`** (per call): `headers` (merged over defaults), `retry` (partial), `signal` (`AbortSignal`, also cancels pending retries), `timeout` (ms per attempt).

**`RetryPolicy`**:

| Field | Default |
| --- | --- |
| `maxRetries` | `2` (`0` disables) |
| `httpStatuses` | 408, 429, 500–599 |
| `apiConnectionError` / `apiTimeoutError` | `true` / `true` |
| `backoffInitialMs` / `backoffMaxMs` | `500` / `5000` (doubling) |
| `backoffJitter` | `0.25` (fraction subtracted at random) |
| `respectRetryAfter` / `maxRetryAfterMs` | `true` / `60000` (honors `Retry-After` and `retry-after-ms`) |

## Requests and results

| Type | Fields |
| --- | --- |
| `SystemOneRequest<Q>` | `state: NonNullable<EntryType>`, `questions: Q` (non-empty), `model?`, `assets?: Record<string, Image>` (names matched literally in strings; each must appear). Extra properties are forwarded. |
| `SystemOneResult<Q>` | `answers` (typed per question via `ResultFor`), `model` (versioned ID that answered), `usage` |
| `Usage` | `input_tokens`, `output_tokens`: `number \| null` |
| `ModelCard` | `name`, `description`, `release_date` |
| `APIPromise<T>` | A `Promise<T>` plus `withResponse()` → `WithResponse<T>` (`data`, `response`, `requestId`), `asResponse()` → raw `Response` (caller owns the body; don't also await the parsed result), `map(fn)` |

## Questions and answers

| Question | Fields | Answer | Fields |
| --- | --- | --- | --- |
| `ChoiceQuestion<T>` | `type: "choice"`, `instructions?`, `criteria: T` (≥ 1 label) | `ChoiceResponse<T>` | `choice: keyof T`, `probabilities`, `confidence`, `type` |
| `ScoreQuestion<T>` | `type: "score"`, `instructions?`, `criteria: T` | `ScoreResponse<T>` | `score` (may be fractional), `legend: ScoreLegend<T>`, `probabilities` (keyed by score), `confidence`, `type` |
| `NoulQuestion` | `type: "noul"`, `instructions?`, `criteria?: { true?, false? } \| null` (one required if no instructions) | `NoulResponse` | `noul` (0–1), `type` |
| `BoxQuestion` | `type: "box"`, `instructions?` | `BoxResponse` | `box: BoxCoordinates`, `confidence: number \| null`, `type` |

`BoxCoordinates`: `top`, `bottom` (fractions of height), `left`, `right` (fractions of width), 0–1. `Questions`: `{ [name: string]: Question }`. `Question` = union of the four question types. `ResultFor<T>` maps a question type to its answer type, preserving criteria keys.

## Helpers

| Export | Signature |
| --- | --- |
| `choice` | `choice<T extends ChoiceCriteria>(instructions: EntryType, criteria: T): ChoiceQuestion<T>` |
| `score` | `score<T extends ScoreCriteria>(instructions: EntryType, criteria: T): ScoreQuestion<T>`; also accepts runtime-built arrays (rejected at call time if under two entries) |
| `noul` | `noul(instructions: NonNullable<EntryType>, criteria?: { true?, false? } \| null)`; or `noul(instructions \| undefined, { true: ..., false? })` |
| `box` | `box(instructions?: EntryType = null): BoxQuestion` |
| `image` | `image(data: ArrayBuffer \| ArrayBufferView \| Blob): Image`; throws if empty or not bytes/Blob. Blob read at send time; its `type` is ignored |
| `withAssets` | Template tag → `TextWithAssets` (`text`, `assets`); `withAssets.join(values, separator = ",")` |

**`Image`**: `new Image(data)`, `Image.fromBase64(text)` (no `data:` prefix; throws on invalid base64), `data`, `type: "image"`, `toString()` / `toJSON()` return its unique reference. PNG or JPEG only (format detected from bytes).

## Errors

| Class | Extends | Meaning |
| --- | --- | --- |
| `TypeSafeError` | `Error` | Base class (also client-side validation failures) |
| `APIError` | `TypeSafeError` | Non-2xx response: `status`, `body` (parsed JSON, text or `undefined`), `headers`, `requestId` (from `x-typesafe-request-id`); `APIError.fromResponse(status, body, headers)` builds the right subclass |
| `BadRequestError` | `APIError` | 400 |
| `AuthenticationError` | `APIError` | 401 |
| `PermissionDeniedError` | `APIError` | 403 |
| `NotFoundError` | `APIError` | 404 |
| `UnprocessableEntityError` | `APIError` | 422 |
| `RateLimitError` | `APIError` | 429 |
| `InternalServerError` | `APIError` | 5xx |
| `APIConnectionError` | `TypeSafeError` | DNS, TLS, closed connection, interrupted body |
| `APITimeoutError` | `APIConnectionError` | Full response not received within the timeout |
| `APIUserAbortError` | `TypeSafeError` | Cancelled via `AbortSignal` |

## Type aliases and constants

| Name | Definition |
| --- | --- |
| `EntryType` | `string \| Asset \| TextWithAssets \| { [key]: ContentValue } \| ContentValue[] \| null` (used for state, instructions, criteria) |
| `ContentValue` | JSON-compatible values plus `Asset` and `TextWithAssets`, nested |
| `JsonValue` | Plain JSON value |
| `Asset` | `Image` |
| `ChoiceCriteria` | `{ [label: string]: EntryType }` (`null` = undescribed) |
| `ScoreCriteria` | `readonly [EntryType, EntryType, ...EntryType[]]` (≥ 2, indexed from 0) |
| `ScoreLegend<T>`, `ScoreOf<T>`, `SentContent<T>` | Legend keyed by score; score keys inferred from the rubric; content as returned (assets as strings) |
| `Description` | `EntryType` (a criterion description) |
| `Compression` | `"zstd" \| false` |
| `LogLevel` | `"debug" \| "info" \| "warn" \| "error" \| "off"`; `LOG_LEVELS` lists them |
| `Fetch` | `(input: string, init?: RequestInit) => Promise<Response>` |
| `Logger` | `debug`, `info`, `warn`, `error` `(message, ...args)`; console-compatible |
| `ENV` | `{ apiKey: "TYPESAFE_API_KEY", baseURL: "TYPESAFE_BASE_URL", defaultModel: "TYPESAFE_DEFAULT_MODEL", logLevel: "TYPESAFE_LOG_LEVEL" }`; `EnvVar` is the union of its values |

## Source docs

Verbatim copies, for details not covered above:

- [sdk/javascript/api.md](references/sdk-javascript-api.md)
- [sdk/javascript/api/classes/TypeSafeClient.md](references/sdk-javascript-api-classes-TypeSafeClient.md)
- [sdk/javascript/api/classes/APIPromise.md](references/sdk-javascript-api-classes-APIPromise.md)
- [sdk/javascript/api/classes/TypeSafeError.md](references/sdk-javascript-api-classes-TypeSafeError.md)
- [sdk/javascript/api/classes/APIError.md](references/sdk-javascript-api-classes-APIError.md)
- [sdk/javascript/api/classes/APIConnectionError.md](references/sdk-javascript-api-classes-APIConnectionError.md)
- [sdk/javascript/api/classes/APITimeoutError.md](references/sdk-javascript-api-classes-APITimeoutError.md)
- [sdk/javascript/api/classes/APIUserAbortError.md](references/sdk-javascript-api-classes-APIUserAbortError.md)
- [sdk/javascript/api/classes/AuthenticationError.md](references/sdk-javascript-api-classes-AuthenticationError.md)
- [sdk/javascript/api/classes/BadRequestError.md](references/sdk-javascript-api-classes-BadRequestError.md)
- [sdk/javascript/api/classes/InternalServerError.md](references/sdk-javascript-api-classes-InternalServerError.md)
- [sdk/javascript/api/classes/NotFoundError.md](references/sdk-javascript-api-classes-NotFoundError.md)
- [sdk/javascript/api/classes/PermissionDeniedError.md](references/sdk-javascript-api-classes-PermissionDeniedError.md)
- [sdk/javascript/api/classes/RateLimitError.md](references/sdk-javascript-api-classes-RateLimitError.md)
- [sdk/javascript/api/classes/UnprocessableEntityError.md](references/sdk-javascript-api-classes-UnprocessableEntityError.md)
- [sdk/javascript/api/classes/Image.md](references/sdk-javascript-api-classes-Image.md)
- [sdk/javascript/api/interfaces/TypeSafeClientConfig.md](references/sdk-javascript-api-interfaces-TypeSafeClientConfig.md)
- [sdk/javascript/api/interfaces/RequestOptions.md](references/sdk-javascript-api-interfaces-RequestOptions.md)
- [sdk/javascript/api/interfaces/RetryPolicy.md](references/sdk-javascript-api-interfaces-RetryPolicy.md)
- [sdk/javascript/api/interfaces/Logger.md](references/sdk-javascript-api-interfaces-Logger.md)
- [sdk/javascript/api/interfaces/Models.md](references/sdk-javascript-api-interfaces-Models.md)
- [sdk/javascript/api/interfaces/ModelCard.md](references/sdk-javascript-api-interfaces-ModelCard.md)
- [sdk/javascript/api/interfaces/SystemOneRequest.md](references/sdk-javascript-api-interfaces-SystemOneRequest.md)
- [sdk/javascript/api/interfaces/SystemOneResult.md](references/sdk-javascript-api-interfaces-SystemOneResult.md)
- [sdk/javascript/api/interfaces/Questions.md](references/sdk-javascript-api-interfaces-Questions.md)
- [sdk/javascript/api/interfaces/ChoiceQuestion.md](references/sdk-javascript-api-interfaces-ChoiceQuestion.md)
- [sdk/javascript/api/interfaces/ChoiceResponse.md](references/sdk-javascript-api-interfaces-ChoiceResponse.md)
- [sdk/javascript/api/interfaces/ScoreQuestion.md](references/sdk-javascript-api-interfaces-ScoreQuestion.md)
- [sdk/javascript/api/interfaces/ScoreResponse.md](references/sdk-javascript-api-interfaces-ScoreResponse.md)
- [sdk/javascript/api/interfaces/NoulQuestion.md](references/sdk-javascript-api-interfaces-NoulQuestion.md)
- [sdk/javascript/api/interfaces/NoulResponse.md](references/sdk-javascript-api-interfaces-NoulResponse.md)
- [sdk/javascript/api/interfaces/BoxQuestion.md](references/sdk-javascript-api-interfaces-BoxQuestion.md)
- [sdk/javascript/api/interfaces/BoxResponse.md](references/sdk-javascript-api-interfaces-BoxResponse.md)
- [sdk/javascript/api/interfaces/BoxCoordinates.md](references/sdk-javascript-api-interfaces-BoxCoordinates.md)
- [sdk/javascript/api/interfaces/TextWithAssets.md](references/sdk-javascript-api-interfaces-TextWithAssets.md)
- [sdk/javascript/api/interfaces/Usage.md](references/sdk-javascript-api-interfaces-Usage.md)
- [sdk/javascript/api/interfaces/WithResponse.md](references/sdk-javascript-api-interfaces-WithResponse.md)
- [sdk/javascript/api/type-aliases/Asset.md](references/sdk-javascript-api-type-aliases-Asset.md)
- [sdk/javascript/api/type-aliases/ChoiceCriteria.md](references/sdk-javascript-api-type-aliases-ChoiceCriteria.md)
- [sdk/javascript/api/type-aliases/Compression.md](references/sdk-javascript-api-type-aliases-Compression.md)
- [sdk/javascript/api/type-aliases/ContentValue.md](references/sdk-javascript-api-type-aliases-ContentValue.md)
- [sdk/javascript/api/type-aliases/Description.md](references/sdk-javascript-api-type-aliases-Description.md)
- [sdk/javascript/api/type-aliases/EntryType.md](references/sdk-javascript-api-type-aliases-EntryType.md)
- [sdk/javascript/api/type-aliases/EnvVar.md](references/sdk-javascript-api-type-aliases-EnvVar.md)
- [sdk/javascript/api/type-aliases/Fetch.md](references/sdk-javascript-api-type-aliases-Fetch.md)
- [sdk/javascript/api/type-aliases/JsonValue.md](references/sdk-javascript-api-type-aliases-JsonValue.md)
- [sdk/javascript/api/type-aliases/LogLevel.md](references/sdk-javascript-api-type-aliases-LogLevel.md)
- [sdk/javascript/api/type-aliases/Question.md](references/sdk-javascript-api-type-aliases-Question.md)
- [sdk/javascript/api/type-aliases/ResultFor.md](references/sdk-javascript-api-type-aliases-ResultFor.md)
- [sdk/javascript/api/type-aliases/ScoreCriteria.md](references/sdk-javascript-api-type-aliases-ScoreCriteria.md)
- [sdk/javascript/api/type-aliases/ScoreLegend.md](references/sdk-javascript-api-type-aliases-ScoreLegend.md)
- [sdk/javascript/api/type-aliases/ScoreOf.md](references/sdk-javascript-api-type-aliases-ScoreOf.md)
- [sdk/javascript/api/type-aliases/SentContent.md](references/sdk-javascript-api-type-aliases-SentContent.md)
- [sdk/javascript/api/variables/ENV.md](references/sdk-javascript-api-variables-ENV.md)
- [sdk/javascript/api/variables/LOG_LEVELS.md](references/sdk-javascript-api-variables-LOG_LEVELS.md)
- [sdk/javascript/api/variables/noul.md](references/sdk-javascript-api-variables-noul.md)
- [sdk/javascript/api/variables/score.md](references/sdk-javascript-api-variables-score.md)
- [sdk/javascript/api/variables/VERSION.md](references/sdk-javascript-api-variables-VERSION.md)
- [sdk/javascript/api/variables/withAssets.md](references/sdk-javascript-api-variables-withAssets.md)
- [sdk/javascript/api/functions/box.md](references/sdk-javascript-api-functions-box.md)
- [sdk/javascript/api/functions/choice.md](references/sdk-javascript-api-functions-choice.md)
- [sdk/javascript/api/functions/image.md](references/sdk-javascript-api-functions-image.md)
