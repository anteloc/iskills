---
name: demos
description: 'Working demo projects built on Jev: Airbnb listing search from a Google Sheets formula (1,000 listings scored in about a second), a smart home assistant that evaluates user requests, and a content audit of the whole Django documentation in under 5 seconds for $0.10. Use when looking for complete app examples or ideas for what Jev can power.'
---

# Demos (Made with Jev)

Three working projects built on Jev, and how each groups its questions into requests and what its code does with the answers. They are complete-app ideas; for step-by-step runnable code, see the sibling cookbooks. The verbatim pages (including the Apps Script and Python sources they show) are in `references/`.

## Airbnb listing search in Google Sheets

Describe a stay in plain English ("6 people and a dog on the beach") and get the 10 best of 1,000 Cape Town listings, scored out of 10, in about a second, from a spreadsheet formula: `=JEV_TOP10(B2, Listings!A2:H1001)`.

- **Why Jev:** filters cover price and bedrooms, not "allows dogs" or "has backup power for load-shedding"; those details are in free-text descriptions. Matching is a quick reading judgment that returns a sortable number.
- **The constraint:** 1,000 sequential one-listing requests take over 30 seconds, and Google Sheets stops custom formulas at 30 seconds.
- **Shortlist, then score: 11 requests instead of 1,000.**

| Step | Requests | Question | Then |
| - | - | - | - |
| Shortlist | 10, in parallel | A Choice over **100 listing IDs**, each described by the start of its description: "Which listing best matches the request?" | Keep the 5 most probable per group (50 total) |
| Score | 1 | One Score per shortlisted listing, with the full description, five levels from "Not a match at all" to "Matches everything asked for" | Convert each score to a mark out of 10; return the top 10 |

The sheet caches results per request. Setup: paste the Apps Script, add `TYPESAFE_API_KEY` under Script properties (anyone with edit access to the copy can see the key).

## Smart home assistant

An assistant for requests like "Turn off all of the lights in the house", demonstrating **speculative fan-out**: each request is evaluated against a long list of Choice questions in one call (request category, domain/area, device type, action per device type), most of which are irrelevant for any one request and ignored by code.

- The sequential alternative (category first, then domain and device, then action) asks fewer questions but is much slower and more expensive than one upfront call.
- **Jev and LLM pairing:** an LLM is called only where generated text is needed. A Noul detects compound requests ("more than one distinct action"), and an LLM splits them into atomic commands; when Jev classifies a request as general information or chat, an LLM writes the reply.
- A Vite/React single-page app; TypeSafe plans to open-source the code.

## Content audit of the Django docs

Audit all 279 pages (584,234 words) of the Django documentation in under 5 seconds for $0.10: one request per page with **45 questions**:

| Questions | Type | Measures |
| - | - | - |
| 8 | Score | Quality: overall, accuracy, freshness, clarity, completeness, structure, examples, spelling and grammar |
| 5 | Score, Choice, Noul | Importance: how much the page matters, expected traffic, whether newcomers or AI assistants read it |
| 7 | Choice | Classification: Divio type, level, complexity, length, fix effort, who can fix it, best single fix |
| 21 | Noul | Problems: out of date, incorrect facts, deprecated APIs, typos, broken markup, insecure examples, missing examples, ... |
| 4 | Noul | Quick wins: one small edit, content to delete, needs cross-links |

- Parallel evaluation: on one page, the median request took 144 ms with 1 question and 151 ms with all 45. Questions add cost (their text is input tokens), not much time.
- Results plotted on an importance × quality grid to find low-quality, high-importance pages; flags counted across pages (e.g. 28 pages show a deprecated API).
- **Deep scan:** a follow-up asks which sentence holds each problem and highlights it (e.g. "it's" → "its"), linking to the line on GitHub.
- The page includes a cut-down `audit.py` that asks 7 of the 45 questions, 12 pages at a time, and lists the 20 highest-priority pages.

## Related

- Speculative fan-out and composite scores: [patterns](../../patterns/SKILL.md).
- Search and re-ranking recipes: [search-and-ranking](../search-and-ranking/SKILL.md).
- Batching many questions per request: [evaluation-and-performance](../evaluation-and-performance/SKILL.md).

## Source docs

Verbatim copies, for details not covered above:

- [demos.md](references/demos.md)
- [demos/airbnb-listing-search.md](references/demos-airbnb-listing-search.md)
- [demos/smart-home.md](references/demos-smart-home.md)
- [demos/content-audit.md](references/demos-content-audit.md)
