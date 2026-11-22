---
name: guardrails-and-verification
description: 'Cookbooks for checking LLM inputs and outputs with Jev: screening every message into and out of an LLM app (guardrails with pass, review, block or support thresholds), double-checking citations against the source, verifying an LLM''s answer follows from its source paragraphs with Noul questions, and an SDE cascade that extracts with a cheap model, checks each field with Jev and escalates to a reasoning model. Use when adding guardrails, hallucination checks or verification to an LLM pipeline.'
---

# Guardrails and Verification Cookbooks

Four worked recipes for checking what goes into and comes out of an LLM: guardrails, citation checks, answer-vs-source verification, and a cheap-model cascade. Each is a runnable notebook and `.py` file in [typesafe-ai/typesafe-public-examples](https://github.com/typesafe-ai/typesafe-public-examples/tree/main/cookbooks) (they replay saved answers, so they run without an API key). The verbatim pages are in `references/`. Shared ideas: [patterns](../../patterns/SKILL.md) and [confidence](../../confidence/SKILL.md).

Common shape: a small helper builds Nouls with explicit yes/no criteria, one request asks the whole battery, and plain code turns the probabilities into an action.

```python
def noul(instructions: str, yes: str, no: str) -> Noul:
    return Noul(instructions=instructions, criteria=NoulCriteria(true=yes, false=no))
```

## Guardrails for LLMs (`llm_guardrails`)

**Problem:** LLM refusal lines vary by lab and version and live in weights; a system prompt is exactly what a jailbreak talks past; a second LLM as a guard costs a full call and can be talked past too.

**Approach:** screen every message **into and out of** the app with one request: a battery of Nouls for hazards plus a Score for how much harm complying would do. "Ignore your instructions" scores as a jailbreak instead of working as one.

- **Input battery:** `jailbreak`, `drop_safeguards`, `harmful_request`, `medical_advice`, `self_harm` (Nouls) + `severity` (Score: no harm, mild, serious, severe).
- **Output battery:** `broke_policy`, `harmful_request`, `medical_advice`, `self_harm` + `severity`.

```python
# A high-probability hazard triggers the product action below.
HAZARD_ACTION = {
    "jailbreak": "block",
    "drop_safeguards": "block",
    "broke_policy": "block",
    "harmful_request": "block",
    "medical_advice": "review",  # Routes to a human review path instead of blocking it
    "self_harm": "support",      # Routes to a support path instead of blocking it
}
PRECEDENCE = ["support", "block", "review", "pass"]  # Highest precedence wins

POLICIES = {
    "strict": {"review_threshold": 0.35, "action_threshold": 0.70, "severity_block": 2.0},
    "permissive": {"review_threshold": 0.70, "action_threshold": 0.85, "severity_block": 2.0},
}


def route(nouls: dict[str, float], severity: float, policy: dict) -> str:
    """Turn Jev's assessment of one message into one policy-specific action."""
    triggered = []
    for hazard, probability in nouls.items():
        if probability >= policy["action_threshold"]:
            triggered.append(HAZARD_ACTION[hazard])
        elif probability >= policy["review_threshold"]:
            triggered.append("review")
    if severity >= policy["severity_block"]:
        triggered = ["block" if action == "review" else action for action in triggered]
    return next((action for action in PRECEDENCE if action in triggered), "pass")
```

The same probabilities support different policies: a tone jailbreak with `drop_safeguards` = 0.81 is blocked under `strict` and sent to review under `permissive`. Rules live in code you can read and change.

## Double-checking citations (`citation_check`)

**Problem:** an LLM attaches citations (claim + section + quote); some quotes are missing from the source, or present but in a context that says the opposite.

**Approach:** two steps in `check_citation()`:

1. **String match in code**: a quote not in the document is `fabricated` (no model call).
2. **One Choice** reads the section and decides its relation to the claim:

```python
QUESTIONS = {
    "relation": Choice(
        instructions="How does the section relate to the claim?",
        criteria={
            "supports": "The section states the claim or directly implies that it is true",
            "contradicts": "The section states the opposite of the claim or implies it is false",
            "says_nothing": "The section does not address what the claim asserts, either way",
        },
    ),
}

RELATION_TO_VERDICT = {
    "supports": "verified",
    "contradicts": "contradicted",
    "says_nothing": "unsupported",
}
```

State is `{"claim": ..., "section": ...}`. Answers with confidence below an auto-accept threshold go to a person. On eight citations about RFC 7519 (JWT), the four accurate ones were `verified` at confidence ≥ 0.98 and all four planted failures were caught (one fabricated, one contradicted, two unsupported, one of them sent to a human).

## Verifying LLM answers against their source (`verify_llm_outputs`)

**Problem:** with retrieved paragraphs, an LLM sometimes fills a missing step with a guess, or wrongly says the paragraphs don't answer the question. Both look like right answers.

**Approach:** one request, three Nouls, over a state of `request`, `response_requirement`, `paragraphs`, `candidate_response`:

- `answerable`: do the paragraphs state every fact needed?
- `declines`: does the candidate decline or say information is missing?
- `supported`: following the paragraphs step by step, do you arrive at the candidate's answer?

```python
def check_answer(question: str, paragraphs: str, answer: str) -> dict:
    nouls = ask_jev(
        question, paragraphs, answer, as_json(CHECK_QUESTIONS), model=TYPESAFE_MODEL
    )["nouls"]
    if nouls["declines"] >= 0.5:
        risk = nouls["answerable"]  # it declined: risky if the paragraphs do answer
    else:
        risk = 1 - nouls["supported"]  # it answered: risky if the paragraphs don't lead there
    return {**nouls, "risk": risk, "status": "review" if risk >= REVIEW_AT else "pass"}
```

Results on 1,000 multi-hop questions answered by `gpt-6-luna` (88.5% right):

| Passed when | Passed | Accuracy of passed | Wrong answers caught |
| --- | --- | --- | --- |
| every answer | 1,000 (100%) | 88.5% | 0 of 115 |
| risk below 0.2 | 727 (73%) | 95.7% | 84 of 115 |
| risk below 0.3 | 825 (82%) | 94.2% | 67 of 115 |
| risk below 0.5 | 917 (92%) | 91.9% | 41 of 115 |
| risk below 0.7 | 965 (96%) | 90.3% | 21 of 115 |

Pick the review threshold by the trade you want between review volume and accuracy. The cookbook also labels answers with a `matches_reference` Noul and rechecks disagreements with a reasoning model.

## SDE cascade (`sde_cascade`)

**Problem:** big reasoning models extract structured data correctly but slowly and expensively; small models are cheap but err.

**Approach:** a cascade:

1. **Answer** with a cheap model (`gpt-6-luna`) as JSON matching a schema.
2. **Verify** with Jev: one Noul per rule the answer must follow, each returning P(rule broken), all in one request.
3. **Escalate** to a reasoning model (`gpt-6.1-sol`, `reasoning_effort="high"`) if the schema check fails or **any** rule fires.

```python
RULES = {
    "busy_conflict": "Does the meeting time in the `answer` overlap a time when any participant in the `task` is busy?",
    "outside_hours": "Is the meeting time in the `answer` outside the work hours or the days the `task` allows?",
    "breaks_preference": "Does the meeting time in the `answer` break a preference stated in the `task`, such as a participant who would rather not meet on a certain day or before or after a certain time?",
    "not_earliest": "Does the `task` ask for the earliest availability, and is there an earlier time that works for every participant?",
    "wrong_length": "Is the meeting in the `answer` a different length from the one the `task` asks for?",
    "no_single_time": "Does the `answer` fail to propose exactly one day and one start and end time?",
}
CHECKS = {
    rule: Noul(
        instructions=question,
        criteria=NoulCriteria(true="the answer breaks this rule", false="the answer follows this rule"),
    )
    for rule, question in RULES.items()
}
```

Escalate when `max` probability > `FIRE_T` (0.7 in the example): one confident red flag is enough, not averaged away. This works only if the questions separate broken from kept rules, and the verifier must cost far less than the reasoning rung. Evaluated on the 1,000 NATURAL PLAN calendar-scheduling tasks with `jev-1.14.0`; the page plots cost against quality.

## Related

- Classifying RAG passages before they reach the model: [classification](../classification/SKILL.md).
- Agent tool selection and skill suggestion: [agents-and-llm-apps](../agents-and-llm-apps/SKILL.md).
- Self-consistency of moderation decisions: [evaluation-and-performance](../evaluation-and-performance/SKILL.md).

## Source docs

Verbatim copies, for details not covered above:

- [cookbooks/llm_guardrails.md](references/cookbooks-llm_guardrails.md)
- [cookbooks/citation_check.md](references/cookbooks-citation_check.md)
- [cookbooks/verify_llm_outputs.md](references/cookbooks-verify_llm_outputs.md)
- [cookbooks/sde_cascade.md](references/cookbooks-sde_cascade.md)
