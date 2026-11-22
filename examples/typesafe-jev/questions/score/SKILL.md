---
name: score
description: 'The Score question type: rating the state against ordered, descriptive levels (`criteria` as a list of levels), returning a fractional `score`, a `legend`, per-level `probabilities` and `confidence`. Covers writing levels, interpreting scores between levels, normalizing, and splitting a complex judgment into several Scores combined with weights. Use when measuring severity, quality, frustration, risk or any position on a spectrum, and when using `Score(...)` in Python or `score(...)` in JavaScript.'
---

# Score

Ask Jev where the state falls on a spectrum you describe in steps: how severe a bug is, how frustrated a customer is, how much Python experience a candidate has. The answer is a position along your levels (it can fall between two), a probability per level, and a confidence. For unordered options use [choice](../choice/SKILL.md); for yes/no use [noul](../noul/SKILL.md). General rules are in [questions](../SKILL.md).

## Request

- `type`: always `"score"`.
- `instructions`: what is being rated.
- `criteria`: an **ordered array** of level descriptions, low end first. At least 2 levels; the API accepts **up to 10**. A level's number is its index (0, 1, 2, ...).

```python
from typesafe_sdk import Score, TypeSafeClient

with TypeSafeClient() as client:
    response = client.system_one(
        state="The export button crashes the settings page in Safari. It works in Chrome, but a few of our customers only use Safari.",
        questions={
            "bug_severity": Score(
                instructions="How severe is the reported issue?",
                criteria=[
                    "Cosmetic; no impact to functionality",
                    "Broken or degraded feature, but workaround exists",
                    "Blocking issue; no workaround exists",
                ],
            ),
        },
    )

    print(response.answers["bug_severity"].score)
```

In JavaScript: `score("How severe is the reported issue?", ["Cosmetic; ...", "Broken ...", "Blocking ..."])`. Over HTTP: `{"type": "score", "instructions": "...", "criteria": ["...", "...", "..."]}`.

## Response

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "bug_severity": {
      "type": "score",
      "score": 1.43,
      "confidence": 0.35,
      "legend": {
        "0": "Cosmetic; no impact to functionality",
        "1": "Broken or degraded feature, but workaround exists",
        "2": "Blocking issue; no workaround exists"
      },
      "probabilities": {"0": 0.0, "1": 0.57, "2": 0.43}
    }
  },
  "usage": {"input_tokens": 332, "output_tokens": 18}
}
```

| Field | Meaning |
| --- | --- |
| `score` | Probability-weighted mean of the level numbers, 0 to top level: 0 × 0.0 + 1 × 0.57 + 2 × 0.43 = 1.43. |
| `probabilities` | Probability per level, keyed by level number (strings in JSON; integers in the Python `ScoreAnswer`). Sums to 1. |
| `legend` | Level number → description (as you sent it). |
| `confidence` | 0 to 1 from how peaked `probabilities` is. See [confidence](../../confidence/SKILL.md). |

## Reading a score

| State | `score` | `confidence` | P(0) | P(1) | P(2) |
| --- | --- | --- | --- | --- | --- |
| Export button misaligned by a few pixels | 0.0 | 1.0 | 1.0 | 0.0 | 0.0 |
| PDF export does nothing; CSV works but is slow | 1.0 | 1.0 | 0.0 | 1.0 | 0.0 |
| PDF export spins forever; CSV works for some | 1.11 | 0.84 | 0.0 | 0.89 | 0.11 |
| Crashes in Safari, works in Chrome, some users Safari-only | 1.43 | 0.35 | 0.0 | 0.57 | 0.43 |
| Nobody can log in; 500 on every attempt | 2.0 | 1.0 | 0.0 | 0.0 | 1.0 |

- A fractional score is a **position**: use it to rank, or round to the nearest level when code needs one outcome.
- The same score can come from different distributions (1.0 = all on level 1, or half on 0 and half on 2). Read `probabilities` and `confidence` too.
- Confidence 1.0 describes the distribution, not correctness.
- Low confidence usually means the levels overlap for this state, the question measures more than one thing, or the state doesn't say enough.

## Writing good levels

- **Describe situations, not degrees.** "Broken or degraded feature, but workaround exists" gives the model something to match; "Moderately severe" doesn't.
- **Each level is judged on its own.** The model doesn't see level numbers or neighbors, so "worse than the previous level" and numbers in descriptions or instructions mean nothing. With `criteria: ["0", "1", "2"]` and "Rate severity from 0 to 2", the misaligned-button report scored 0.55 (confidence 0.33) instead of 0.0 (confidence 1.0).
- **As many levels as you can describe distinctly**, up to 10. Three is fine.
- **One dimension per Score.** "Punctual and smart and experienced" measures three things; split it.
- **Give a rare extreme its own level** if you must act on it differently (add "abusive or threatening" above "very angry").
- **No in-between?** Use a Choice or several Nouls.
- Check answers against known examples; higher confidence alone does not prove a description is better. Two wordings of a scale can behave differently on your data.

## Several Scores combined in code (composite scoring)

Split a complex judgment into one Score per factor, send them in one request, **normalize** each by its top level (`len(criteria) - 1`) so scales of different lengths are comparable, then weight in code:

```python
from typesafe_sdk import Score, TypeSafeClient

