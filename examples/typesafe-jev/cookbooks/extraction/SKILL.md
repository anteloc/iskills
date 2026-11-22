---
name: extraction
description: 'Cookbooks for extracting structured data with Jev: absolute and relative date extraction resolved and validated in code, pre-parsed value extraction (regex candidates for emails, phones, amounts, then a Choice picks one), structure recovery that rebuilds Markdown from plain text, and a shopping cart built from a natural-language order with a shrinking-options Choice loop. Use when turning unstructured text into fields, values or structure.'
---

# Extraction Cookbooks

Four worked recipes for turning unstructured text into typed values and structure with Jev. They share one rule: **Jev never generates text**. It chooses among options (date parts, regex candidates, menu items, block types) and code assembles, normalizes and validates. Every character of output comes from the input or from your option lists, and every judgment carries a probability. Each recipe is a runnable notebook and `.py` file in [typesafe-ai/typesafe-public-examples](https://github.com/typesafe-ai/typesafe-public-examples/tree/main/cookbooks). The verbatim pages are in `references/`. Why: Jev is weak at generation and date math (see [designing-with-jev](../../designing-with-jev/SKILL.md)).

## Date extraction (`date_extraction_cookbook`)

`extract_date(document, role)`: given a phrase naming the date you want ("the deadline to return the form"), return a `date` with a confidence, flagging low-confidence reads, parts that don't form a date, and dates the document never states. Handles absolute ("August 14, 2027") and relative ("tomorrow", "next Thursday") dates.

Seven Choices in **one** call read the date's shape and parts; each closed set has an explicit `none` / `out_of_range` option so a missing part is reported, not guessed:

```python
def date_questions(role: str) -> dict[str, Choice]:
    """Seven typed choices that read a date's shape and parts off the text -- no math."""
    absent = "The document does not state this, or it is not this kind of date."
    return {
        "mode": Choice(
            instructions=(
                f"How is {role} written? 'absolute' = a calendar date naming a month (e.g. "
                "'August 14', 'the 3rd of March'); 'relative' = given relative to today (today, "
                "tomorrow, the day after tomorrow, or a named weekday such as 'next Thursday'); "
                "'none' = the document does not state this date."
            ),
            criteria={"absolute": None, "relative": None, "none": None},
        ),
        "month": Choice(
            instructions=f"If {role} is an absolute calendar date, which month is it in?",
            criteria={m: None for m in MONTHS} | {"none": absent},
        ),
        "day": Choice(
            instructions=f"If {role} is an absolute calendar date, which day of the month (1-31)?",
            criteria={str(d): None for d in range(1, 32)} | {"none": absent},
        ),
        # "year": a YEAR_WINDOW of years + "out_of_range" + "none"
        # "day_anchor": today / tomorrow / day_after / weekday / none
        # "weekday": the seven weekdays + none
        # "week_offset": current / next / none
    }
```

Code then resolves the parts (weekday arithmetic, inferring a missing year as this year, bumped to next if well past), validates the date, and takes the **weakest confidence among the parts actually used** as the date's confidence. Below `REVIEW_BELOW` = 0.60, or if it can't be assembled, a person reviews it.

## Pre-parsed value extraction (`pre_parsed_value_extraction_cookbook`)

1. A **recall-tuned regex** finds every candidate (emails, phones, amounts), even with some wrong ones.
2. Jev **picks** which candidate the question asks for. The options *are* the candidate spans, so `choice` is a verbatim copy and Jev cannot invent a value or transpose a digit. Small Choices / Nouls read attributes (currency, country, credit vs charge).
3. Code copies the picked span and normalizes it (e.g. phone to E.164 `+14155550177`, total to `1315.50 USD`).

```python
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\(?\+?\d[\d\s()\-.]{6,}\d")
MONEY_RE = re.compile(r"[$€£¥]\s?\d[\d,]*(?:\.\d{2})?")


@json_cache
def pick(document: str, candidates: list[str], question: str, model: str) -> dict:
    """Jev selects which found span plays the role. Returns {choice, confidence}.

    The options ARE the candidate spans, so ``choice`` is a verbatim copy of one of them (or the
    ``none`` hatch). The model chooses; code owns the string."""
    criteria = {c: None for c in candidates} | {
        NONE: "None of these is the requested value."
    }
    answer = ts.system_one(
        state=document,
        questions={"pick": Choice(instructions=question, criteria=criteria)},
        model=model,
    ).answers["pick"]
    return {"choice": answer.choice, "confidence": answer.confidence}
```

Example question: "Which email address does the sender want their receipt sent to?". Limits: a Choice allows at most 255 options (with more candidates, narrow by section first, as in line-by-line search in [search-and-ranking](../search-and-ranking/SKILL.md)); values without a regex (names) need candidates from a roster, a NER model or an LLM.

## Structure recovery (`autoformat`)

Rebuild Markdown (headings, paragraphs, lists, quotes, code, callouts) from plain text that lost its formatting, in **two sequential requests**:

- **Pass 1, stitch:** one Noul per adjacent pair of lines, all in one request: "Does line L5 pick up mid-sentence, continuing a sentence left unfinished at the end of line L4?". Lines that continue a split sentence are merged into blocks.
- **Pass 2, classify:** one Choice per block (heading, paragraph, list item, quote, code, callout), plus companion questions per block whose answers are read only when relevant: heading level (only for blocks ≤ 90 chars), "is this a step in an ordered sequence?" (Noul), and callout kind. The blocks only exist after pass 1, so this is a justified second request.
- **Direct evidence stays in code:** blank lines and explicit markers (`- `, `1.`, `#`) are read directly and never sent to the model.

```python
def join_question(i: int) -> Noul:
    return Noul(
        instructions=(
            f'Line {line_id(i - 1)} is "{LINES[i - 1]["text"]}" and line {line_id(i)} is '
            f'"{LINES[i]["text"]}". Does line {line_id(i)} pick up mid-sentence, continuing a '
            f"sentence left unfinished at the end of line {line_id(i - 1)}?"
        ),
        criteria=NoulCriteria(
            true="The line starts in the middle of a sentence that began on the previous line - the line break tore the sentence apart",
            false="The line begins a new sentence, item, heading, or thought of its own",
        ),
    )
```

The appendix shows why the wording matters: asking "are these lines part of the same paragraph?" merges differently (and worse) than the literal "mid-sentence" question. State is the document with each line or block tagged by ID.

## Shopping cart (`cart_from_primitives`)

Turn "Can I get a large oat milk latte and a blueberry muffin please" into a structured cart (`latte` with `size: large`, `milk: oat`; `blueberry_muffin`). A Choice returns one value, not a cart, so:

1. **Find the items with a shrinking-options loop:** ask which remaining menu item the order mentions (the first one, if several), save it, remove it from the options, and repeat with the full order until Jev picks `nothing_else`.
2. **Fill the fields:** one request per found item with a Choice per known field (each with an `unspecified` option).

```python
def item_question(remaining: dict[str, dict], found: list[str]) -> Choice:
    """Build one request's question from the items not found yet."""
    already = ", ".join(found) if found else "nothing yet"
    criteria = {name: item["description"] for name, item in remaining.items()}
    criteria[NOTHING_ELSE] = (
        "The order mentions no menu item other than the ones already accounted for."
    )
    return Choice(
        instructions=(
            f"This is a cafe order. Items already accounted for: {already}. "
            "Which remaining menu item does the order mention? If the order mentions more "
            "than one remaining item, choose the one mentioned first."
        ),
        criteria=criteria,
    )


def field_questions(item_name: str) -> dict[str, Choice]:
    questions = {}
    for field, values in MENU[item_name]["fields"].items():
        criteria = {value: None for value in values}
        criteria[UNSPECIFIED] = (
            f"The order does not say which {field} for the {item_name}."
        )
        questions[field] = Choice(
            instructions=f"Which {field} did the order ask for, for the {item_name}?",
            criteria=criteria,
        )
    return questions
```

A `MAX_ITEM_REQUESTS` cap bounds the loop. This is a real-time use case; the page links a demo video.

## Related

- Checking fields a cheap model extracted (SDE cascade): [guardrails-and-verification](../guardrails-and-verification/SKILL.md).
- Function calling with closed-set arguments: [agents-and-llm-apps](../agents-and-llm-apps/SKILL.md).
- Reading values off scans: [vision-and-documents](../vision-and-documents/SKILL.md).

## Source docs

Verbatim copies, for details not covered above:

- [cookbooks/date_extraction_cookbook.md](references/cookbooks-date_extraction_cookbook.md)
- [cookbooks/pre_parsed_value_extraction_cookbook.md](references/cookbooks-pre_parsed_value_extraction_cookbook.md)
- [cookbooks/autoformat.md](references/cookbooks-autoformat.md)
- [cookbooks/cart_from_primitives.md](references/cookbooks-cart_from_primitives.md)
