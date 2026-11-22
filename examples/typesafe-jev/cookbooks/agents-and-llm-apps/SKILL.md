---
name: agents-and-llm-apps
description: 'Cookbooks for using Jev inside agents and LLM apps: function calling (mapping natural-language requests to typed functions and closed-set arguments with confidence), skill suggestion for an agent turn from a 194-skill catalog in two requests, a simple memory system where Jev decides what is worth remembering, and the Intelliprompter that ticks off presenter notes from a live transcript. Use when adding tool selection, routing, memory or live tracking to an agent.'
---

# Agents and LLM Apps Cookbooks

Four worked recipes for putting Jev inside an agent or an LLM-powered app: function calling, skill suggestion, a simple memory, and live tracking of a speaker's notes. Each is a runnable notebook and `.py` file in [typesafe-ai/typesafe-public-examples](https://github.com/typesafe-ai/typesafe-public-examples/tree/main/cookbooks) (replaying saved answers, no API key needed). The verbatim pages are in `references/`. Background: [patterns](../../patterns/SKILL.md), [confidence](../../confidence/SKILL.md).

Jev is not the agent's LLM (see the [root skill](../../SKILL.md)). Here it makes the narrow decisions around the agent: which function, which arguments, which skill, what to remember, what's been covered.

## Function calling (`function_calling`)

Turn natural-language trading requests into calls to **ten ordinary typed functions** without changing them. Arguments whose values come from fixed lists (`Literal`s) are **closed sets**, and each becomes a question over exactly those values, so whatever reaches the function is a value it accepts. You add a **spec** describing in plain words what each function and argument means; a `Dispatcher` builds the questions and reads the answers back into a call.

Question building (all in **one request** per command):

- `__tool__`: a Choice over function names, with each function's description.
- Per argument (prefixed `function.argument`): a Choice for a one-of-list argument; one Noul **per member** for a set-valued argument (e.g. `compare_returns.symbols.NVDA`); a Noul for a boolean.
- For optional arguments, a companion Noul `argument?` asks whether the request states it at all. Below 0.5 the argument is omitted.

```python
ROUTE = "__tool__"


def all_questions(spec: Mapping[str, Any], tools: Mapping[str, Callable]) -> dict[str, dict]:
    questions = {
        ROUTE: {
            "type": "choice",
            "instructions": spec["question"],
            "criteria": {n: e["description"] for n, e in spec["functions"].items()},
        }
    }
    for name, fn in tools.items():
        questions.update(questions_for(fn, spec["functions"][name], prefix=f"{name}."))
    return questions
```

Speculative fan-out: arguments for every function are asked even though only the chosen function's are used. The resulting `Call` records every judgement behind it; its **confidence is the minimum** probability across the decisions taken ("one wrong argument is enough to spoil it"), and `weakest()` names the argument to confirm with the user. The page runs fourteen commands and shows how to read the confidence.

## Skill suggestion (`skill_suggestion`)

Agents usually choose skills from an index of truncated descriptions (Hermes cuts them to 60 characters), so similar skills look alike and a list of names invites a guess when none fits. Two Jev requests per turn suggest **at most one** skill, using progressive disclosure:

1. **Rank wide:** one Choice over all 194 skills (name → description), plus Nouls that gate whether the turn needs a skill at all: acts on the user's files or services? would an expert follow a documented procedure? could prose alone satisfy it (inverted)? does it name a specific tool or format?
2. **Rerank the top three** with each skill's full description plus the opening of its instructions: a Choice ("Exactly one of these skills is the right one... Read what each actually does, not just its name.") plus one absolute Noul per candidate ("Does the skill X do the specific thing the user's request asks for?"). If no candidate's fit passes a threshold, suggest nothing.

```python
def rerank_questions(names: tuple[str, ...], excerpt: int) -> dict:
    questions = {
        "which": Choice(
            instructions=RERANK_INSTRUCTIONS, criteria=rerank_criteria(names, excerpt)
        )
    }
    for name in names:
        questions[f"fits::{name}"] = Noul(
            instructions=(
                f"Does the skill '{name}' do the specific thing the user's request asks "
                f"for? It is described as: {BY_NAME[name]['description_full']}"
            )
        )
    return questions
```

The winner goes into one extra system-prompt line for that turn; the agent keeps its index and its own judgement. Over 452 requests with `claude-haiku-4-5-20251001`:

| | Loads the wrong skill | Loads one when nothing fits |
| - | - | - |
| Agent alone | 15.7% | 14.0% |
| **Agent with a Jev suggestion** | **7.9%** | **5.2%** |
| Agent handed the right answer (floor) | 3.2% | 4.1% |

The second request is justified because it needs data (full skill text) that code only fetches after the first answer.

## Simple memory system (`basic_memory`)

Each Jev request sees only its state, so remembered facts must be put there by code. A wrapper `ask_with_memory()` with the same signature and return type as `ask()` (cached, model-pinned `client.system_one`) adds:

- **After each call:** a second request shows Jev the original request plus its answer (`jev_answered`) and asks a **remember** Noul: does the ticket thread state a lasting fact about the customer that should change how future, unrelated tickets are handled? (It is told not to count anything the routing answer says or implies.) At P(yes) ≥ 0.5 the ticket and answer are saved, in a dict keyed by customer ID.
- **Before each call:** the customer's saved tickets and Jev's answers to them are added to the state.

The routing question is a Choice over teams (`cloud_ops`, `selfhosted_linux`, `selfhosted_windows`, `billing`, `enterprise_desk`, `general`, `none_suitable`). A customer who said in August that they self-host on Windows Server writes in September "Dashboards have been really slow since this morning": without memory it goes to the cloud team; with memory, all six later tickets reached the expected teams (three of six without). It is a minimal agent harness: same interface, plus memory.

## Intelliprompter (`intelliprompter`)

Tick off a presenter's talking points as they speak. Every half second, if the cumulative transcript changed, send it as the state with **one Score per unchecked point**:

```python
SCORE_LEVELS = [
    "Not mentioned at all",
    "Briefly or indirectly mentioned",
    "Mentioned directly",
    "Mostly covered",
    "Covered well and with useful detail",
]


def score_question(description: str) -> Score:
    return Score(
        instructions=(
            "How completely has the speaker covered this criterion in `transcript`: "
            f'"{description}"'
        ),
        criteria=SCORE_LEVELS,
    )
```

The SDK numbers levels 0–4; the app adds one for a 1–5 display. A point whose score reaches 2.5 out of 5 (an app threshold, not a Jev confidence) is marked covered, **stays checked**, and is dropped from later requests, so requests shrink as the talk goes on. The live demo pairs speech-to-text (ElevenLabs) with this loop.

## Related

- Guardrails for LLM inputs and outputs, and verifying LLM answers: [guardrails-and-verification](../guardrails-and-verification/SKILL.md).
- Classifying RAG passages before they reach the model: [classification](../classification/SKILL.md).
- Smart home assistant demo: [demos](../demos/SKILL.md).

## Source docs

Verbatim copies, for details not covered above:

- [cookbooks/function_calling.md](references/cookbooks-function_calling.md)
- [cookbooks/skill_suggestion.md](references/cookbooks-skill_suggestion.md)
- [cookbooks/basic_memory.md](references/cookbooks-basic_memory.md)
- [cookbooks/intelliprompter.md](references/cookbooks-intelliprompter.md)
