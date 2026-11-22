---
name: search-and-ranking
description: 'Cookbooks for search, re-ranking and matching with Jev: re-ranking BM25 shortlists for legal queries, finding one item among thousands (infinite cardinality choice with Noul screening then a Choice), line-by-line semantic search of a document with a Choice over line ids, and knowledge-graph entity alignment that routes record pairs to merge, review or no link. Use when building retrieval, re-ranking, deduplication or record linkage.'
---

# Search and Ranking Cookbooks

Four worked recipes for finding and matching things with Jev: re-ranking a keyword shortlist, finding one item among thousands, searching a long document line by line, and aligning records across two sources. Each is a runnable notebook and `.py` file in [typesafe-ai/typesafe-public-examples](https://github.com/typesafe-ai/typesafe-public-examples/tree/main/cookbooks) (replaying saved answers, no API key needed). The verbatim pages are in `references/`.

Common idea: use the **probability itself** to sort, not just a threshold, and fan many independent calls out in parallel (a thread pool) because each is cheap and fast.

## Re-ranking (`rerank_typesafe`)

Two-step search: a fast method (here BM25) cuts thousands of documents to a shortlist; Jev scores **each query–candidate pair** with one Noul and the shortlist is sorted by `noul`.

```python
is_cited_source = Noul(
    instructions=(
        "The query excerpt comes from a US federal court opinion and was written "
        "immediately around a citation to a precedent; the citation itself has been "
        "removed. Could the candidate passage be from that cited precedent — does it "
        "establish the specific legal proposition the query excerpt invokes at its "
        "citation point?"
    ),
    criteria=NoulCriteria(
        true=(
            "The candidate passage states or establishes the specific rule, standard, "
            "holding, or fact pattern that the query excerpt attributes to its removed "
            "citation."
        ),
        false=(
            "The candidate passage is merely on a similar topic or doctrine; it does not "
            "supply the specific proposition the query excerpt relies on."
        ),
    ),
)

# state={"query_excerpt": query, "candidate_passage": candidate}
reranked = {
    q: sorted(candidates[q], key=lambda c: -pair_scores[q][c]["noul"]) for q in queries
}
```

On 40 CLERC legal queries with 30-passage BM25 shortlists from 3,565 court-opinion passages (1,200 independent calls through a 12-worker thread pool): top-1 accuracy rose from 5% to **30%**, top-10 from 38% to **65%**. The `false` criterion ("merely on a similar topic") is what separates the right passage from look-alikes.

## Infinite cardinality choice (`infinite_cardinality_choice`)

A Choice takes at most 255 options (only about forty when each option is a long text). To find one film among **5,000** from someone's vague description, read more about fewer candidates in three steps:

1. **Filter:** one Noul per film ("The film this person is trying to remember is X. Its plot: <first 100 words>"), sent in chunks of questions, all chunks at once. Latency stays flat as the catalog grows, rate limits permitting.
2. **Re-read** the top 80 with 600-word plots.
3. **Decide** with one Choice over the top 20, whose option descriptions are the long plots.

```python
def proposition(film_id: str, plot: str = "plot") -> str:
    return (
        f"The film this person is trying to remember is {label(film_id)}. "
        f"Its plot: {FILMS[film_id][plot]}"
    )


DECISION = "Which film is this person trying to remember?"


def decision_question(options: tuple[str, ...]) -> dict:
    return {
        "film": Choice(
            instructions=DECISION,
            criteria={key: f"{label(key)}: {FILMS[key]['long_plot']}" for key in options},
        )
    }
```

Note the state is the person's description and the **candidates go in the questions**, so one state serves thousands of Nouls. On 100 real forum requests, the right film came first **78%** of the time with all three steps vs 33% when embedding search built the 20-film shortlist. Every time the Choice's top probability was ≥ 0.8 (48 cases), it was right: show one film above that, a short list below.

## Line-by-line search (`semantic_find`)

Semantic search inside one document (GitHub's Terms of Service, 218 clauses), in **one request**:

1. Tag each line with an ID in the state.
2. A Choice whose options are **the line IDs** (no descriptions) ranks lines by how well they answer the query.
3. A Noul in the same request checks whether the document answers it at all.

```python
def where_question(query: str) -> Choice:
    return Choice(
        instructions=f'Which line of the document contains the answer to: "{query}"?',
        criteria={line_id(i): None for i in range(len(LINES))},
    )


def exists_question(query: str) -> Noul:
    return Noul(
        instructions=f'Does any line of the document address or answer: "{query}"?',
        criteria=NoulCriteria(
            true="At least one line of the document states or directly implies the answer",
            false="No line of the document addresses this",
        ),
    )


@json_cache
def _find(
    state: str,
    where: Choice,
    exists: Noul,
    model: str,
) -> dict:
    response = client.system_one(
        state=state,
        questions={"where": where, "exists": exists},
        model=model,
    )
    probabilities = response.answers["where"].probabilities
    return {
        "exists": response.answers["exists"].noul,
        "relevance": [probabilities.get(line_id(i), 0.0) for i in range(len(LINES))],
    }
```

The per-line probabilities act as relevance scores; the `exists` Noul is a companion that labels the document answered, partly answered, or not answered (a Choice always picks some line).

## Knowledge graph entity alignment (`entity_alignment`)

Decide whether two records (from Wikidata and MusicBrainz) describe the same album, with **one Score whose levels are the outcomes**, plus three field-level Nouls for explanation:

```python
LEVELS = [
    "They describe two different albums.",
    "They describe closely related albums that may or may not be the same one: "
    "a reissue, a compilation, a special or live edition, or a title that could "
    "plausibly refer to either.",
    "They describe one and the same album.",
]
OUTCOME = {0: "leave unlinked", 1: "curator queue", 2: "assert sameAs"}

QUESTIONS = {
    "link_state": Score(
        instructions="How do the two entity descriptions relate as albums?",
        criteria=LEVELS,
    ),
    "same_title": Noul(
        instructions="Do the two entities give the same album title? Differences in "
        "casing, punctuation, or writing system (a title and its romanisation) do not "
        "make two titles different.",
    ),
    "same_artist": Noul(
        instructions="Do the two entities credit the same artist? A name written in "
        "another script or word order, or a credit that adds collaborators to the same "
        "lead artist, is the same artist.",
    ),
    "same_label": Noul(
        instructions="Do the two entities name the same record label? A shortened name "
        "or a regional branch of a label is the same label; an imprint and its parent "
        "company are different labels. A label of '-' or '[no label]' is not recorded.",
    ),
}
```

State: `{"entity_a": ..., "entity_b": ...}`. Routing rounds the score to the **nearest level**, which names the outcome. On 450 album pairs: 57 merge recommendations (48 recorded as matches in the dataset), 79 to a curator, 314 left unlinked. The middle level gives ambiguous cases (reissues, compilations) somewhere to go other than a wrong merge. The Nouls spell out what "same" means for each field (scripts, branches, imprints).

## Related

- Classifying retrieved passages for RAG: [classification](../classification/SKILL.md).
- Ranking skills for an agent: [agents-and-llm-apps](../agents-and-llm-apps/SKILL.md).
- Airbnb listing search from a spreadsheet: [demos](../demos/SKILL.md).

## Source docs

Verbatim copies, for details not covered above:

- [cookbooks/rerank_typesafe.md](references/cookbooks-rerank_typesafe.md)
- [cookbooks/infinite_cardinality_choice.md](references/cookbooks-infinite_cardinality_choice.md)
- [cookbooks/semantic_find.md](references/cookbooks-semantic_find.md)
- [cookbooks/entity_alignment.md](references/cookbooks-entity_alignment.md)
