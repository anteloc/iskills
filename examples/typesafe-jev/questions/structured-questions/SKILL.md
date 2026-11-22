---
name: structured-questions
description: 'Advanced question structure: passing JSON objects or arrays (not just strings) as `instructions`, Choice option descriptions, Score levels and Noul criteria, to separate the question from the data it refers to and encode domain rules and boundary cases. Use when a question needs embedded examples, rules, records or per-option detail that a single string can''t hold.'
---

# Structured Questions

Pass JSON (objects and arrays), not just strings, in a question's `instructions` and `criteria`. System One models are trained to understand structure. Use it to label the parts of a multi-part question, to attach supporting data (a schema, a taxonomy, a database row) as-is instead of serializing it into a string template, and to pin down boundaries between options or levels. Question basics are in [questions](../SKILL.md).

## Where structure is allowed

Each of these fields is an `EntryType` (see [javascript-api](../../reference/javascript-api/SKILL.md)):

| Field | Applies to | Accepted shape |
| - | - | - |
| `instructions` | Choice, Score, Noul, Box | `string`, `object`, `array`, or `null` |
| `criteria` values (option descriptions) | Choice | `string`, `object`, `array`, or `null` |
| `criteria` entries (level descriptions) | Score | `string`, `object`, `array`, or `null` |
| `criteria.true` and `criteria.false` | Noul | `string`, `object`, `array`, or `null` |

Start with strings. Reach for structure:

- **For clarity**, when a question has several parts: labeled keys make each part explicit.
- **When the question needs supporting data** that is already JSON: pass it whole or the relevant subfields.

Field names inside these objects (`question`, `focus`, `what`, `not_for`, `examples`, ...) are **not part of the API and none are reserved**. You choose them; the model reads them, so use short names that label what follows.

## Structured instructions

Put the question in one field and the data it refers to in others. A common shape: one object describes the field being checked, and each question refers to it by key. The same shape can drive a Noul that verifies a value, a Choice that picks one from candidates, and Scores that place a value on a scale. Build one such question per field in a loop and send them all in one request (the SDE cascade in [guardrails-and-verification](../../cookbooks/guardrails-and-verification/SKILL.md) does this; the duplicate-record check in [noul](../noul/SKILL.md) is a full Python example).

Arrays work too, e.g. a list of things to compare:

```json
"instructions": {
  "question": "Does the claimed sender identity conflict with the sending domain?",
  "compare": ["ticket.sender.display_name", "ticket.sender.email"],
  "focus": "Compare the named organization with the email domain."
}
```

## Structured Choice options

### Rubrics that sharpen boundaries

Make each option's description an object saying what the option covers and what it does *not* cover (plus examples), to separate options the model keeps confusing. Example in [choice](../choice/SKILL.md).

### Walking a taxonomy

To classify into a deep taxonomy, ask one Choice per level and walk the tree in code. At each step:

- the **options** are the children of the current node, and
- each option's **value is that child's subtree**, so the model sees what lives under a branch before committing to it.

This matters when the right leaf isn't obvious from the branch name. A water bottle listing might fit `Sporting Goods > Cycling > Bike Bottles & Cages` or `Home & Kitchen > Drinkware > Water Bottles`; showing both subtrees lets the model weigh the listing's emphasis. The answer's `probabilities` tell you whether the split is close enough to explore both branches.

Once a department is chosen, ask the next Choice with that department's children as options and their subtrees as values, and repeat until a leaf. In code, each question's `criteria` is simply the current node of a nested dict. If a subtree is too large, trim it to its direct children plus a sample of leaves. The beam-search version that keeps several paths alive is in [classification](../../cookbooks/classification/SKILL.md).

## Structured Score levels

Each entry in a Score's `criteria` array can be an object, typically with the same fields on every level, such as `what` and `examples`. Measured effect and an example in [score](../score/SKILL.md).

## Structured Noul criteria

When the yes/no boundary is subtle, make `criteria.true` and `criteria.false` objects with a definition and examples on each side. See [noul](../noul/SKILL.md).

The source page's request examples are interactive Playground links that did not survive conversion; the verbatim copy below has the surrounding text only.

## Source docs

Verbatim copies, for details not covered above:

- [primitives/advanced.md](references/primitives-advanced.md)