TRIAGE_QUESTIONS = {
    "severity": Score(
        instructions="How severe is the reported issue?",
        criteria=[
            "Cosmetic; no impact to functionality",
            "Broken or degraded feature, but workaround exists",
            "Blocking issue; no workaround exists",
        ],
    ),
    "frustration": Score(
        instructions="How frustrated is the customer?",
        criteria=[
            "Calm, just stating facts",
            "Frustrated but civil",
            "Very angry, strong language or threatening to leave",
        ],
    ),
    "report_quality": Score(
        instructions="How much does the report give an engineer to work with?",
        criteria=[
            "No detail; just says something is broken",
            "Names the feature but no steps or environment",
            "Steps to reproduce or environment, but not both",
            "Steps to reproduce and environment",
        ],
    ),
}


def normalized(answers, question_id: str) -> float:
    """Put a score on 0 to 1 by dividing by its top level number."""
    top_level = len(TRIAGE_QUESTIONS[question_id].criteria) - 1
    return answers[question_id].score / top_level


def priority(ticket: str) -> float:
    with TypeSafeClient() as client:
        response = client.system_one(
            state=ticket,
            questions=TRIAGE_QUESTIONS,
        )
    answers = response.answers

    severity = normalized(answers, "severity")
    frustration = normalized(answers, "frustration")
    report_quality = normalized(answers, "report_quality")

    # A detailed report helps an engineer investigate, so it raises priority a little.
    return 0.6 * severity + 0.3 * frustration + 0.1 * report_quality
```

For a sample ticket Jev returned severity 1.24, frustration 1.28 and report quality 3.0; normalized 0.62, 0.64 and 1.0; priority `0.6 × 0.62 + 0.3 × 0.64 + 0.1 × 1.0 = 0.664`. The weights are yours: when the ranking doesn't match your team's judgment, change them and rerun. More in [patterns](../../patterns/SKILL.md) (composite scoring).

## Structured level descriptions

When the model keeps landing between two neighboring levels on inputs you think are clear, make each level an object with the **same field names** on every level, e.g. a `what` and an `examples` list:

```json
"criteria": [
  {"what": "Cosmetic; no impact to functionality", "examples": ["typo in a label", "misaligned icon"]},
  {"what": "Broken or degraded feature, but workaround exists", "examples": ["export fails in one browser but works in another"]},
  {"what": "Blocking issue; no workaround exists", "examples": ["cannot log in", "data loss"]}
]
```

Examples help only when they resemble your real inputs. On the Safari report:

| Level description | `score` | `confidence` |
| - | - | - |
| Plain strings | 1.43 | 0.35 |
| With a matching example ("export fails in one browser but works in another") | 1.03 | 0.96 |
| With an unrelated example ("search fails, but browsing categories still works") | 1.43 | 0.35 |

Pick examples with known expected levels, then test on separate inputs before keeping them. See [structured-questions](../structured-questions/SKILL.md).

## Source docs

Verbatim copies, for details not covered above:

- [primitives/score.md](references/primitives-score.md)
