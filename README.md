# iskills

An installable [Agent Skill](https://agentskills.io) that turns API docs into
a **skill tree**: a root `SKILL.md` with the API's core concepts, plus linked
subskills for each task, so agents load only the part of the API they need.

A Python CLI (`scripts/skilltree.py`) does the deterministic work (crawl the
docs, draw the taxonomy, validate, install) and hands the judgment calls
(planning the tree, writing each skill) to a CLI agent (`claude -p` by default).

## Structure

```
iskills/
├── SKILL.md                 # the skill: how to run the pipeline
├── scripts/
│   └── skilltree.py         # CLI: map | plan | generate | check | install | build
├── references/
│   ├── planning.md          # agent rules: docs taxonomy -> skill tree plan
│   ├── writing.md           # agent rules: writing one SKILL.md
│   └── adding-tools.md      # how to add and register new tools
├── examples/moonshine/      # worked example on the Moonshine Voice docs
├── pyproject.toml           # uv project
├── LICENSE                  # AGPL-3.0 (code)
└── CC-BY-SA-4.0             # CC BY-SA 4.0 (documentation/research)
```

## Quick start

```bash
uv sync
uv run scripts/skilltree.py build ../moonshine/docs/index.md -o build/moonshine
uv run scripts/skilltree.py install build/moonshine/moonshine-voice --to ~/.claude/skills
```

Or step by step (`map`, `plan`, `generate`, `check`, `install`), reviewing the
mermaid diagrams `taxonomy.md` and `plan.md` in between. See [SKILL.md](SKILL.md).

## Install

### With the skills CLI

```bash
npx skills add anteloc/iskills
```

### Manually

Clone (or copy) this repo into your agent's skills directory as `iskills`:

```bash
git clone git@github.com:anteloc/iskills.git ~/.agents/skills/iskills
```

Common skill directories:

| Agent       | Personal (all projects)   | Project-local        |
|-------------|---------------------------|----------------------|
| Shared      | `~/.agents/skills/`       | `.agents/skills/`    |
| Qwen Code   | `~/.qwen/skills/`         | `.qwen/skills/`      |
| Claude Code | `~/.claude/skills/`       | `.claude/skills/`    |

A symlink works too, so one checkout serves every agent:

```bash
ln -s "$(pwd)" ~/.qwen/skills/iskills
```

## Develop

This is a [uv](https://docs.astral.sh/uv/) project: add dependencies with
`uv add <pkg>`, run tools with `uv run scripts/<tool>.py`. To add a new tool,
follow [references/adding-tools.md](references/adding-tools.md).

## License

- Code: [AGPL-3.0](LICENSE)
- Documentation and research material: [CC BY-SA 4.0](CC-BY-SA-4.0)