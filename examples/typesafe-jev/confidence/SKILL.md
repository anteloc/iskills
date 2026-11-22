---
name: confidence
description: 'Using Jev''s confidence and probabilities to decide what code does: how confidence is derived from the probability distribution (and differs from it), "I don''t know" as a signal, acting automatically vs escalating to a person or a reasoning model, thresholds that scale with risk, routing by confidence as a second axis, and routing by probability with stricter thresholds for riskier actions. Use when setting thresholds, deciding when to trust an answer, or building human-review or escalation paths.'
---

# Confidence and Routing

Decide what your code does with a Jev answer: act automatically, confirm, or hand off to a person or another system. Covers what `confidence` is and how it relates to `probabilities`, which number to threshold for each question type, risk-scaled thresholds, routing a Score by confidence, and routing a Choice by probability. The answer fields themselves are described in [questions](../questions/SKILL.md).

## What confidence is

Choice and Score answers carry `probabilities` (a distribution over your options or levels) and `confidence`, a 0–1 summary of how **concentrated** that distribution is: 1 when everything is on one outcome, 0 when it's spread evenly. Noul answers have no `confidence`: the `noul` value is already the probability of yes.

- Low confidence on a **Choice** usually means no option clearly wins.
- Low confidence on a **Score** usually means the levels are ambiguous or multi-dimensional, or the state doesn't say enough.
- Confidence is on the same 0–1 scale for every question, so it's useful for comparing uncertainty across questions.

"I don't know" is a feature: honest uncertainty is what lets you build behavior you can rely on.

## Three paths

| Confidence | Behavior |
| --- | --- |
| High | Act automatically. |
| Medium | Proceed with caution: ask the user to confirm, flag for review, or gather more information. |
| Low | Don't act: route to a person, ask for clarification, or fall back to another system. |

**Thresholds scale with risk.** Different actions in the same system get different thresholds:

```python
response = client.system_one(
    state=user_message,
    questions={
        "action": Choice(
            instructions="What is the user trying to do?",
            criteria={
                "check_balance": "View account balance",
                "approve_transfer": "Approve the pending withdrawal request",
                "support": "Get help with an issue",
            },
        ),
    },
)

action = response.answers["action"]
confidence = action.confidence

if confidence < 0.5:
    # Model is genuinely unsure. Don't guess.
    route_to_human(user_message)

elif action.choice == "check_balance":
    # Low stakes. Showing the wrong screen is recoverable.
    show_balance(account_id)

elif action.choice == "approve_transfer":
    if confidence > 0.9:
        # High stakes, high confidence. Proceed with confirmation.
        confirm_then_execute(account_id)
    else:
        # High stakes, moderate confidence. Verify first.
        ask_user_to_confirm(account_id)
```

Start conservative, test on your own data, adjust. Correct values depend on your domain.

## Which number to threshold

Confidence measures concentration, **not** the probability that the answer is correct. A Choice confidence of 0.5 means a top probability of 0.75 with 2 options, 0.67 with 3, and 0.55 with 10.

| Question | Threshold on | Why |
| --- | --- | --- |
| Noul | `noul` itself | Already the probability of yes. Start at 0.7 (yes) / 0.3 (no) and give the 0.3–0.7 band its own outcome. |
| Choice | `probabilities[choice]` (the option you'll act on) | Reads directly as risk: "act above 0.9" = "act when the chance of the wrong option is under 10%". For a fixed number of options, `confidence` is just a transform of the top probability, so checking both adds nothing. |
| Score, decision hinges on one level boundary | Sum of the probabilities on the side that matters | The position can sit between levels and hide a split; probability on a neighbor barely lowers confidence. |
| Score, "is the answer settled at all?" | `confidence` first, then route on `score` | Catches probability spread across distant levels that the position hides. |

To tell a close runner-up from probability spread across many options, look at the other probabilities or the top-to-second ratio.

## Routing a Choice by probability

Give each action its own probability threshold; riskier actions need more. Below the threshold is its own outcome (clarify, hand off), not a yes. Voice banking example:

```python
action = response.answers["intent"]
likelihood = action.probabilities[action.choice]

# Below 0.7 on any action, the command didn't settle the intent. Route to a human.
if likelihood < 0.7:
    route_to_support_agent(account_id)

elif action.choice == "check_balance":
    # Low stakes. 0.7 is sufficient.
    show_balance(account_id)

elif action.choice == "approve_transfer":
    if likelihood > 0.9:
        # Identifying the intent starts confirmation; it does not approve a transfer.
        show_transfer_for_confirmation(account_id)
    else:
        # Clarify what the user wants before opening the transfer workflow.
        ask_user_to_clarify("Would you like to review the pending transfer?")

else:
    route_to_support_agent(account_id)
```

Thresholds pick the **workflow**; none of them moves money. A clear intent is not consent: "Um, the transfer thing... yeah, go ahead I guess." got 0.99 for `approve_transfer` (`jev-1.14.0`), which identifies the action but doesn't mean the user checked the details. Keep a confirmation step for risky actions. (The example's `other` option keeps it short; a companion Noul is usually a better catch-all, see [patterns](../patterns/SKILL.md).)

