---
name: designing-with-jev
description: 'How to design software around a System One model: keeping code in control and giving Jev narrow, structured decisions, breaking a workflow into focused judgments, using structure in the state and questions, the use case map (which business workflows fit), why Jev is trained for calibrated decisions (RLCD) rather than generated text, and Jev''s known weaknesses (model jaggedness, long states, edge cases). Use when deciding whether and where Jev fits, planning a new feature or workflow, or diagnosing surprising answers.'
---

# Designing with Jev

Decide whether and where Jev belongs in a system, and design the workflow around it: keep code in control, give Jev narrow typed judgments, compose the answers in code, and route on uncertainty. Also covers which use cases fit, why Jev returns calibrated probabilities (RLCD), and its known weaknesses. The request basics are in the [root skill](../SKILL.md).

## The architecture: AI-powered software, not agents

| Architecture | Shape |
| --- | --- |
| Traditional software | A decision tree of simple, reliable primitives. |
| LLM agents | The model reads instructions and chooses its next step; each loop is another chance to go off the rails. |
| **AI-powered software** (TypeSafe's target) | Code owns the control flow and deterministic work; the model appears only where you need programmable common sense over unstructured data, each task atomic and constrained. |

Jev does not generate code or choose its own next action. Summary of the method:

- Keep control flow, deterministic rules and side effects in code.
- Break broad judgments into narrow, typed questions with explicit instructions and criteria.
- Give each question only the context it needs.
- Use probabilities and confidence to act, ask for review, or escalate.
- Ask independent questions together, then compose the answers in code.

What makes the answers composable: **structured** (always one of your options, never prose to parse), **parallel** (questions are independent), **comparable** (sortable, thresholdable), **fast** (most calls about 100 ms), **calibrated** (probabilities reflect uncertainty), **self-consistent** (stable across repeated evaluations).

## Design a workflow in eight steps

1. **Use code when you can.** Deterministic work is reliable and cheap; avoid agent `while` loops when a workflow can express the behavior.

   ```python
   days_overdue = (today - invoice.due_date).days

   if days_overdue > 30:
       route_to_collections(invoice)
   ```

2. **Decompose the state.** Send only what the current questions need, to avoid distraction and context rot. Prefer your own knowledge base over facts in model weights.
3. **Structure the state.** Nested JSON; point questions at values with backticked paths such as `` `support.tickets[0].message` ``.
4. **Decompose the questions** (the most important step). Ask the most explicit, narrow, atomic questions you can. Broad questions hide several judgments behind one answer; atomic ones expose them so you can inspect, tune and combine them.
5. **Structure the questions** when needed: put the question in one field and its guiding data (context, examples, code-sourced records) in others. See [structured-questions](../questions/structured-questions/SKILL.md).
6. **Ask a lot of questions** about the same state in one request (parallel, so no extra round trips). See [patterns](../patterns/SKILL.md).
7. **Combine outputs in code**, with rules or weighted sums, or use the probabilities as features for a classical ML model:

   ```python
   answers = response.answers

   # Combine independent signals into one application-specific score.
   quality = (
       0.4 * answers["answers_request"].noul
       + 0.4 * answers["citations_are_supported"].noul
       + 0.2 * (1 - answers["contradicts_context"].noul)
   )
   ```

   No labels for a downstream model? Generate them with an ensemble of expensive reasoning models (the autoresearch cookbook in [evaluation-and-performance](../cookbooks/evaluation-and-performance/SKILL.md)).
8. **Route on uncertainty.** Escalate unsure answers to a person or a reasoning model. Test thresholds by plotting confidence against accuracy on your data. See [confidence](../confidence/SKILL.md).

   ```python
   answer = response.answers["card_help_topic"]

   if answer.confidence < 0.8:
       route_to_human_review(ticket)
   else:
       route_to_handler(answer.choice, ticket)
   ```

## Putting it together (abridged)

A support-ticket triage that applies every step. The full version (with structured criteria for every question) is in the verbatim source.

```python
from typesafe_sdk import Choice, Noul, NoulCriteria, Score, TypeSafeClient


def triage_ticket(ticket, customer):
    # Handle deterministic states without calling a model.
    if ticket["status"] == "closed":
        return "no_action"

    open_orders = [
        order for order in customer["orders"] if order["status"] != "delivered"
    ]

    # Include only the structured context needed by the questions below.
    state = {
        "ticket": {
            "message": ticket["message"],
            "sender": ticket["sender"],
            "links": ticket["links"],
        },
        "customer": {
            "plan": customer["plan"],
            "open_orders": open_orders,
        },
        "policy": {
            "sensitive_credentials": ["password", "security code", "API key"],
        },
    }

    # Ask structured, atomic questions together so they run in parallel:
    # topic (Choice), requests_credentials, sender_identity_mismatch,
    # unexpected_reward, refund_requested, mentions_open_order (Nouls),
    # frustration (Score).
    questions = {...}

    with TypeSafeClient() as client:
        response = client.system_one(
            state=state,
            questions=questions,
        )

    # Compose independent spam signals with weights controlled by code.
    answers = response.answers
    spam_risk = (
        0.45 * answers["requests_credentials"].noul
        + 0.30 * answers["sender_identity_mismatch"].noul
        + 0.25 * answers["unexpected_reward"].noul
    )

    # Escalate uncertain judgments instead of guessing.
    spam_is_uncertain = 0.4 < spam_risk < 0.6
    if spam_is_uncertain or answers["topic"].confidence < 0.75:
        return route_to_human_review(ticket)
    if spam_risk >= 0.6:
        return quarantine_as_spam(ticket)

    # Let code decide which speculative answers matter on this path.
    if answers["topic"].choice == "billing":
        return route_to_billing(
            ticket,
            refund_requested=answers["refund_requested"].noul >= 0.7,
        )
    if answers["topic"].choice == "orders":
        return route_to_orders(
            ticket,
            mentions_open_order=answers["mentions_open_order"].noul >= 0.7,
        )

    priority = (
        "high"
        if answers["frustration"].confidence >= 0.7
        and answers["frustration"].score >= 1.5
        else "normal"
    )
    return route_to_account_support(ticket, priority=priority)
```

Note the spam decision: instead of asking "is this spam?", it asks about the **signs** (requests a credential, sender name conflicts with domain, unexpected reward) and weights them in code.

## Does Jev fit? Signs and use cases

Signs you need Jev in a code workflow:

- You ask an LLM for JSON, then parse, validate and retry it.
- You have too much data for a frontier LLM at a practical cost.
- Your LLM workflow gives different answers to the same input.
- Your LLM workflow is too slow (in TypeSafe's security-incidents evaluation, 0.3 s per case vs 3.4–66 s for frontier models).
- Someone reads each item to decide what happens to it, based on details an informed person notices at a glance.
- Mistakes are costly, so uncertain cases must reach a person.

Use case categories (each has worked examples in [cookbooks](../cookbooks/SKILL.md)):

| Category | Examples |
| --- | --- |
| Business process automation | Invoice payment decisions, OCR value checks, value and date extraction, structure recovery, SEC filing classification, regulation briefings, security alert triage, claims triage, KYC, risk indicators |
| Real-time apps (about 150 ms) | Presenter-note tracking, cafe orders to carts, smart home control, Twitch chat filtering, voice agents (end-of-turn, call routing, split sensitive values) |
| Search and labeling at scale (about 100x cheaper than a frontier LLM) | Line-by-line search, legal re-ranking, finding one film among 5,000, Airbnb search in Sheets, hierarchical classification, entity alignment, feature discovery |
| Agents and verification | LLM guardrails, citation checks, answer-vs-source checks, agent-run review, RAG passage classification, cheap-model cascades, skill suggestion, support next actions, memory, function calling, tool-call and data-leak checks, model routing, semantic linting |
| Images and video | Scanned records, feeder-camera logs |

Decision shapes: classification (Choice), detection (Noul), scoring (Score), routing (Choice → code path), search, retrieval, ranking, verification, ML feature extraction, structured extraction.

**Designing your own:** start from the action your system takes, list the judgments it depends on, turn each into a question, and keep the rules that combine them in code.

Worked idea (invoice fraud in an accounts-payable inbox): don't ask "is this fraud?". Ask whether the email needs action, whether the sender's address belongs to the named vendor, whether it asks to change bank details, whether it pressures the reader, which open invoice it's about (Choice), and whether it refers to any open invoice (companion Noul). Code checks the fraud rule first (bank-detail change plus wrong sender or pressure → hold payments and alert finance), then needs-action, then the invoice match; any uncertain answer that a rule depends on goes to finance. Require stronger evidence before irreversible actions such as archiving.

## Why calibrated probabilities (RLCD)

TypeSafe's bet is that automation will be mostly machine-to-machine, so the machine interface matters more than chat. Pretrained models were adapted by **RLHF** (chatbots: responses people prefer) and **RLVR** (reasoning models: strong but slow and expensive). Jev is trained with **RLCD**, reinforcement learning for calibrated decisions: no text, just decisions and probabilities, where higher probability should mean a greater chance of being correct.

Across many predictions from a well-calibrated model, outcomes given 0.2 happen about 20% of the time and outcomes given 0.8 about 80%. This describes groups of predictions, not any single answer. RLHF, by contrast, can reward sycophancy and confident-sounding hallucinations and narrows output distributions (mode dropping).

## Known weaknesses (model jaggedness)

Jev is best at System One tasks: fast, common-sense judgments. It can be literal, struggles with indirection, and is weak at numeric precision.

| Failure mode | Do this instead |
| - | - |
| **Literal reading**: answers the question you wrote, not the one you meant | State the exact condition; put boundary cases in criteria. When you find yourself explaining what you meant, that's the missing half of the instruction. |
| **Math and numbers**, including **counting** | Do arithmetic in code. To count matches, ask one Noul per item and sum in code. |
| **Numeric representations** (hex colors, RGB, binary) | Convert in code to a number or named bucket; keep the judgment for Jev. |
| **Interpolating Score magnitudes** | Use a score to check a threshold, not to reconstruct an exact number between levels. |
| **Date and time comparison** | Extract day/month/year with Choices (with a "not stated" option); order and diff dates in code. See [extraction](../cookbooks/extraction/SKILL.md). |
| **Indirection** (double negatives, multi-hop) | Write directly; name the relevant part of the state. |
| **Large state full of irrelevant detail** | Filter in code first; or filter for relevance with a Noul (RAG passages in [classification](../cookbooks/classification/SKILL.md)). |
| **Adversarial content** in the state (injected instructions, self-advocating text) | Be explicit in criteria; test edge cases before deploying. |
| **Contradictory instructions and criteria** (e.g. a Noul whose `true` means no) | Treat criteria as an extension of the instruction; align them. |
| **Choice option order** (leans toward the first option in some cases) | Reorder the options and check the answer stays consistent. |
| **Generation** | Use a generative model, or extract candidates with regex / an LLM and let a Choice pick. |

Counting in code, one Noul per item:

```python
from typesafe_sdk import Noul, TypeSafeClient

client = TypeSafeClient(model="jev-latest")
YES = 0.5  # up to you on what you want the threshold to be, depends on your usecase.

items = ["typesafe", "apple", "california", "banana", "likes", "calibration", "orange", "vertex"]

result = client.system_one(
    {"items": items},
    {
        f"item_{i}": Noul(instructions=f"Is `items[{i}]` the name of a fruit?")
        for i in range(len(items))
    },
)

count = sum(result.nouls[f"item_{i}"].noul > YES for i in range(len(items)))
```

Avoid: asking what code can compute exactly, hiding several judgments in one question, System Two tasks with layers of indirection, and more state than the question needs.

## Source docs

Verbatim copies, for details not covered above:

- [concepts/how-to-build-with-system-one.md](references/concepts-how-to-build-with-system-one.md)
- [concepts/use-case-map.md](references/concepts-use-case-map.md)
- [introduction/machine-learning-primer.md](references/introduction-machine-learning-primer.md)
- [model-jaggedness.md](references/model-jaggedness.md)
