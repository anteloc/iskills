---
name: choice
description: 'The Choice question type: selecting one option from a defined set of options (`criteria` as a map of option keys to descriptions), with a probability for every option and a confidence. Covers writing options, reading `choice`, `probabilities` and `confidence`, large option sets, and what to do when no option fits. Use when routing, classifying, or picking one label, and when using `Choice(...)` in Python or `choice(...)` in JavaScript.'
---

# Choice

Ask Jev to pick one option from a fixed set: which team handles a ticket, which category a product is in, which language a snippet is written in. The answer is the selected option, a probability for every option, and a confidence. For a position on a spectrum use [score](../score/SKILL.md); for yes/no use [noul](../noul/SKILL.md). General question-writing rules are in [questions](../SKILL.md).

## Request

A Choice question has:

- `type`: always `"choice"`.
- `instructions`: the question.
- `criteria`: a map of **option name → description**. Both names and descriptions are sent to the model (the question ID is not), so write descriptions that separate the options from each other. A description can be `None` / `null` when the name is clear on its own.

```python
from typesafe_sdk import Choice, TypeSafeClient

with TypeSafeClient() as client:
    response = client.system_one(
        state="My running shoes arrived in the wrong size. Can I swap them for a size 10?",
        questions={
            "department": Choice(
                instructions="Which team should handle this?",
                criteria={
                    "returns": "Exchanges, wrong or damaged items",
                    "shipping": "Delivery status, delays, lost packages",
                    "billing": "Charges, invoices, payment problems",
                },
            ),
        },
    )

    print(response.answers["department"].choice)
```

Over HTTP the question is `{"type": "choice", "instructions": "...", "criteria": {"returns": "...", ...}}` inside `questions`. In JavaScript: `choice("Which team should handle this?", { returns: "...", ... })`.

## Response

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "department": {
      "type": "choice",
      "choice": "returns",
      "confidence": 1.0,
      "probabilities": {"shipping": 0.0, "returns": 1.0, "billing": 0.0}
    }
  },
  "usage": {"input_tokens": 328, "output_tokens": 34}
}
```

| Field | Meaning |
| --- | --- |
| `choice` | The option with the highest probability. |
| `probabilities` | Distribution over every option; sums to 1. |
| `confidence` | 0 to 1, computed from how `probabilities` is spread: one peak = high, flat = low. See [confidence](../../confidence/SKILL.md). |

A ticket that mentions both a wrong size and a missing refund splits probability between `returns` and `billing`, and confidence drops.

## Options

- Give the **full list** (teams, categories, products), not a shortlist. A Choice accepts **up to 255 options**, and each extra option costs only a few tokens.
- A Choice **always picks one**. When the list may not cover every input you can add an `other` / `none of the above` option, but it often works poorly: it competes with real options for probability. Better: a **companion Noul** in the same request ("Does `message` name any of `our_products`?") and read the Choice only when the Noul says yes. See [patterns](../../patterns/SKILL.md).
- For deep hierarchies or large taxonomies, chain Choices level by level with a beam search over probabilities ([classification](../../cookbooks/classification/SKILL.md)).

## Several Choices in one request

Ask every Choice your code might need at once, including speculative ones. Then read only what applies and treat low confidence as a reason to ask rather than act:

```python
from typesafe_sdk import Choice, TypeSafeClient

TRIAGE_QUESTIONS = {
    "department": Choice(
        instructions="Which team should handle this?",
        criteria={
            "returns": "Exchanges, wrong or damaged items",
            "shipping": "Delivery status, delays, lost packages",
            "billing": "Charges, invoices, payment problems",
        },
    ),
    "return_reason": Choice(
        instructions="If the customer wants to return something, why?",
        criteria={
            "wrong_size": "The item doesn't fit",
            "wrong_item": "A different product was delivered",
            "damaged": "The item arrived broken or faulty",
            "changed_mind": "The item is fine, the customer no longer wants it",
            "other": "A return reason that fits none of the above",
        },
    ),
    "shipping_issue": Choice(
        instructions="If this is a shipping problem, which kind is it?",
        criteria={
            "not_delivered": "The package never arrived",
            "delayed": "The package is late but still on its way",
            "wrong_address": "The package went to the wrong place",
            "damaged_in_transit": "The package arrived damaged",
            "other": "A shipping problem that fits none of the above",
        },
    ),
    "requested_resolution": Choice(
        instructions="What does the customer want to happen?",
        criteria={
            "exchange": "Swap the item for a different one",
            "refund": "Money back",
            "replacement": "The same item sent again",
            "information": "Just an answer, no action needed",
        },
    ),
    "tone": Choice(
        instructions="What is the customer's tone?",
        criteria={"calm": None, "frustrated": None, "angry": None},
    ),
}


def triage(ticket: str) -> None:
    with TypeSafeClient() as client:
        response = client.system_one(
            state=ticket,
            questions=TRIAGE_QUESTIONS,
        )
    answers = response.answers

    department = answers["department"]
    if department.confidence < 0.3:
        # Not clear which team to send to. Let a person decide.
        send_to_manual_triage(ticket)
        return

    if department.choice == "returns":
        # return_reason answer is only used here
        assign(ticket, team="returns", issue=answers["return_reason"].choice)
    elif department.choice == "shipping":
        # shipping_issue answer is only used here
        assign(ticket, team="shipping", issue=answers["shipping_issue"].choice)
    else:
        assign(ticket, team="billing")

    # A second team with a real share of the probability gets a copy
    for team, probability in department.probabilities.items():
        if team != department.choice and probability > 0.25:
            notify(ticket, team=team)

    resolution = answers["requested_resolution"]
    if resolution.confidence < 0.5:
        # The customer hasn't said what they want. Ask, don't guess.
        ask_customer_what_they_want(ticket)
    elif resolution.choice == "refund":
        flag_for_refund_approval(ticket)

    if answers["tone"].choice == "angry":
        flag_for_senior_agent(ticket)
```

On an ambiguous ticket (wrong size plus a double charge, no stated wish), Jev answered `department: returns` at 0.61 with `billing` 0.35 (confidence 0.42), `return_reason: wrong_size` (confidence 1.0), and `requested_resolution: refund` at only 0.40 (confidence 0.20). So the code routes to returns, copies billing (0.35 > 0.25), and asks the customer what they want. `shipping_issue` is ignored. Adding another question (language, product) keeps the call count at one.

Use the second-highest probability, not just `choice`: a real share for another option is a useful signal (here, copy a second team).

## Structured option descriptions

When two options keep getting confused, describe each with an **object** instead of a string: what it covers, what belongs to a neighbor instead, and example inputs. For example, `return_policy` vs `return_status` options, each saying what it is *not* for, resolved a ticket to `return_status` at confidence 1.0. Field names such as `question`, `focus`, `what`, `not_for` and `examples` are not part of the API and none are reserved; choose short names that label what follows (the model sees them). Details in [structured-questions](../structured-questions/SKILL.md).

## Pitfalls

- Relying on `none of the above` to catch inputs that fit nothing. Prefer a companion Noul.
- Vague, overlapping descriptions: Jev sees them, so make them distinguish the options.
- One request per Choice. Batch them.

## Source docs

Verbatim copies, for details not covered above:

- [primitives/choice.md](references/primitives-choice.md)
