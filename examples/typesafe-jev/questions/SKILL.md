---
name: questions
description: 'Writing System One questions (primitives) for Jev: defining a question''s ID, `type`, `instructions` and `criteria`, choosing between Choice, Score, Noul and Box, reading the typed answers, pointing questions at parts of a structured state with backtick paths like `ticket.messages[0].text`, asking many questions in one request, speculative questions, splitting complex judgments, and when one question really depends on another. Use when designing or debugging the questions sent to `system_one()` / `systemOne()`, or deciding which question type fits a judgment.'
---

# Questions (Primitives)

Write the questions you send to Jev. A question defines one judgment about the state; its answer is a typed value your code compares, thresholds, sorts or routes on. This skill covers defining a question, choosing its type, reading answers, and asking several at once. The request basics (state, client setup) are in the [root skill](../SKILL.md); each type has its own subskill.

| Type | What it answers | Returns |
| - | - | - |
| [Choice](choice/SKILL.md) | Which of these options? | `choice`, `probabilities`, `confidence` |
| [Score](score/SKILL.md) | Which level? | `score`, `legend`, `probabilities`, `confidence` |
| [Noul](noul/SKILL.md) | Is this true? | `noul` (0 to 1) |
| [Box](box/SKILL.md) | Where is it in this image? | `box` (`top`, `bottom`, `left`, `right`), `confidence` |

## One snap judgment per question

Ask for a judgment a knowledgeable person could make in a second, given the right context. "Does this message convey urgency?" is good. "Analyze this message and determine the best course of action" is not: that needs slow reasoning, so break it into small questions and compose the answers in code.

If a judgment depends on several independent factors, ask about each separately and weight them in code. Instead of "rate this startup pitch", ask about market size, technical feasibility and differentiation. When priorities change, change the weights, not a prompt.

## Define a question

Every question has:

- **ID**: the key you choose, e.g. `refund_requested`. It labels the answer in the response. **IDs are not sent to the model**: write the complete question in `instructions`, even when the ID seems self-explanatory.
- **`type`**: `choice`, `score`, `noul` or `box`.
- **`instructions`**: the question about the state, as a clear question or a statement to judge. Usually a string; it can also be an object or array that separates the question from the data it refers to (see [structured-questions](structured-questions/SKILL.md)).
- **`criteria`**: the possible answers. A map of options for Choice, an ordered list of levels for Score, an optional clarification of yes and no for Noul.

```python
from typesafe_sdk import Noul

questions = {
    "refund_requested": Noul(
        instructions="Does the customer request a refund?",
    ),
}
```

## Choose a question type

- **Choice**: one of a known set of options with no order between them (route a ticket, classify a document type, detect a language). Give the full list. A Choice **always picks one**, even when nothing fits. If the list may not cover every input, add a [companion Noul](../patterns/SKILL.md) asking whether any option fits, and act on the Choice only when it says yes. In TypeSafe's tests this beats an `other` / `none of the above` option, which competes with your real options for probability.
- **Score**: a position on a spectrum whose points you can describe (bug severity, frustration, skill level).
- **Noul**: a clean yes/no where the probability itself is the signal (contains PII, requests a refund, mentions distributed systems).
- **Box**: where something is in an image. A Box always returns a location, so pair it with a Noul asking whether the target is present.

Noul vs Score: a Noul of 0.5 means yes and no are equally likely, **not** "medium". "Is this candidate strong in Python?" is ambiguous. To measure skill, use a Score with defined levels (no experience, some familiarity, daily use, deep expertise). For a yes/no decision, define the condition clearly: "Does the resume state that the candidate has used Python at work?"

If two types fit, prefer the one your code can act on directly: a Choice between `refund`, `rebook` and `information` maps onto three code paths; a Score maps onto a threshold; a Noul maps onto an `if`.

## What comes back

| Type | Answer fields | How to read it |
| - | - | - |
| Choice | `choice`, `probabilities`, `confidence` | `choice` is the selected option; `probabilities` covers every option; `confidence` summarizes how peaked that distribution is. |
| Score | `score`, `legend`, `probabilities`, `confidence` | `score` is a position along your levels and can fall between two. `legend` repeats the levels by number. |
| Noul | `noul` | Probability of yes: near 1 strong yes, near 0 strong no, near 0.5 uncertain. No separate `confidence`. |
| Box | `box`, `confidence` | Four edges as fractions of the image's width or height, 0 to 1. |

Two properties make answers composable:

- **Constrained:** a distribution over your options or levels, never a value outside them.
- **Independent:** one question's answer is never hidden context for another, so adding or removing questions doesn't change the others' results.

How to act on `confidence` and probabilities is in [confidence](../confidence/SKILL.md).

## Point at parts of a structured state

When the state is a JSON object and a question is about one part, name that part in `instructions` with a dot-and-index path **in backticks**:

```json
{
  "ticket": {
    "subject": "Duplicate charge",
    "messages": [
      {"from": "customer", "text": "I was charged twice for order A-104. Please refund the duplicate."},
      {"from": "support", "text": "We are checking the charges."}
    ]
  },
  "order": {
    "id": "A-104",
    "charges": [
      {"amount_usd": 49, "status": "captured"},
      {"amount_usd": 49, "status": "captured"}
    ]
  },
  "refund_policy": "Duplicate charges are eligible for a refund."
}
```

```python
questions = {
    "refund_requested": {
        "type": "noul",
        "instructions": "Does `ticket.messages[0].text` request a refund?",
    },
    "policy_supports_refund": {
        "type": "noul",
        "instructions": (
            "Does `refund_policy` support the refund requested "
            "in `ticket.messages[0].text`, given `order.charges`?"
        ),
    },
}
```

