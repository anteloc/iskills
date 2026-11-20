# iskills

An installable [Agent Skill](https://agentskills.io) with bundled Python
tools. The repo root is the skill itself: `SKILL.md` defines it, `scripts/`
holds the tools, and `references/` holds supporting docs the agent loads on
demand.

This is a scaffold — it ships one working example tool (`text_stats`) and the
conventions for adding more.

## Structure

```
iskills/
├── SKILL.md                 # skill definition (frontmatter + tool docs)
├── scripts/
│   └── text_stats.py        # example tool: line/word/character counts
├── references/
│   └── adding-tools.md      # how to add and register new tools
├── pyproject.toml           # uv project (for tools that need dependencies)
├── LICENSE                  # AGPL-3.0 (code)
└── CC-BY-SA-4.0             # CC BY-SA 4.0 (documentation/research)
```

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

## Use the tools directly

The example tool is standard-library-only (Python 3.10+):

```bash
python3 scripts/text_stats.py README.md SKILL.md
cat notes.txt | python3 scripts/text_stats.py
python3 scripts/text_stats.py --json README.md
```

## Develop

This is a [uv](https://docs.astral.sh/uv/) project. Tools with third-party
dependencies are managed with `uv add <pkg>` and run with `uv run`:

```bash
uv sync
uv run scripts/text_stats.py README.md
```

To add a new tool, follow [references/adding-tools.md](references/adding-tools.md).

## License

- Code: [AGPL-3.0](LICENSE)
- Documentation and research material: [CC BY-SA 4.0](CC-BY-SA-4.0)