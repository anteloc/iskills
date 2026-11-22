---
name: python-types
description: 'Reference for the Python SDK''s question, asset and answer types: `Choice`, `Score`, `Noul`, `Box`, `NoulCriteria`, question dictionaries and models, `Image` and `Asset` with `attach_assets`, `SystemOneResponse` (`answers`, `choices`, `scores`, `nouls`, `boxes`, `usage`, `model`), `ChoiceAnswer`, `ScoreAnswer`, `NoulAnswer`, `BoxAnswer`, `BoxCoordinates`, `Usage`, `ListModelsResponse` and response validation. Use when checking the exact fields of a Python question or answer object.'
---

# Python SDK Types

Compact reference for the question, asset and response types in `typesafe_sdk`. Usage is in [python-sdk](../../python-sdk/SKILL.md); clients and exceptions are in [python-clients](../python-clients/SKILL.md). The verbatim pages include each model's JSON schema.

## State

`state` is a `Content` value: text, an asset, a JSON object, or an array. It cannot be `None`; values inside an object may be `None`.

## Question objects (Pydantic models)

| Class | Fields | Notes |
| --- | --- | --- |
| `Noul` | `type: Literal["noul"]`, `instructions: Content \| None = None`, `criteria: NoulCriteria \| None = None` | `criteria` required when `instructions` is `None` |
| `Choice` | `type: Literal["choice"]`, `criteria: Mapping[str, Content \| None]`, `instructions: Content \| None = None` | Non-empty map of labels to descriptions (`None` = undescribed) |
| `Score` | `type: Literal["score"]`, `criteria: Sequence[Content]`, `instructions: Content \| None = None` | Non-empty ordered list, one per score from 0 (the docs recommend at least two; the API accepts up to 10) |
| `Box` | `type: Literal["box"]`, `instructions: Content \| None = None` | What to locate in the request's image |

`NoulCriteria` is a `TypedDict` with optional `true` and `false`, each `Content | None`.

Construct with keyword arguments: `Noul(instructions="...")`, `Choice(instructions="...", criteria={...})`, `Score(instructions="...", criteria=[...])`, `Box(instructions="...")`.

```python
from pathlib import Path
from typesafe_sdk import Box, BoxAnswer, Image, TypeSafeClient

def locate_dog(client: TypeSafeClient, photo: Path) -> BoxAnswer:
    result = client.system_one(
        state=Image(photo),
        questions={"dog": Box(instructions="The dog")},
        model="jev-preview",
    )
    return result.boxes["dog"]
```

## Question dictionaries (TypedDicts)

Plain dicts with a `type` key (`"noul"`, `"choice"`, `"score"`, `"box"`) work too, and can be mixed with objects in one request: `NoulModel`, `ChoiceModel`, `ScoreModel`, `BoxModel` (same fields as above; `instructions` is `NotRequired`).

| Alias | Definition |
| --- | --- |
| `Question` | `Noul \| Choice \| Score \| Box \| QuestionModel` |
| `QuestionModel` | `NoulModel \| ChoiceModel \| ScoreModel \| BoxModel` |
| `Questions` | `Mapping[str, Question]` |

## Assets

`Asset` = `Image` (only images are supported). The API detects each image's format from its bytes.

`Image(data: Buffer | PathLike[str])` is a dataclass holding raw bytes (anything supporting the buffer protocol: `bytes`, `bytearray`, `memoryview`, `mmap`, NumPy arrays; non-`bytes` buffers are copied) or a file path. An `Image` is loaded once, on first use, and reused by every request that sends the same object.

| Constructor | Notes |
| --- | --- |
| `Image(Path("photos/product.png"))` | From a file path |
| `Image(data)` | From bytes in memory, or a slice: `Image(memoryview(container)[offset : offset + length])` |
| `Image.from_base64(data: str \| Buffer)` | Whitespace (line breaks) ignored; raises `TypeSafeError` on invalid base64 |
| `Image.from_pil(image, format="jpeg")` | Needs the `pil` extra. Pillow defaults except JPEG quality 95; use `format="png"` for RGBA or P-mode images (JPEG can't store transparency or palettes). Raises `TypeSafeError` if Pillow can't encode |

```python
import mmap

def map_photo(path: Path) -> Image:
    with path.open("rb") as file:
        return Image(mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ))
```

`str(image)` is its unique reference, for use inside text with `client.attach_assets(...)`.

## SystemOneResponse

Frozen, strict Pydantic model; extra fields ignored.

| Member | Type / notes |
| --- | --- |
| `model` | `str`: the model that answered |
| `usage` | `Usage` |
| `answers` | `dict[str, Answer]`: all answers by question name |
| `nouls` | `dict[str, NoulAnswer]` (cached property) |
| `choices` | `dict[str, ChoiceAnswer]` |
| `scores` | `dict[str, ScoreAnswer]` |
| `boxes` | `dict[str, BoxAnswer]` |
| `request_id` | `x-typesafe-request-id` header |
| `raw_http_response` | The underlying `httpx2.Response` (status, headers, body), e.g. to read answer kinds the SDK doesn't know yet |

Subclass it to declare typed answer attributes (`class BillingResponse(SystemOneResponse): billing: NoulAnswer`) and pass `response_model=BillingResponse`.

## Answers

All frozen, strict, extra fields ignored.

| Class | Fields |
| --- | --- |
| `NoulAnswer` | `noul: float` (probability of yes, 0–1), `type: Literal["noul"]` |
| `ChoiceAnswer` | `choice: str` (highest-probability label), `confidence: float`, `probabilities: dict[str, float]` (sums to about 1), `type: Literal["choice"]` |
| `ScoreAnswer` | `score: float` (probability-weighted average of levels; may be fractional), `confidence: float`, `legend: dict[int, str \| dict \| list]`, `probabilities: dict[int, float]`, `type: Literal["score"]` |
| `BoxAnswer` | `box: BoxCoordinates`, `confidence: float \| None`, `type: Literal["box"]` |
| `BoxCoordinates` | `top`, `bottom`, `left`, `right`: fractions of the image's height / width, 0–1 |
| `Answer` | Union of the answer types |

Score `legend` and `probabilities` are keyed by **integer** level (the raw JSON uses string keys).

## Usage and models

| Class | Fields |
| --- | --- |
| `Usage` | `input_tokens: int \| None`, `output_tokens: int \| None` (`None` when not reported) |
| `ListModelsResponse` | `models: tuple[ModelMetadata, ...]`, plus `request_id` and `raw_http_response` |
| `ModelMetadata` | `name`, `description`, `release_date` |

## Response validation

A 2xx response whose body is missing or has structurally invalid required data raises `TypeSafeAPIResponseValidationError`, with `field_path` such as `answers.tone.confidence` (see [python-clients](../python-clients/SKILL.md)).

## Source docs

Verbatim copies, for details not covered above:

- [sdk/python/api/types/questions.md](references/sdk-python-api-types-questions.md)
- [sdk/python/api/types/assets.md](references/sdk-python-api-types-assets.md)
- [sdk/python/api/types/responses.md](references/sdk-python-api-types-responses.md)