(Questions can be SDK objects like `Noul(...)` or plain dictionaries with a `type`.)

## Ask multiple questions together

Send every question about the same state in **one request**, mixing types freely. They run in parallel: extra questions barely change response time and cost only their own (cheap) tokens.

```python
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

state = {
    "ticket_message": "My flight was cancelled. Can I get a refund?",
    "refund_policy": "Cancelled flights are eligible for a full refund.",
}

with TypeSafeClient() as client:
    response = client.system_one(
        state=state,
        questions={
            "refund_requested": Noul(
                instructions="Does `ticket_message` request a refund?",
            ),
            "request_type": Choice(
                instructions="What is the main request in `ticket_message`?",
                criteria={
                    "refund": "The customer wants money returned.",
                    "rebooking": "The customer wants a replacement flight.",
                    "information": "The customer is asking for information only.",
                },
            ),
            "frustration": Score(
                instructions="How frustrated does the customer appear in `ticket_message`?",
                criteria=[
                    "Calm and neutral.",
                    "Concerned but civil.",
                    "Very angry or using strong language.",
                ],
            ),
        },
    )

print(response.answers["refund_requested"].noul)
print(response.answers["request_type"].choice)
print(response.answers["frustration"].score)
```

- **Speculative questions:** also ask questions whose answers only matter for some inputs, and let code ignore the rest (if the ticket isn't a bug report, ignore severity). This is the speculative fan-out pattern ([patterns](../patterns/SKILL.md)); batching 13 questions into one call was 12.2x cheaper and 11.8x faster than 13 calls with the same answers ([evaluation-and-performance](../cookbooks/evaluation-and-performance/SKILL.md)).
- **How many:** no limit on the count. The request must fit the per-request context (state + all questions) and per-question context (state + any one question); see the [root skill](../SKILL.md). If questions don't fit, spread them across several requests with the same state.
- **Complex judgments:** split into one question per factor, weight in code (composite scoring; worked example in [score](score/SKILL.md)).

Coding agents tend to fall into one question per request. Don't: pack questions together.

## When one question depends on another

Questions in a request are independent. Make a **second request** only when your code cannot build it until it has the first answer: it needs the answer to fetch more data for the state, to decide what the state is made of, or to choose the next question's options. Otherwise ask everything together and combine in code.

Real examples of a justified second request:

- [Skill suggestion](../cookbooks/agents-and-llm-apps/SKILL.md): rank 182 skills, then fetch the full text of the top three and judge them again.
- [Structure recovery](../cookbooks/extraction/SKILL.md): decide which line breaks split a sentence, merge lines into blocks, then classify the blocks that now exist.
- [Hierarchical classification](../cookbooks/classification/SKILL.md): each Choice decides which options the next request offers.

Breaking a whole workflow into focused judgments is covered in [designing-with-jev](../designing-with-jev/SKILL.md).

## Subskills

Read the one that matches your task:

- [choice](choice/SKILL.md): The Choice question type: selecting one option from a defined set of options (`criteria` as a map of option keys to descriptions), with a probability for every option and a confidence. Covers writing options, reading `choice`, `probabilities` and `confidence`, large option sets, and what to do when no option fits. Use when routing, classifying, or picking one label, and when using `Choice(...)` in Python or `choice(...)` in JavaScript.
- [score](score/SKILL.md): The Score question type: rating the state against ordered, descriptive levels (`criteria` as a list of levels), returning a fractional `score`, a `legend`, per-level `probabilities` and `confidence`. Covers writing levels, interpreting scores between levels, normalizing, and splitting a complex judgment into several Scores combined with weights. Use when measuring severity, quality, frustration, risk or any position on a spectrum, and when using `Score(...)` in Python or `score(...)` in JavaScript.
- [noul](noul/SKILL.md): The Noul question type: a yes/no question or statement that returns `noul`, the probability that the answer is yes (0 to 1), with optional `criteria` that clarify what yes and no mean. Covers phrasing statements, thresholds, and why Noul has no separate confidence. Use when checking whether something is true of the state (PII present, refund requested, claim supported), and when using `Noul(...)` in Python or `noul(...)` in JavaScript.
- [box](box/SKILL.md): The Box question type (Jev 1.14+): locating something in an image, returning `box` with `top`, `bottom`, `left` and `right` edges as fractions of the image's height and width, plus confidence. Covers asking for a location, converting to pixels, cropping, and pairing a Box with a Noul that checks the target is present. Use when finding where an object, field or value is in a photo or scan, and when using `Box(...)` in Python or `box(...)` in JavaScript.
- [images](images/SKILL.md): Sending images to Jev: turning images on, attaching PNG and JPEG assets to a request, referencing them from the `state`, from a question's `instructions`, or from `criteria` (an image per option or level), uploading images over HTTP, and image placement. Covers the Python `Image` / assets helpers and the JavaScript `image()`, `withAssets` and `assets` helpers. Use when a request needs to evaluate photos, screenshots, scans or other images.
- [structured-questions](structured-questions/SKILL.md): Advanced question structure: passing JSON objects or arrays (not just strings) as `instructions`, Choice option descriptions, Score levels and Noul criteria, to separate the question from the data it refers to and encode domain rules and boundary cases. Use when a question needs embedded examples, rules, records or per-option detail that a single string can't hold.

## Source docs

Verbatim copies, for details not covered above:

- [primitives.md](references/primitives.md)
