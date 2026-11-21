# iskills

An installable [Agent Skill](https://agentskills.io) that turns API docs into
a **skill tree**: a root `SKILL.md` with the API's core concepts, plus linked
subskills for each task, so agents load only the part of the API they need.

A Python script (`scripts/skilltree.py`) does the deterministic work (fetch
the docs from a folder, a git repo or a website, draw the taxonomy, validate,
package, install) and hands the judgment calls
(planning the tree, writing each skill) to a CLI agent (`claude -p` by default).

## Structure

```
iskills/
├── SKILL.md                 # the skill: how to run the pipeline
├── scripts/
│   ├── skilltree.py         # fetch | map | plan | generate | check | package | install | build
│   └── docsource.py         # fetch: local / git / website docs -> markdown (pandoc)
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

Only [uv](https://docs.astral.sh/uv/) is needed: the script declares its
dependencies inline (PEP 723), and `uv run` fetches them on first use.

```bash
uv run scripts/skilltree.py build ../moonshine/docs/index.md -o build/moonshine
# or from a repo or a docs site (markdown, Sphinx .rst or HTML):
#   build https://github.com/org/lib/tree/main/docs -o build/lib
#   build https://lib.readthedocs.io/en/stable/index.html -o build/lib
uv run scripts/skilltree.py package build/moonshine/moonshine-voice   # -> build/moonshine/moonshine-voice.zip
uv run scripts/skilltree.py install build/moonshine/moonshine-voice.zip --to ~/.claude/skills
```

The zip is a self-contained installer: share it, upload it where skills are
accepted, or install it with `skilltree.py install`.

Or step by step (`map`, `plan`, `generate`, `check`, `package`, `install`), reviewing the
mermaid diagrams `taxonomy.md` and `plan.md` in between. See [SKILL.md](SKILL.md).

## Use it from other projects

Install this skill where your agent finds it in every project (personal
skills directory, below) or in one project (`<project>/.claude/skills/iskills`,
etc.). Then, when a task in that project needs an API with no skill yet
(because you ask for it, or because the agent sees the code depending on
it), the agent fetches the API's docs, builds a skill tree in
`~/.cache/iskills/<api>` and installs it into that project:

```bash
uv run <iskills-dir>/scripts/skilltree.py build https://github.com/org/lib/tree/v1.2/docs \
    -o ~/.cache/iskills/lib --project .
```

`--project` installs into every agent directory the project has (`.claude`,
`.agents`, `.qwen`, ...). Commit the installed skill to share it with the
team. Requirements: `uv` and `git` on the PATH, plus a CLI agent for the
plan and generate steps (`claude -p` by default, `--agent` to change it).

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
`uv add <pkg>` (and add it to the script's inline `# /// script` block too),
run tools with `uv run scripts/<tool>.py`. To add a new tool,
follow [references/adding-tools.md](references/adding-tools.md).

## License

- Code: [AGPL-3.0](LICENSE)
- Documentation and research material: [CC BY-SA 4.0](CC-BY-SA-4.0)