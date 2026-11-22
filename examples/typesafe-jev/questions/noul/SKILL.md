---
name: noul
description: 'The Noul question type: a yes/no question or statement that returns `noul`, the probability that the answer is yes (0 to 1), with optional `criteria` that clarify what yes and no mean. Covers phrasing statements, thresholds, and why Noul has no separate confidence. Use when checking whether something is true of the state (PII present, refund requested, claim supported), and when using `Noul(...)` in Python or `noul(...)` in JavaScript.'
---

# Noul

Ask Jev a yes/no question (or give it a statement to judge) and get `noul`: the probability that the answer is yes, from 0 to 1. Use it for checks like "does this message ask for a refund", "does this resume mention distributed systems", "does this comment contain personal data". For one of several options use [choice](../choice/SKILL.md); for a degree on a spectrum use [score](../score/SKILL.md). General rules are in [questions](../SKILL.md).

## Request

- `type`: always `"noul"`.
- `instructions`: the yes/no question, or a statement to judge.
- `criteria` (optional): `true` and `false` descriptions of what counts as yes and no.

```python
from typesafe_sdk import Noul, NoulCriteria, TypeSafeClient

with TypeSafeClient() as client:
    response = client.system_one(
        model="jev-latest",
        state="I have asked three times now. Can I please just talk to a real person?",
        questions={
            "is_human_escalation": Noul(
                instructions="Is the customer asking for a human agent?",
            ),
            "is_repeat_contact": Noul(
                instructions="Has the customer contacted support about this before?",
                criteria=NoulCriteria(
                    true="Mentions a prior attempt, ticket, or that they have asked before",
                    false="No sign of any previous contact",
                ),
            ),
        },
    )

    print(response.answers["is_human_escalation"].noul)
    print(response.answers["is_repeat_contact"].noul)
```

In JavaScript: `noul("Is the customer asking for a human agent?")`. Over HTTP: `{"type": "noul", "instructions": "...", "criteria": {"true": "...", "false": "..."}}`.

## Response

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "is_human_escalation": {"type": "noul", "noul": 0.99},
    "is_repeat_contact": {"type": "noul", "noul": 0.93}
  },
  "usage": {"input_tokens": 360, "output_tokens": 39}
}
```

There is **no `confidence`** for a Noul: with only two outcomes, `noul` describes the whole distribution. Near 1 = strong yes, near 0 = strong no, near 0.5 = undecided.

Recorded `jev-1.13.0` answers to `is_human_escalation`:

| State | `noul` |
| - | - |
| Thanks, that fixed it! | 0.02 |
| How do I reset my password? | 0.07 |
| I need this sorted today, whatever it takes. | 0.26 |
| Are you a bot? | 0.40 |
| Is there any way to speak to someone about my invoice? | 0.84 |
| I have asked three times now. Can I please just talk to a real person? | 0.99 |

## Thresholds

Most code thresholds `noul` into a boolean:

```python
wants_human = response.answers["is_human_escalation"].noul > 0.9

if wants_human:
    route_to_agent(ticket)
else:
    route_to_bot(ticket)
```

- Start at **0.7 for yes** and **0.3 for no**. Often only the yes threshold matters.
- Raise the yes threshold when a false yes is expensive (paging someone, issuing a refund). Lower it when missing a true yes is expensive (failing to flag a safety issue).
- Send values between 0.3 and 0.7 to a person: the same three-way split as in [confidence](../../confidence/SKILL.md).
- Don't fit thresholds tightly to a handful of test cases.

Route several Nouls with a review band:

```python
from typesafe_sdk import Noul, NoulCriteria, TypeSafeClient

SUPPORT_QUESTIONS = {
    "is_human_escalation": Noul(
        instructions="Is the customer asking for a human agent?",
    ),
    "is_repeat_contact": Noul(
        instructions="Has the customer contacted support about this before?",
        criteria=NoulCriteria(
            true="Mentions a prior attempt, ticket, or that they have asked before",
            false="No sign of any previous contact",
        ),
    ),
}

YES = 0.7
NO = 0.3


