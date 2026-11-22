---
name: cookbooks
description: 'End-to-end recipes that apply Jev to real problems, from a few questions to full pipelines, grouped by task: LLM guardrails and verification, classification, search and ranking, extraction, vision and documents, agents and LLM apps, evaluation and performance, and demo apps. Use when looking for a worked example or a proven architecture for a task before building one.'
---

# Cookbooks

End-to-end recipes that show Jev on real problems, from a few questions to full pipelines: a real dataset, the System One questions that decide something about it, and the code that turns those decisions into a system. Read one to see how [questions](../questions/SKILL.md), [patterns](../patterns/SKILL.md) and [confidence](../confidence/SKILL.md) come together, or copy one as a starting point.

## Running them

Every cookbook is a Colab notebook and a `.py` file in [github.com/typesafe-ai/typesafe-public-examples](https://github.com/typesafe-ai/typesafe-public-examples/tree/main/cookbooks) (`cookbooks/<name>/<name>.py`). They **replay saved answers** from a JSON cache, so they run as published without an API key. To run live, set `TYPESAFE_API_KEY`, turn off the cache download, and delete the cache file. Most pin `TYPESAFE_MODEL = "jev-1.14.0"`; switch to `jev-latest` for the newest model. Each also has an "Open in playground" link to edit one request live.

Patterns you'll see repeatedly:

- Questions are built in code (loops over records, candidates, rules), serialized with `q.model_dump(mode="json", exclude_none=True)`, and sent in **one request per state**.
- Calls are wrapped in a cache keyed on the state, the question JSON and the model.
- Independent requests run concurrently with a `ThreadPoolExecutor`.
- Thresholds and routing rules live in plain functions that read stored answers, so they can be retuned with **no new API calls**.

## Which cookbook

| Group | Cookbooks | Use when |
| --- | --- | --- |
| [guardrails-and-verification](guardrails-and-verification/SKILL.md) | Guardrails for LLMs, Double-checking citations, Verifying LLM answers against their source, SDE cascade | Screening LLM inputs/outputs, catching hallucinations, cheap-model-first extraction |
| [classification](classification/SKILL.md) | Hierarchical classification, Classification using confidence, Twitch chat filter, Classifying RAG passages | Taxonomies, moderation, falling back to a broader label, gating retrieval |
| [search-and-ranking](search-and-ranking/SKILL.md) | Re-ranking, Infinite cardinality choice, Line-by-line search, Entity alignment | Re-ranking shortlists, finding one in thousands, in-document search, record linkage |
| [extraction](extraction/SKILL.md) | Date extraction, Pre-parsed value extraction, Structure recovery, Shopping cart | Dates, emails/phones/amounts, rebuilding Markdown, orders to carts |
| [vision-and-documents](vision-and-documents/SKILL.md) | Scanned vaccination record, OCR confidence and bounding boxes, Feeder-cam visit log | Scans, OCR checks, camera frames (Box + images) |
| [agents-and-llm-apps](agents-and-llm-apps/SKILL.md) | Function calling, Skill suggestion, Simple memory, Intelliprompter | Tool and argument selection, skill routing, memory, live transcript tracking |
| [evaluation-and-performance](evaluation-and-performance/SKILL.md) | Parallel questions, Self-consistency (choices, nouls), Autoresearch feature discovery | Cost/latency of batching, reliability testing vs LLMs, Jev answers as ML features |
| [demos](demos/SKILL.md) | Airbnb search in Google Sheets, Smart home assistant, Django docs content audit | Complete app ideas |

By difficulty, TypeSafe marks these as **beginner**: citations, answer verification, memory, confidence classification, Twitch filter, dates, pre-parsed values, structure recovery, cart, re-ranking, line-by-line search, entity alignment, Intelliprompter, both self-consistency tests, parallel questions. **Intermediate**: function calling, skill suggestion, guardrails, RAG passages, hierarchical classification, SDE cascade, infinite cardinality, all three image cookbooks. **Advanced**: autoresearch feature discovery.

## Subskills

Read the one that matches your task:

- [guardrails-and-verification](guardrails-and-verification/SKILL.md): Cookbooks for checking LLM inputs and outputs with Jev: screening every message into and out of an LLM app (guardrails with pass, review, block or support thresholds), double-checking citations against the source, verifying an LLM's answer follows from its source paragraphs with Noul questions, and an SDE cascade that extracts with a cheap model, checks each field with Jev and escalates to a reasoning model. Use when adding guardrails, hallucination checks or verification to an LLM pipeline.
- [classification](classification/SKILL.md): Cookbooks for classifying content with Jev: hierarchical classification with parallel beam search over Choice probabilities (patents, retail products, biomedical), classifying SEC filings into 75 industry groups and falling back to a broader division by confidence, a Twitch chat filter (insults, spam, spoilers, questions) with concurrent requests, and classifying RAG passages before they reach the answering model. Use when building a classifier, moderation filter, taxonomy labeller or retrieval filter.
- [search-and-ranking](search-and-ranking/SKILL.md): Cookbooks for search, re-ranking and matching with Jev: re-ranking BM25 shortlists for legal queries, finding one item among thousands (infinite cardinality choice with Noul screening then a Choice), line-by-line semantic search of a document with a Choice over line ids, and knowledge-graph entity alignment that routes record pairs to merge, review or no link. Use when building retrieval, re-ranking, deduplication or record linkage.
- [extraction](extraction/SKILL.md): Cookbooks for extracting structured data with Jev: absolute and relative date extraction resolved and validated in code, pre-parsed value extraction (regex candidates for emails, phones, amounts, then a Choice picks one), structure recovery that rebuilds Markdown from plain text, and a shopping cart built from a natural-language order with a shrinking-options Choice loop. Use when turning unstructured text into fields, values or structure.
- [vision-and-documents](vision-and-documents/SKILL.md): Cookbooks that use Jev on images: reading a scanned vaccination record with Noul, Box and Choice questions, checking OCR-extracted invoice values with Box and Score against a crop, and a bird feeder camera visit log with a Box per frame. Use when processing scans, photos, OCR output or video frames.
- [agents-and-llm-apps](agents-and-llm-apps/SKILL.md): Cookbooks for using Jev inside agents and LLM apps: function calling (mapping natural-language requests to typed functions and closed-set arguments with confidence), skill suggestion for an agent turn from a 194-skill catalog in two requests, a simple memory system where Jev decides what is worth remembering, and the Intelliprompter that ticks off presenter notes from a live transcript. Use when adding tool selection, routing, memory or live tracking to an agent.
- [evaluation-and-performance](evaluation-and-performance/SKILL.md): Cookbooks on measuring and scaling Jev: parallel questions (13 questions batched into one call, 12.2x cheaper and 11.8x faster), self-consistency tests for Choice and Noul decisions compared with LLMs on borderline moderation and insurance cases, and autoresearch feature discovery where an LLM proposes questions, Jev answers them per row, and CatBoost trains on the answers. Use when benchmarking reliability, optimizing cost and latency, or using Jev answers as features for a classical model.
- [demos](demos/SKILL.md): Working demo projects built on Jev: Airbnb listing search from a Google Sheets formula (1,000 listings scored in about a second), a smart home assistant that evaluates user requests, and a content audit of the whole Django documentation in under 5 seconds for $0.10. Use when looking for complete app examples or ideas for what Jev can power.

## Source docs

Verbatim copies, for details not covered above:

- [cookbooks.md](references/cookbooks.md)
