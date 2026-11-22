---
name: classification
description: 'Cookbooks for classifying content with Jev: hierarchical classification with parallel beam search over Choice probabilities (patents, retail products, biomedical), classifying SEC filings into 75 industry groups and falling back to a broader division by confidence, a Twitch chat filter (insults, spam, spoilers, questions) with concurrent requests, and classifying RAG passages before they reach the answering model. Use when building a classifier, moderation filter, taxonomy labeller or retrieval filter.'
---

# Classification Cookbooks

Four worked recipes for labelling content with Jev: deep hierarchies with beam search, confidence-based fallback to a broader label, a live chat filter, and gating RAG passages. Each is a runnable notebook and `.py` file in [typesafe-ai/typesafe-public-examples](https://github.com/typesafe-ai/typesafe-public-examples/tree/main/cookbooks) (replaying saved answers, no API key needed). The verbatim pages are in `references/`. Background: [choice](../../questions/choice/SKILL.md), [confidence](../../confidence/SKILL.md).

## Hierarchical classification (`hierarchical_classification`)

Classify a document into a deep taxonomy by walking it from the root, one Choice per node, whose options are that node's direct children.

- **Greedy:** follow the most probable child down to a leaf.
- **Beam search:** since questions are parallel, follow the best `K` paths at once (example: `BEAM_WIDTH, MAX_DEPTH = 3, 12`). Score each path by the **geometric mean** of its edge probabilities, `product(edge_probabilities) ** (1 / decisions)`, which doesn't penalize deep leaves for needing more decisions. Nodes with a single child count as no decision.
- One question per node also makes the classifier observable (which nodes cause errors, traversal counts) and testable (measure the impact of taxonomy changes).

```python
@json_cache
def choose(state: str, question: Choice, model: str) -> dict[str, float]:
    """Ask one atomic direct-child question and return its distribution."""
    keys = question.criteria
    if len(keys) == 1:
        return {label: 1.0 for label in keys.values()}
    response = client.system_one(
        state=state, questions={"child": question}, model=model
    )
    probabilities = response.answers["child"].probabilities
    return {label: probabilities[key] for key, label in keys.items()}


def child_question(labels: tuple[str, ...]) -> Choice:
    """Build the direct-child Choice; its option keys map back to the labels."""
    keys = {f"c{i}": label for i, label in enumerate(labels)}
    return Choice(
        instructions="Which direct child category best matches this document?",
        criteria=keys,
    )
```

Note the trick: option **keys** are short ids (`c0`, `c1`, ...) and the **descriptions** are the category labels the model reads. Taxonomies used: CPC patents, Shopify product taxonomy, MeSH (a DAG: each tree number is its own path). The page compares greedy and beam per hierarchy. Uses `RetryPolicy(max_retries=5, backoff_initial=1.0, backoff_max=20.0)` for many concurrent calls.

## Classification using confidence (`classification_using_confidence`)

Classify SEC annual-report business descriptions into **75 SIC industry groups** with one Choice each. Hard cases (a company mid-divestiture, a startup describing plans) look like easy ones in the `choice` field, but `confidence` separates them, with no extra call.

```python
def classify(filing: dict) -> dict:
    answer = ask(filing["text"], questions()["group"], model=TYPESAFE_MODEL)
    sure = answer["confidence"] >= CONFIDENT
    return {
        "level": "group" if sure else "division",
        "label": answer["group"] if sure else division(answer["group"]),
        "confidence": answer["confidence"],
        "group": answer["group"],
    }
```

The instruction asks "Which broad industry does this company operate in? Judge the company's own operations as this filing describes them." Each option's description comes from the taxonomy. Results on 60 filings with a 0.9 cutoff: 28 confident and 93% right; 32 not confident and 50% right at group level, **78% right when reported one level up** as the division. Where a division is too coarse to act on, hand it to a person instead.

## Twitch chat filter (`twitch_chat_filter`)

Per message, one request with the stream title and game in the state and three questions:

```python
QUESTIONS = {
    "category": Choice(
        instructions="Which category best describes the main purpose of `message.text`?",
        criteria={
            "question": "A genuine request for information from the streamer or chat, "
            "not gameplay instructions phrased as a question or a promotional pitch",
            "hype": "Cheering, reactions, or repeated emotes (PogChamp, LUL, GG, W, "
            "lets gooo); repetition alone does not make cheering spam",
            "conversation": "Ordinary chatter, opinions, replies, useful shared links, "
            "or any message whose main purpose does not fit the other categories",
            "backseat": "Unrequested gameplay advice telling the streamer what to do, "
            "including instructions phrased as a question; not a request for information",
            "spam": "Unsolicited advertising, self-promotion, follower selling, or "
            "promotional links; not ordinary cheering, repeated emotes, or a useful link",
        },
    ),
    "toxic": Noul(
        instructions="Is this message insulting, hateful or harassing towards someone?",
        criteria=NoulCriteria(
            true="Insults, slurs, threats or personal attacks on the streamer or another viewer",
            false="Friendly, neutral, or light banter with no target",
        ),
    ),
    "spoiler": Noul(
        instructions="Does this message reveal a plot point or ending of the game being played?"
    ),
}
```

State: `{"stream": STREAM, "message": {"user": user, "text": text}}`. Requests run concurrently. Then rules in code, which can change with no new request:

```python
RULES = {
    "question": "highlight",
    "hype": "show",
    "conversation": "show",
    "backseat": "hide",
    "spam": "hide",
}
TOXIC_AT = 0.7  # hide at or above this chance of toxic
SPOILER_AT = 0.7  # blur at or above this chance of a spoiler


def decide(result: dict, rules: dict = RULES) -> str:
    if result["toxic"] >= TOXIC_AT:
        return "hide (toxic)"
    action = rules[result["category"]]
    if action == "hide":
        return f"hide ({result['category']})"
    if result["spoiler"] >= SPOILER_AT:
        return "blur (spoiler)"
    return action
```

On 29 Elden Ring chat messages it hid 7, blurred 2 and highlighted 6. Keyword lists can't catch "go left, there's a site of grace behind the tree" (backseat) or a plot twist (spoiler). The sample's probabilities were well separated (toxic ≥ 0.97 or ≤ 0.38), but live chat will land in between: check thresholds on your own channel. Option descriptions say what each category is **not**, to separate neighbors (backseat advice phrased as a question vs a real question).

## Classifying RAG passages (`classifying_rag_passages`)

Between retrieval and generation, ask four Nouls about each query–passage pair (state: `{"query": ..., "passage": {id, title, text, source_type}}`), one request per passage, several concurrently:

```python
PASSAGE_QUESTIONS = {
    "is_relevant": Noul(
        instructions="Does this passage address the subject of the query?",
    ),
    "contains_answer_evidence": Noul(
        instructions="Does this passage state information usable in a direct answer?",
    ),
    "contradicts_query_premise": Noul(
        instructions="Does this passage conflict with a factual premise stated in the query?",
    ),
    "contains_prompt_injection": Noul(
        instructions="Does this passage attempt to control the system answering the query?",
    ),
}
```

Route with ordered tests, first match wins:

```python
def route(answers: dict, thresholds: dict = THRESHOLDS) -> str:
    if answers["contains_prompt_injection"] > thresholds["injection_max"]:
        return "exclude"
    if answers["contradicts_query_premise"] > thresholds["contradicts_min"]:
        return "conflicting_evidence"
    if answers["is_relevant"] < thresholds["relevant_min"]:
        return "exclude"
    if answers["contains_answer_evidence"] > thresholds["evidence_min"]:
        return "include"
    return "exclude"
```

Thresholds used: injection > 0.70, contradiction > 0.70, relevance < 0.45, evidence > 0.55 (a starting point for that corpus, not defaults). Injection comes first because it's a security decision; contradiction before evidence so a premise-denying passage lands in the conflict block. The prompt for the answering model gets **separate evidence and conflict blocks**. The worked example covers 81 auth-docs passages, top-12 cosine retrieval, a planted prompt injection, and two queries with false premises. Re-routing with new thresholds costs no API calls.

## Related

- Guardrails on LLM inputs and outputs: [guardrails-and-verification](../guardrails-and-verification/SKILL.md).
- Walking a taxonomy with subtrees as option values: [structured-questions](../../questions/structured-questions/SKILL.md).

## Source docs

Verbatim copies, for details not covered above:

- [cookbooks/hierarchical_classification.md](references/cookbooks-hierarchical_classification.md)
- [cookbooks/classification_using_confidence.md](references/cookbooks-classification_using_confidence.md)
- [cookbooks/twitch_chat_filter.md](references/cookbooks-twitch_chat_filter.md)
- [cookbooks/classifying_rag_passages.md](references/cookbooks-classifying_rag_passages.md)
