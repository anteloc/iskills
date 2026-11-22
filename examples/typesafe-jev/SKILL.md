---
name: typesafe-jev
description: 'TypeSafe''s System One API and its model Jev: send a `state` (text, JSON or images) plus typed questions, get structured answers (choice, score, yes/no probability, image box) with calibrated probabilities and confidence instead of generated text. Covers what Jev is and isn''t (not a chat or coding LLM), `POST https://api.typesafe.ai/v1/systemone`, `TYPESAFE_API_KEY`, the Python SDK (`pip install typesafe-sdk`, `TypeSafeClient`, `client.system_one(state=..., questions=...)`) and JS/TS SDK (`@typesafe-ai/sdk`, `client.systemOne(...)`), models and aliases (`jev-latest`, `jev-1.14.0`), pricing and context limits. Use when a task mentions TypeSafe, Jev, System One, `typesafe_sdk` or `@typesafe-ai/sdk`, or needs AI judgments code can branch on (classification, routing, scoring, guardrails, verification, extraction, ranking), and as the entry point to the subskills.'
---

# TypeSafe Jev (System One API)

Jev is TypeSafe's flagship model and the first **System One** model. You send it a **state** (the content to judge) and a set of typed **questions**. It returns structured answers your code can use directly: a selected option, a score on your rubric, a yes-probability, or a box in an image, each with a probability distribution and (for some types) a confidence. There is no generated text to parse. This skill covers the mental model, a first request in Python, JavaScript/TypeScript and HTTP, and the models. Open a subskill for the task itself.

## Mental model

- **Jev makes judgments, not text.** It does not write replies, produce code, explain its reasoning, or hold a conversation. It is **not** a replacement for the LLM behind a coding agent, and no `model: "jev-latest"` setting turns a coding agent into a Jev agent. Use it *inside* the software you build, wherever code needs a fast structured decision.
- **One request = one state + many questions.** Every question sees the same state and is evaluated in parallel and in isolation. Adding questions barely changes response time and causes no context rot. Ask everything you might need in one request.
- **Answers are constrained to your options.** The model returns a distribution over the options or levels you supplied, never a value outside them.
- **Probabilities are calibrated.** Jev is trained so its probabilities reflect uncertainty across groups of predictions (not a guarantee for any single answer). Use them, and confidence, to decide when to act and when to escalate.
- **Atomic questions, composed in code.** Ask for one snap judgment per question: something a knowledgeable person could decide in a few seconds. If a judgment needs extended reasoning or weighs several factors, split it into several questions and combine the answers with your own logic and weights.
- **Jev is not fine-tuned per customer.** The same weights serve every account. Shape answers through the state (your content and reference material), the instructions and criteria (your rules), and decomposition.

## The four question types

| Type | Goal | Returns |
| - | - | - |
| Choice | Choose an option from a list | `choice`, `probabilities`, `confidence` |
| Score | Score the state on a rubric | `score`, `legend`, `probabilities`, `confidence` |
| Noul | Is this statement true? | `noul` (0–1) |
| Box | Where is it in this image? | `box` (`top`, `bottom`, `left`, `right`), `confidence` |

How to write each one is in [questions](questions/SKILL.md).

## State

The state is the content Jev evaluates: a message, a passage, a record, application state, or images.

| Format | Useful for | Example |
| - | - | - |
| String | A message, article, or passage | `"My card was charged twice."` |
| Object | Named fields, related records, or application state | `{"message": "My card was charged twice.", "order_id": "A-104"}` |
| Array | A sequence of messages or records | `["Hi", "My customer number is TS1337.", "My card was charged twice."]` |

- Prefer an **object** so each part has a descriptive name; questions can then point at parts by path (e.g. `` `ticket.messages[0].text` ``).
- Put related information in one state when the decision compares those parts (a conversation, an order and a refund policy).
- Keep content and supporting facts in the state; put the judgments in the questions.
- PNG and JPEG images can go in the state (see [images](questions/images/SKILL.md)). Audio and video are not supported natively.