## Routing a Score by confidence

Use confidence as a second axis: check it first, send unsettled answers to a person, route the rest on the score. Bug triage with five severity levels (cosmetic → critical):

```python
severity = response.answers["severity"]

if severity.confidence < 0.5:
    # The probability is spread across the scale. A person reads the report first.
    send_to_triage(report_id)

elif severity.score < 1.5:
    add_to_backlog(report_id)

elif severity.score < 2.5:
    add_to_sprint(report_id)

else:
    message_on_call(report_id)
```

| Report (`jev-1.14.0`) | `score` | `confidence` | Outcome |
| - | - | - | - |
| Typo on the settings page | 0.0 | 1.0 | backlog |
| PDF export fails over 50 pages; splitting works | 2.0 | 1.0 | this sprint |
| Checkout returns 500 for every customer | 3.36 | 0.7 | message on-call |
| Notes gone after the update, or maybe deleted | 3.19 | 0.34 | triage |

The "notes gone" report scored 3.19, which alone would page the engineer, but its probabilities were 0.59 on critical and 0.14 on minor (deleted by the user?), so confidence 0.34 sends it to a person.

**When two neighboring levels split the answer**, confidence stays fairly high and the answer can land on the wrong side of a boundary. Sum the levels on the side that matters:

```python
blocked = severity.probabilities[3] + severity.probabilities[4]

if blocked >= 0.3:
    # A real chance users are blocked. Message someone rather than wait for the sprint.
    message_on_call(report_id)
```

## How confidence is calculated

The formulas are exact, and every answer includes its full `probabilities`, so you can compute any other measure you prefer.

**Noul:** no `confidence`. If you want one on the same scale as Choice: `|2p - 1|`.

**Choice** with `n` options and top probability `p_max`: `(p_max - 1/n) / (1 - 1/n)`. Only the top probability counts: (0.6, 0.3, 0.1) and (0.6, 0.2, 0.2) both give 0.4.

```python
def choice_confidence(probabilities: list[float]) -> float:
    n = len(probabilities)
    return (max(probabilities) - 1 / n) / (1 - 1 / n)


choice_confidence(list(answer.probabilities.values()))
```

Alternatives worth trying: the **top probability** itself (set its threshold per question, since its meaning depends on `n`) and the **top-to-second ratio** `p_max / p_second` (how clearly the winner beats the runner-up).

**Score** with levels `0..n-1` and most likely level `m`: `max(0, 1 - Σ p_i·|i - m| / MAD_unif)`, where `MAD_unif = (1/n) Σ |i - (n-1)/2|`. Probability on a neighboring level costs less than on a distant one: with three levels, (0, 0.5, 0.5) → 0.25 but (0.5, 0, 0.5) → 0.

```python
def score_confidence(probabilities: list[float]) -> float:
    n = len(probabilities)
    m = probabilities.index(max(probabilities))
    spread = sum(p * abs(i - m) for i, p in enumerate(probabilities))
    even_spread = sum(abs(i - (n - 1) / 2) for i in range(n)) / n
    return max(0.0, 1 - spread / even_spread)


levels = sorted(answer.probabilities)
score_confidence([answer.probabilities[level] for level in levels])
```

Worked: probabilities (0, 0.57, 0.43) → m = 1, spread 0.43, MAD_unif = 2/3, confidence ≈ 0.35.

Confidence thresholds are tuned against a model version. Pin the versioned model ID (e.g. `jev-1.14.0`) if you rely on them, as described in the [root skill](../SKILL.md).

## Source docs

Verbatim copies, for details not covered above:

- [confidence.md](references/confidence.md)
- [patterns/confidence-routing.md](references/patterns-confidence-routing.md)
- [patterns/probability-routing.md](references/patterns-probability-routing.md)
