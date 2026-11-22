---
name: evaluation-and-performance
description: 'Cookbooks on measuring and scaling Jev: parallel questions (13 questions batched into one call, 12.2x cheaper and 11.8x faster), self-consistency tests for Choice and Noul decisions compared with LLMs on borderline moderation and insurance cases, and autoresearch feature discovery where an LLM proposes questions, Jev answers them per row, and CatBoost trains on the answers. Use when benchmarking reliability, optimizing cost and latency, or using Jev answers as features for a classical model.'
---

# Evaluation and Performance Cookbooks

Four recipes about how Jev behaves at scale: batching questions (cost and speed), measuring self-consistency against LLMs without an answer key (Choice and Noul versions), and using Jev's answers as features for a classical model. Each is a runnable notebook and `.py` file in [typesafe-ai/typesafe-public-examples](https://github.com/typesafe-ai/typesafe-public-examples/tree/main/cookbooks). The verbatim pages are in `references/`.

## Parallel questions (`parallel_questions`)

**Claim tested:** asking N questions in one request gives the same answers as N requests with one question each, at a fraction of the cost and time.

**Setup:** the Wikipedia article on the GDPR (~54,000 characters) as state `{"article": ...}`, and a 13-question compliance briefing: 8 Nouls (e.g. "Must a personal data breach be reported to the supervisory authority within 72 hours?"), 2 Choices (`instrument_type`: Regulation / Directive / Treaty / Recommendation; `max_fine`: four fine regimes), 3 Scores (individual rights, penalty severity, compliance burden). Each strategy runs 5 times.

**Results:**

- **Answers don't change:** 7 of 13 answers were identical across all 5 repeats either way (std dev 0.0); the rest moved by at most 0.015 under either strategy. Each question is scored on its own against the document.
- **12.2x cheaper and 11.8x faster** batched. The document dominates every request; N single calls pay for it N times. The bigger the state, the nearer the saving comes to Nx. (The speed figure sums sequential single calls; concurrency narrows the time gap, but the cost gap stays.)

To compare answers across types on one scale, the cookbook tracks `noul`, the top Choice probability, and the Score normalized by `len(criteria) - 1`. Rule of thumb: everything about one state goes in one request ([patterns](../../patterns/SKILL.md), speculative fan-out).

## Self-consistency: choices and nouls (`consistency_choice_cookbook`, `consistency_noul_cookbook`)

**Question:** send the same input repeatedly, unchanged. How often does the **decision** change? This needs no answer key, so every model is measured the same way, and it comes before correctness: if decisions move when inputs don't, appeals can't be reproduced and identical cases get different treatment.

**Method:**

- Borderline inputs: 40 versions of a post (choices) or an auto-insurance claim (nouls), each a different mix of facts.
- Rubrics: **8 Choice questions** (37 options in all) for a moderation post, or **14 Noul questions** for a claim (pay, deny, or send to a human).
- A decision is a cutoff on a probability (e.g. strike when P(Strike) > 0.6). Since your cutoff is unknown, every cutoff from 0 to 1 counts equally: two answers 0.10 apart disagree at 10% of cutoffs. Average over pairs of repeats, and score each input by its **least stable** question (a pipeline is as dependable as its shakiest decision).
- LLMs got the same rubric in one prompt with a JSON-schema structured output for a probability distribution per question: Claude (`claude-fable-5-1`, `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-5-5`) and GPT (`gpt-6-astra`, `gpt-6.1-sol`, `gpt-6.1-terra`, `gpt-6-luna`) at high reasoning effort, plus `gpt-6.1-terra` and `gpt-6-luna` with reasoning off at temperature 0 and default. Jev 1.14: one `system_one` call over the rubric.

**Results:**

| Rubric | Jev: least-stable decision changes, average | Jev: worst input |
| --- | --- | --- |
| 8 Choices (moderation) | 4.0% (about 1 in 25) | 6.7% |
| 14 Nouls (insurance claim) | 3.8% (about 1 in 25) | 8.4% |

For the Noul rubric, the steadiest LLM conditions came close on an average claim (6.2% for GPT-6.1 Terra, 6.4% for Claude Opus 5.5, both reasoning), but each LLM condition had worse inputs. The pages chart every condition, with cost and speed per rubric query.

Use these pages as a template to test reliability on your own borderline inputs before trusting any model with an automated decision.

## Autoresearch feature discovery (`autoresearch_feature_discovery`)

Use Jev's answers as **features** for a classical model, with an LLM discovering the questions:

1. An LLM (the proposer) writes questions about labelled text.
2. Jev answers every question for every row (Nouls and Scores).
3. CatBoost trains on the answers, then reports which questions it used and which rows it still gets wrong.
4. The proposer reads that report and suggests changes. A change is **kept only if it lowers the error on held-out rows** the proposer never reads.

Worked example: predict how polite 2,000 Wikipedia talk-page requests read (each rated by five people). RMSE on 800 never-seen rows (lower is better):

| How the message becomes a rating | RMSE |
| - | - |
| Predict the training mean | 0.788 |
| Control: CatBoost on the raw text | 0.703 |
| Ask Jev for the rating directly, with a fitted line | 0.492 |
| 16 questions from the proposer's first call, no loop | 0.471 |
| **20 questions after five steps of the loop** | **0.456** |

The first call did most of the work. Without being told any politeness research, the proposer wrote questions matching features a 2013 study built by hand (thanks and praise, apologies, hedging, greetings, indirect asks, "we" framing). The loop later added a "please"/courtesy-words question the first call missed, and rejected most other suggestions. When you lack labels, the [designing-with-jev](../../designing-with-jev/SKILL.md) skill suggests generating them with an ensemble of reasoning models.

## Related

- Composite scoring with hand-set weights instead of a learned model: [patterns](../../patterns/SKILL.md).
- Calibration and what probabilities mean: [confidence](../../confidence/SKILL.md).

## Source docs

Verbatim copies, for details not covered above:

- [cookbooks/parallel_questions.md](references/cookbooks-parallel_questions.md)
- [cookbooks/consistency_choice_cookbook.md](references/cookbooks-consistency_choice_cookbook.md)
- [cookbooks/consistency_noul_cookbook.md](references/cookbooks-consistency_noul_cookbook.md)
- [cookbooks/autoresearch_feature_discovery.md](references/cookbooks-autoresearch_feature_discovery.md)