## First request

Get an API key from the [TypeSafe console](https://console.typesafe.ai/keys) and store it in `TYPESAFE_API_KEY`; the SDKs read it automatically.

### Python

Requires Python 3.10+. Install with `pip install typesafe-sdk` or `uv add typesafe-sdk`.

```python
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

ticket = "Our API integration started returning 500 errors on every request about 20 minutes ago, and we can't process any customer orders until this is fixed."

with TypeSafeClient(model="jev-latest") as client:  # Reads TYPESAFE_API_KEY.
    response = client.system_one(
        state=ticket,
        questions={
            "department": Choice(
                instructions="Which team should handle this",
                criteria={
                    "billing": "Payment or subscription issues",
                    "technical": "Bugs or integration problems",
                    "sales": "Pricing or account questions",
                },
            ),
            "frustration": Score(
                instructions="How frustrated the customer appears",
                criteria=[
                    "Calm, just stating facts",
                    "Frustrated but civil",
                    "Very angry, strong language",
                ],
            ),
            "is_urgent": Noul(
                instructions="The message conveys urgency or time-sensitivity",
            ),
        },
    )

print(response.choices["department"].choice)
print(response.scores["frustration"].score)
print(response.nouls["is_urgent"].noul)
```

More in [python-sdk](python-sdk/SKILL.md).

### JavaScript / TypeScript

`npm install @typesafe-ai/sdk` and `npm pkg set type=module`. The SDK (v0.7.0+) requires Node.js 22 or newer (the quick start page still says 20); 22.18+ runs TypeScript files directly.

```javascript
import { choice, noul, score, TypeSafeClient } from "@typesafe-ai/sdk";

const ticket = "Our API integration started returning 500 errors on every request about 20 minutes ago, and we can't process any customer orders until this is fixed.";

const client = new TypeSafeClient({ defaultModel: "jev-latest" }); // Reads TYPESAFE_API_KEY.
const response = await client.systemOne({
  state: ticket,
  questions: {
    department: choice("Which team should handle this", {
      billing: "Payment or subscription issues",
      technical: "Bugs or integration problems",
      sales: "Pricing or account questions",
    }),
    frustration: score("How frustrated the customer appears", [
      "Calm, just stating facts",
      "Frustrated but civil",
      "Very angry, strong language",
    ]),
    is_urgent: noul("The message conveys urgency or time-sensitivity"),
  },
});

console.log(response.answers.department.choice);
console.log(response.answers.frustration.score);
console.log(response.answers.is_urgent.noul);
```

In TypeScript the SDK infers answer types from the questions: `response.answers.department.choice` has type `"billing" | "technical" | "sales"`. More in [javascript-sdk](javascript-sdk/SKILL.md).

### HTTP

```bash
curl --fail-with-body --silent --show-error \
  https://api.typesafe.ai/v1/systemone \
  -H "Authorization: Bearer $TYPESAFE_API_KEY" \
  -H "Content-Type: application/json" \
  --data-binary @- <<'JSON'
{
  "state": "Our API integration started returning 500 errors on every request about 20 minutes ago, and we can't process any customer orders until this is fixed.",
  "model": "jev-latest",
  "questions": {
    "department": {
      "type": "choice",
      "instructions": "Which team should handle this",
      "criteria": {
        "billing": "Payment or subscription issues",
        "technical": "Bugs or integration problems",
        "sales": "Pricing or account questions"
      }
    },
    "frustration": {
      "type": "score",
      "instructions": "How frustrated the customer appears",
      "criteria": ["Calm, just stating facts", "Frustrated but civil", "Very angry, strong language"]
    },
    "is_urgent": {
      "type": "noul",
      "instructions": "The message conveys urgency or time-sensitivity"
    }
  }
}
JSON
```

Response (answers come back under the IDs you chose):

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "department": {
      "type": "choice",
      "choice": "technical",
      "confidence": 1.0,
      "probabilities": {"technical": 1.0, "billing": 0.0, "sales": 0.0}
    },
    "frustration": {
      "type": "score",
      "score": 0.67,
      "confidence": 0.5,
      "legend": {"0": "Calm, just stating facts", "1": "Frustrated but civil", "2": "Very angry, strong language"},
      "probabilities": {"0": 0.33, "1": 0.67, "2": 0.0}
    },
    "is_urgent": {"type": "noul", "noul": 0.99}
  },
  "usage": {"input_tokens": 428, "output_tokens": 73}
}
```

`score` is a position on the 0–2 rubric (it can fall between levels); `noul` is the probability of yes. Values can change between Jev releases. Every field is in [http-api](reference/http-api/SKILL.md).

To try questions without code, use the [Playground](https://console.typesafe.ai/playground).

## Models

All models use `POST /v1/systemone`; the request's `model` field picks one.

| | Jev 1.14 | Jev 1.13 |
| :- | :- | :- |
| Model ID | `jev-1.14.0` | `jev-1.13.0` |
| Price (per Btok / per Mtok) | $42 / $0.042 | $42 / $0.042 |
| Context length | 64k per-request / 32k per-question | 64k per-request / 32k per-question |
| Input | Text, images | Text, images |
| Question types | Choice, Score, Noul, Box | Choice, Score, Noul |

- **Price:** input tokens only; output tokens are free.
- **Context:** *per-request* = state plus all questions; *per-question* = state plus any one question. No limit on the number of questions beyond that.
- **Long context:** send the header `TypeSafe-Danger-Zone-Long-Context: true` to raise both limits to 262k tokens (same price per token, but slower and less accurate; use only when needed).
- **Rate limits** are per organization, in tokens and requests per second, shown in the [console](https://console.typesafe.ai/rate-limits). Over a limit returns `429`; the SDKs retry with backoff and honor `retry-after`.
- **Data:** Jev is not trained on customer requests or responses.

| Alias | Points to | Meaning |
| :- | :- | :- |
| `jev-latest` | `jev-1.14.0` | Most recent stable release. The SDK default. |
| `jev-preview` | `jev-1.14.0` | Most recent release, official or not (currently the same as `jev-latest`). |

An alias moves when a new release ships, so answers can change without code changes. Each response's `model` field gives the versioned ID that answered: log it. If you tuned thresholds against one version, pin that version's ID.

`GET /v1/models` lists the names your account can use (`client.models.list()` in both SDKs).

Release notes: Jev 1.14 (October 14, 2026) added better multilingual support, the Box type, images in `state`, `instructions` or `criteria` (also on 1.13), and long context (also on 1.13).

## Which subskill

| Task | Subskill |
| --- | --- |
| Write questions; pick Choice vs Score vs Noul vs Box; ask many at once | [questions](questions/SKILL.md) |
| Decide when to trust an answer; thresholds; human review or escalation | [confidence](confidence/SKILL.md) |
| Structure requests: fan-out, screening, companion Noul, composite scores | [patterns](patterns/SKILL.md) |
| Decide whether and where Jev fits; design a workflow; known weaknesses | [designing-with-jev](designing-with-jev/SKILL.md) |
| Python code | [python-sdk](python-sdk/SKILL.md) |
| JavaScript / TypeScript code | [javascript-sdk](javascript-sdk/SKILL.md) |
| A worked example for a task (guardrails, classification, ranking, extraction, vision, agents) | [cookbooks](cookbooks/SKILL.md) |
| Exact fields, types, exceptions, status codes | [reference](reference/SKILL.md) |

TypeSafe also publishes its own agent skill: `npx skills add typesafe-ai/skills --skill typesafe-ai`, or in Claude Code `claude plugin marketplace add typesafe-ai/skills` then `claude plugin install typesafe@typesafe-ai`.

## Subskills

Read the one that matches your task:

- [questions](questions/SKILL.md): Writing System One questions (primitives) for Jev: defining a question's ID, `type`, `instructions` and `criteria`, choosing between Choice, Score, Noul and Box, reading the typed answers, pointing questions at parts of a structured state with backtick paths like `ticket.messages[0].text`, asking many questions in one request, speculative questions, splitting complex judgments, and when one question really depends on another. Use when designing or debugging the questions sent to `system_one()` / `systemOne()`, or deciding which question type fits a judgment.
- [confidence](confidence/SKILL.md): Using Jev's confidence and probabilities to decide what code does: how confidence is derived from the probability distribution (and differs from it), "I don't know" as a signal, acting automatically vs escalating to a person or a reasoning model, thresholds that scale with risk, routing by confidence as a second axis, and routing by probability with stricter thresholds for riskier actions. Use when setting thresholds, deciding when to trust an answer, or building human-review or escalation paths.
- [patterns](patterns/SKILL.md): Architectural patterns for building with Jev: speculative fan-out (many questions, including speculative ones, in one request), screening with a Noul before an expensive step, a companion Noul that tells whether any Choice option fits, and composite scoring (atomic Scores combined with weights in code). Use when structuring requests for cost, latency and reliability, or when a single question isn't enough.
- [designing-with-jev](designing-with-jev/SKILL.md): How to design software around a System One model: keeping code in control and giving Jev narrow, structured decisions, breaking a workflow into focused judgments, using structure in the state and questions, the use case map (which business workflows fit), why Jev is trained for calibrated decisions (RLCD) rather than generated text, and Jev's known weaknesses (model jaggedness, long states, edge cases). Use when deciding whether and where Jev fits, planning a new feature or workflow, or diagnosing surprising answers.
- [python-sdk](python-sdk/SKILL.md): Using the TypeSafe Python SDK (`typesafe-sdk`, `import typesafe_sdk`): `TypeSafeClient` and `AsyncTypeSafeClient`, `system_one()`, choosing a model, attaching media assets with automatic or named references, typed responses (`response.choices`, `response.scores`, `response.nouls`, `response.answers`), custom response types, retries, error handling, environment variables, base URL, and performance tuning (client reuse, zstd, aiohttp, HTTP/2, connection limits), logging and forward compatibility. Use when writing or debugging Python code that calls Jev.
- [javascript-sdk](javascript-sdk/SKILL.md): Using the TypeSafe JavaScript/TypeScript SDK (`@typesafe-ai/sdk`): `new TypeSafeClient()`, `client.systemOne({ state, questions })`, the `choice()`, `score()`, `noul()`, `box()` and `image()` helpers, `withAssets` and `assets` for images, type inference of answers from questions, request compression, and the changelog. Use when writing or debugging Node.js, browser or TypeScript code that calls Jev.
- [cookbooks](cookbooks/SKILL.md): End-to-end recipes that apply Jev to real problems, from a few questions to full pipelines, grouped by task: LLM guardrails and verification, classification, search and ranking, extraction, vision and documents, agents and LLM apps, evaluation and performance, and demo apps. Use when looking for a worked example or a proven architecture for a task before building one.
- [reference](reference/SKILL.md): API reference for TypeSafe: the HTTP API (request and response schemas, list models, request limits, compression and status codes), the Python SDK's clients, types, retries, exceptions and constants, and the JavaScript SDK's classes, interfaces, type aliases and helpers. Use when looking up an exact field, parameter, type, default, exception or status code rather than learning a task.

## Source docs

Verbatim copies, for details not covered above:

- [introduction.md](references/introduction.md)
- [introduction/quickstart.md](references/introduction-quickstart.md)
- [concepts/system-one.md](references/concepts-system-one.md)
- [concepts/state.md](references/concepts-state.md)
- [introduction/coding-agents.md](references/introduction-coding-agents.md)
- [models.md](references/models.md)
- [changelog.md](references/changelog.md)
- [sdk.md](references/sdk.md)
