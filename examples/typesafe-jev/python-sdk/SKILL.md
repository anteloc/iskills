---
name: python-sdk
description: 'Using the TypeSafe Python SDK (`typesafe-sdk`, `import typesafe_sdk`): `TypeSafeClient` and `AsyncTypeSafeClient`, `system_one()`, choosing a model, attaching media assets with automatic or named references, typed responses (`response.choices`, `response.scores`, `response.nouls`, `response.answers`), custom response types, retries, error handling, environment variables, base URL, and performance tuning (client reuse, zstd, aiohttp, HTTP/2, connection limits), logging and forward compatibility. Use when writing or debugging Python code that calls Jev.'
---

# Python SDK

Call Jev from Python with `typesafe-sdk` (`import typesafe_sdk`): synchronous and asynchronous clients, typed questions and answers, images, typed response models, retries, errors, configuration, and performance tuning for high request rates. What to ask is covered in [questions](../questions/SKILL.md); exact signatures are in [python-clients](../reference/python-clients/SKILL.md) and [python-types](../reference/python-types/SKILL.md). Source: [github.com/typesafe-ai/typesafe-sdk-python](https://github.com/typesafe-ai/typesafe-sdk-python).

## Install

```sh
uv add typesafe-sdk
# or
pip install typesafe-sdk
```

Requires Python 3.10+. Extras (e.g. `typesafe-sdk[http2]`):

| Extra | For |
| --- | --- |
| `http2` | HTTP/2 support |
| `pil` | Sending Pillow images |
| `zstd` | Request body compression on Python 3.13 and earlier |

Set `TYPESAFE_API_KEY` (create one in the [console](https://console.typesafe.ai/)).

## Call the System One API

```python
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

with TypeSafeClient() as client:
    response = client.system_one(
        state={"ticket": "I was charged twice. Please fix this ASAP."},
        questions={
            "billing": Noul(instructions="Is this ticket about billing?"),
            "tone": Choice(
                instructions="What is the customer's tone?",
                criteria={"calm": None, "frustrated": None, "angry": None},
            ),
            "urgency": Score(
                instructions="How urgent is this ticket?",
                criteria=["can wait", "this week", "today"],
            ),
        },
    )

print(response.nouls["billing"].noul)
print(response.choices["tone"].choice)
print(response.scores["urgency"].score)
```

Async is the same with `AsyncTypeSafeClient`, `async with` and `await`:

```python
from typesafe_sdk import AsyncTypeSafeClient, Choice, Noul, Score


async def main() -> None:
    async with AsyncTypeSafeClient() as client:
        response = await client.system_one(
            state={"ticket": "I was charged twice. Please fix this ASAP."},
            questions={
                "billing": Noul(instructions="Is this ticket about billing?"),
                # ...
            },
        )
```

- `state` and `questions` can also be passed positionally: `client.system_one(state, questions)`.
- Questions are `Choice`, `Score`, `Noul`, `Box` objects (`NoulCriteria(true=..., false=...)` for Noul criteria) or raw dicts like `{"type": "noul", "instructions": "..."}`.
- Read answers by type with `response.choices[...]`, `response.scores[...]`, `response.nouls[...]` (and `response.boxes[...]`), or generically with `response.answers[...]`. Each answer has the fields described in [questions](../questions/SKILL.md) (`.choice`, `.probabilities`, `.confidence`, `.score`, `.legend`, `.noul`, `.box`).
- Score `probabilities` and `legend` are keyed by **integer** level in the SDK (strings in raw JSON).
- `TypeSafeClient()` without a context manager also works; call `close()` (`aclose()` for async) when done.

## Choose a model

```python
from typesafe_sdk import TypeSafeClient

print(TypeSafeClient().models.list())

client = TypeSafeClient(model="jev")
```

Also per call: `client.system_one(..., model="jev-1.14.0")`. Default: `jev-latest` (or `TYPESAFE_DEFAULT_MODEL`). Models and aliases are in the [root skill](../SKILL.md).

## Images and other assets

Only images are supported, and they are "dreamer-ready": opt in with the header, on the client or per call (`extra_headers=`):

```python
client = TypeSafeClient(headers={"TypeSafe-Danger-Zone-Images": "true"})
```

Requests with assets are sent as `multipart/form-data`. An **asset reference** in `state` or `questions` is replaced by the asset data. Two ways to create references (they can be mixed):

**Automatic: place `Image` objects directly** in state, instructions or criteria:

```python
from pathlib import Path

from typesafe_sdk import Image, Noul, SystemOneResponse, TypeSafeClient


def compare_return(
    client: TypeSafeClient, returned: Path, listing: Path, *, model: str
) -> SystemOneResponse:
    return client.system_one(
        state=["The customer returned this item:", Image(returned)],
        questions={
            "same_item": Noul(
                instructions=["Is it the item in this listing photo?", Image(listing)]
            )
        },
        model=model,
    )
```

**Automatic, in text:** attach assets to the client and format them into strings. The `with client.attach_assets(...)` block is required, or the SDK can't match text references to the data:

```python
photo = Image(returned)
with client.attach_assets(photo):
    return client.system_one(
        state=f"The customer says {photo} arrived scratched.",
        questions={"damaged": Noul(instructions="Is the item damaged?")},
        model=model,
    )
```

**Named references:** choose your own, passed through `assets`. Use distinct delimiters like `<product>` so they don't match ordinary text:

```python
return client.system_one(
    state="Inspect this returned product: <product>",
    questions={"damaged": Noul(instructions="Is the product damaged?")},
    assets={"<product>": Image(photo)},
    model=model,
)
```

`Image` accepts file paths, raw bytes, base64 strings and PIL objects (`pil` extra). Image rules and limits are in [images](../questions/images/SKILL.md).

## Typed responses

Pass `response_model=` to get attribute access with types:

```python
from typesafe_sdk import Noul, NoulAnswer, SystemOneResponse, TypeSafeClient


class BillingResponse(SystemOneResponse):
    billing: NoulAnswer


with TypeSafeClient() as client:
    result = client.system_one(
        "I was charged twice.",
        {"billing": Noul(instructions="Is this about billing?")},
        response_model=BillingResponse,
    )
    assert 0 <= result.billing.noul <= 1
    assert result.billing == result.nouls["billing"]
    print(result.request_id)
```

Or any Pydantic model of the response shape, without inheriting `SystemOneResponse`:

```python
from pydantic import BaseModel

from typesafe_sdk import Noul, NoulAnswer, TypeSafeClient


class BillingAnswers(BaseModel):
    billing: NoulAnswer


class BillingResponse(BaseModel):
    answers: BillingAnswers


result = TypeSafeClient().system_one(
    "I was charged twice.",
    {"billing": Noul(instructions="Is this about billing?")},
    response_model=BillingResponse,
)
assert 0 <= result.answers.billing.noul <= 1
```

## Retries and errors

The clients retry by default (including `429` with backoff, honoring `retry-after`). Customize with a `RetryPolicy` on the client or per call:

```python
from typesafe_sdk import RetryPolicy, TypeSafeClient

client = TypeSafeClient(retry=RetryPolicy(max_retries=3, backoff_max=0.2, timeout=1.0))

client.system_one(
    state, questions, retry=RetryPolicy(max_retries=3, backoff_max=0.2, timeout=1.0)
)
```

```python
from typesafe_sdk import TypeSafeAPIError

try:
    client.system_one(state, questions)
except TypeSafeAPIError as error:
    print(error.status, error.request_id)
```

Invalid API keys raise `TypeSafeError` at client creation, before any request. The full exception hierarchy and `RetryPolicy` fields are in [python-clients](../reference/python-clients/SKILL.md).

## Configuration

| Variable | Configures | Default |
| - | - | - |
| `TYPESAFE_API_KEY` | API key (required) | — |
| `TYPESAFE_BASE_URL` | API root URL | `https://api.typesafe.ai` |
| `TYPESAFE_DEFAULT_MODEL` | Default model | `jev-latest` |
| `TYPESAFE_LOG_LEVEL` | `typesafe_sdk` logger level, applied once at import | unset |

Keys from `api_key` or the environment have surrounding whitespace stripped; empty keys, internal whitespace, control and non-ASCII characters are rejected before sending. An explicitly empty `api_key` does not fall back to the environment.

**Other base URLs / gateways** (must follow the [TypeSafe OpenAPI spec](https://api.typesafe.ai/docs/)): set `base_url` or `TYPESAFE_BASE_URL`.

```python
import os

from typesafe_sdk import Noul, TypeSafeClient

with TypeSafeClient(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api",
    model="~typesafe/jev-latest",
) as client:
    result = client.system_one(
        "I was charged twice.",
        {"billing": Noul(instructions="Is this about billing?")},
    )
    print(result.nouls["billing"].noul)
```

| Gateway | `base_url` | `model` | Key env var in the example |
| --- | --- | --- | --- |
| OpenRouter | `https://openrouter.ai/api` | `~typesafe/jev-latest` | `OPENROUTER_API_KEY` |
| Vercel AI Gateway | `https://ai-gateway.vercel.sh/typesafe` | `typesafe-ai/jev` | `AI_GATEWAY_API_KEY` |
| Pydantic AI Gateway | `https://gateway-us.pydantic.dev/proxy/typesafe` | `jev-latest` | `PYDANTIC_AI_GATEWAY_API_KEY` |

## Performance (hundreds of requests per second)

- **Reuse clients:** a new client means new connections and TLS handshakes.
- **zstd compression:** bodies of 1 KiB or more are compressed with zstd by default. On Python < 3.14 install `typesafe-sdk[zstd]`. Configure or disable with the `compression` constructor argument.
- **aiohttp for async at high rates:**

  ```python
  from httpx_aiohttp.httpx2 import Httpx2AiohttpClient

  from typesafe_sdk import AsyncTypeSafeClient

  client = AsyncTypeSafeClient(http_client=Httpx2AiohttpClient())
  ```

  (`uv add "httpx-aiohttp[httpx2]"`)
- **One client per thread** under heavy load (a shared client's connection pool becomes the bottleneck):

  ```python
  import threading

  from typesafe_sdk import TypeSafeClient


  class ThreadClients(threading.local):
      def __init__(self) -> None:
          self.client = TypeSafeClient()


  clients = ThreadClients()
  ```

- **HTTP/1.1 (default) for high rates; HTTP/2** for low/moderate concurrency with fewer connections (e.g. behind a restrictive proxy): install `typesafe-sdk[http2]` and pass `http_client=httpx2.Client(http2=True)` (`httpx2.AsyncClient` for async).
- **Connection limits:** defaults are at most 100 connections kept alive 30 s when idle. Set limits yourself when you pass your own `http_client`, e.g. `httpx2.Limits(max_connections=200, max_keepalive_connections=200, keepalive_expiry=30)`.

## Logging

```python
import logging

logging.getLogger("typesafe_sdk").setLevel(logging.DEBUG)
```

Or set `TYPESAFE_LOG_LEVEL` (`debug`, `info`, `warning`, `error`, `off`) before import. `info` logs one line per request; `debug` adds headers and bodies. Secret headers are redacted; **request and response bodies are not**.

## Forward compatibility

- Extra request fields: `client.system_one(..., extra_body={...})` (send only fields the API supports).
- Raw question dicts can carry fields the SDK doesn't know yet.
- Unknown answer kinds are skipped with a warning; read everything via `result.raw_http_response.json()["answers"]`.
- Unknown response fields are ignored.

Prefer upgrading the SDK over relying on these escape hatches.

## Changelog highlights

- **v0.7.5 (2026-10-14):** zstd request compression on by default (non-official APIs may not support it yet); `Image` assets from bytes, paths, base64 and PIL; `Box` questions and answers; `attach_assets` for text references.
- **v0.7.4:** non-finite numbers serialized as strings.
- **v0.7.3:** async TLS concurrency fix with `truststore<=0.10.4`; more request validation; pooled connections kept alive 30 s.

Older entries are in the verbatim changelog.

## Source docs

Verbatim copies, for details not covered above:

- [sdk/python.md](references/sdk-python.md)
- [sdk/python/usage/basic.md](references/sdk-python-usage-basic.md)
- [sdk/python/usage/advanced.md](references/sdk-python-usage-advanced.md)
- [sdk/python/changelog.md](references/sdk-python-changelog.md)
