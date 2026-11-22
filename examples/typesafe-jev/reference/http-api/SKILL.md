---
name: http-api
description: 'Reference for the TypeSafe HTTP API: `POST /v1/systemone` (request fields `state`, `model`, `questions`, assets; question objects for choice, score, noul and box; answer objects and `usage`), `GET /v1/models`, request rules (size limits, compression) and errors (HTTP status codes, 429 rate limits, retry-after). Use when calling the API without an SDK, debugging raw requests, or checking a field or status code.'
---

# HTTP API

Reference for calling TypeSafe without an SDK: `POST /v1/systemone`, `GET /v1/models`, request rules, compression and status codes. Base URL `https://api.typesafe.ai`; authenticate with `Authorization: Bearer <API_KEY>`. The OpenAPI spec is at [api.typesafe.ai/openapi.json](https://api.typesafe.ai/openapi.json) (version 0.2.0). The full spec as published in the docs is in the verbatim copy.

## POST /v1/systemone

Answer one or more questions about the content in `state`. Mixed question types are allowed; answers come back under the question names.

**Headers**

| Header | When |
| --- | --- |
| `Authorization: Bearer <API_KEY>` | Always |
| `Content-Type: application/json` | JSON body (or `multipart/form-data` with images) |
| `TypeSafe-Danger-Zone-Images: true` | Required for any assets or Box questions |
| `TypeSafe-Danger-Zone-Long-Context: true` | Raises both context limits to 262k tokens |
| `Content-Encoding: gzip` / `x-gzip` / `zstd` | Optional body compression (one layer) |

**Request body** (`SystemOneRequest`)

| Field | Type | Notes |
| --- | --- | --- |
| `model` | string, **required** | Model ID or alias (e.g. `jev-latest`); names from `GET /v1/models` |
| `state` | string \| object \| array, **required** | The content every question refers to |
| `questions` | object, **required**, ≥ 1 entry | Name → `Question` |
| `assets` | object, ≥ 1 entry if present | Placeholder → `Asset`. Each placeholder (a per-image UUID is recommended) is replaced wherever it appears as or inside a string in `state`, `instructions` or `criteria` |

**Questions**

| `type` | Fields | Constraints |
| --- | --- | --- |
| `noul` | `instructions?`, `criteria?: {true?, false?}` | Yes/no question or statement |
| `choice` | `instructions?`, `criteria` (**required**) | Map of option name → description (string, object, array or `null`), 1 to **255** options |
| `score` | `instructions?`, `criteria` (**required**) | Ordered array of level descriptions, up to **10** (schema minimum 1; the docs and SDKs require at least 2) |
| `box` | `instructions?` | What to locate; needs an image and the images header |

`instructions` and criteria entries accept a string, object, array or `null`.

**Asset** (`assets` values)

| Field | Notes |
| --- | --- |
| `type` | `"image"` (optional) |
| `data_base64` | Base64 image data (standard alphabet, padded, no whitespace or `data:` prefix); required unless `part` |
| `format` | `png`, `jpg` or `jpeg`; required with `data_base64` |
| `part` | Multipart file part name holding the image (wins over `data_base64`) |

**Multipart:** the first part is named `request` (`application/json`) and holds the JSON body; each image is its own uniquely named part, used by exactly one asset's `part`. Image rules and limits are in [images](../../questions/images/SKILL.md).

**Response** (`SystemOneResponse`, 200)

| Field | Notes |
| --- | --- |
| `model` | The model that answered; may be a versioned ID different from the alias you sent |
| `answers` | Name → answer, each with the `type` of its question |
| `usage` | `input_tokens` (billable), `output_tokens` |

| Answer `type` | Fields |
| --- | --- |
| `noul` | `noul`: probability of yes |
| `choice` | `choice`, `confidence`, `probabilities` (per option) |
| `score` | `score`, `confidence`, `legend` (`"0"`, `"1"`, ... → your descriptions), `probabilities` (per level, string keys) |
| `box` | `box: {top, bottom, left, right}` (fractions), `confidence` (may be `null`) |

Example:

```bash
curl https://api.typesafe.ai/v1/systemone \
  -H "Authorization: Bearer $TYPESAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "jev-latest",
    "state": "I was charged twice for my subscription this month. Please refund the extra charge.",
    "questions": {
      "billing": {"type": "noul", "instructions": "Is this message about billing?"},
      "tone": {
        "type": "choice",
        "instructions": "What is the tone of this message?",
        "criteria": {"angry": "An upset or hostile message", "calm": "A neutral or polite message", "excited": "An enthusiastic or eager message"}
      },
      "urgency": {
        "type": "score",
        "instructions": "How urgent is this message?",
        "criteria": ["Can wait", "Needs attention this week", "Needs attention today"]
      }
    }
  }'
```

```json
{
  "model": "jev-latest",
  "answers": {
    "billing": {"type": "noul", "noul": 0.98},
    "tone": {"type": "choice", "choice": "calm", "confidence": 0.7, "probabilities": {"angry": 0.15, "calm": 0.8, "excited": 0.05}},
    "urgency": {"type": "score", "score": 1.7, "confidence": 0.55, "legend": {"0": "Can wait", "1": "Needs attention this week", "2": "Needs attention today"}, "probabilities": {"0": 0.1, "1": 0.1, "2": 0.8}}
  },
  "usage": {"input_tokens": 120, "output_tokens": 12}
}
```

(These are the spec's illustrative examples, combined into one request.)

**Error bodies:** `400` returns `{"detail": string | object}` (long text shortened with `…`); `422` returns `{"detail": [ValidationError]}` where each error has `loc` (e.g. `["body", "questions", "urgency", "score", "criteria"]`), `msg`, `type` (machine-readable, e.g. `missing`), and optionally `input` and `ctx`.

## GET /v1/models

Returns `{"models": [{"name", "description", "release_date"}]}`: the names your account can send in `model`. It currently lists the aliases; versioned IDs such as `jev-1.14.0` are accepted whether listed or not.

```bash
curl https://api.typesafe.ai/v1/models \
  -H "Authorization: Bearer $TYPESAFE_API_KEY"
```

## Request rules

| Rule | Limit |
| - | - |
| Body size | At most 32 MiB (headers don't count) |
| Encoding | UTF-8 JSON, no byte order mark |
| Nesting | At most 64 levels of objects/arrays in each of `state`, `instructions`, `criteria` |
| Numbers | Finite only: `NaN`, `Infinity` and unrepresentable numbers like `1e400` are rejected. Send IDs and exact large quantities as strings |

**Compression:** `gzip` / `x-gzip` or `zstd`, one layer, zstd window at most 8 MiB. The 32 MiB limit applies to both compressed and decompressed size.

Context limits (64k per request / 32k per question by default) are in the [root skill](../../SKILL.md).

## Status codes

| Status | Meaning |
| - | - |
| `400 Bad Request` | Breaks a request rule (invalid UTF-8, too much nesting, non-finite number, malformed compressed body), image problems, or missing images header. `max_tokens_exceeded` = over the context length. |
| `401 Unauthorized` | Missing or invalid API key |
| `413 Payload Too Large` | Body over 32 MiB (or an image size limit) |
| `415 Unsupported Media Type` | Unsupported `Content-Encoding` or more than one compression layer |
| `422 Unprocessable Entity` | Validation failed (missing field, malformed question); the body names the field |
| `429 Too Many Requests` | Rate limit exceeded |
| `529 Overloaded` | TypeSafe temporarily overloaded |

On `429` and `529`, retry with exponential backoff, not immediately (the SDKs do this by default and honor `retry-after`). Rate limits are per organization, in tokens and requests per second.

## Source docs

Verbatim copies, for details not covered above:

- [api/system-one.md](references/api-system-one.md)
- [api/list-models.md](references/api-list-models.md)
- [api/errors.md](references/api-errors.md)