def route(message: str) -> None:
    with TypeSafeClient() as client:
        response = client.system_one(
            model="jev-latest",
            state=message,
            questions=SUPPORT_QUESTIONS,
        )
    answers = response.answers

    wants_human = answers["is_human_escalation"].noul
    repeat = answers["is_repeat_contact"].noul

    if NO < wants_human < YES or NO < repeat < YES:
        # The model isn't sure either way. Let a person decide.
        send_to_review(message)
        return

    priority = "high" if repeat >= YES else "normal"
    if wants_human >= YES:
        route_to_agent(message, priority=priority)
    else:
        route_to_bot(message, priority=priority)
```

Too many messages to review: narrow the gap between `NO` and `YES`. Too many wrong routes: widen it. Need another check (mentions a payment, contains personal data)? Add another Noul; it stays one call.

## Noul is not a degree

A Noul value is the probability of yes, **not** a measure of the thing you asked about. "Is the candidate strong in Python?" vs a four-level Score ("no experience", "some familiarity", "regular use in a job", "deep expertise"):

| Candidate | Noul: "strong in Python?" | Score: "how much Python experience?" |
| - | - | - |
| Java and Go, no Python | 0.03 | 0.0 (No experience) |
| Occasional small scripts | 0.14 | 1.0 (Some familiarity) |
| Daily for two years, data pipelines | 0.81 | 2.05 (Regular use in a job) |
| Daily for eight years, large Django codebase | 0.92 | 2.89 (Deep expertise) |

A middle Noul value can mean "medium" or "unclear", and code-side bands (e.g. 0.3–0.7 = "some experience") were never seen by the model. For degree, use a Score.

## Writing a Noul

- **One condition per Noul.** "Is the customer angry and asking for a refund?" forces two judgments into one number. Ask two Nouls and combine in code.
- **High value = yes.** "Does the message contain personal data?", not "Is the message free of personal data?" (inverted meaning gets misread later).
- **Statements work too.** "The customer is requesting a refund": near 1 means true. Try both phrasings on your data.
- **Make the boundary unambiguous.** "Does this candidate have *any* Python experience?" leaves no middle ground. When the boundary is subtle, add `criteria` with `true` / `false`. The instruction alone is usually enough, so compare with and without criteria on your documents.
- **Checklists:** one Noul per condition, all in one request; code decides what the combination means.

## Questions built in code (structured instructions)

`instructions` can be an object: the question in one field, supplementary data in others. Here a new resume is checked against candidate duplicate records, one Noul per record, all in one request, with record IDs in the question keys:

```python
from typesafe_sdk import Noul, TypeSafeClient

SAME_PERSON = "Is the resume for the same person as `potential_duplicate`?"


def duplicate_questions(candidates: list[dict]) -> dict[str, Noul]:
    """One Noul per candidate record, all asking the same question."""
    return {
        f"same_as_record_{candidate['id']}": Noul(
            instructions={
                "potential_duplicate": {
                    "name": candidate["name"],
                    "location": candidate["location"],
                    "last_employer": candidate["last_employer"],
                },
                "question": SAME_PERSON,
            },
        )
        for candidate in candidates
    }


def find_duplicates(resume: dict, candidates: list[dict]) -> list[str]:
    with TypeSafeClient() as client:
        response = client.system_one(
            model="jev-latest",
            state={"resume": resume},
            questions=duplicate_questions(candidates),
        )
    return [
        question_id
        for question_id, answer in response.answers.items()
        if answer.noul > 0.7
    ]
```

A record with a differently spelled name but the same location and employer scored 0.74; same name, different city and employer scored 0.09. More on structure in [structured-questions](../structured-questions/SKILL.md).

## Where Nouls shine in the cookbooks

- Re-ranking: sort candidates by the `noul` value itself, no threshold ([search-and-ranking](../../cookbooks/search-and-ranking/SKILL.md)).
- A Choice that finds a line paired with a Noul that checks an answer exists ([search-and-ranking](../../cookbooks/search-and-ranking/SKILL.md)).
- One Noul per pair of lines to rebuild paragraphs ([extraction](../../cookbooks/extraction/SKILL.md)).
- A 13-question checklist in one request, and self-consistency over 14 Nouls ([evaluation-and-performance](../../cookbooks/evaluation-and-performance/SKILL.md)).
- Verifying each extracted field with the same structured questions ([guardrails-and-verification](../../cookbooks/guardrails-and-verification/SKILL.md)).

## Source docs

Verbatim copies, for details not covered above:

- [primitives/noul.md](references/primitives-noul.md)
