# iskills

An installable [Agent Skill](https://agentskills.io) that turns API docs into
a **skill tree**: a root `SKILL.md` with the API's core concepts, plus linked
subskills for each task, so agents load only the part of the API they need.

A Python script (`scripts/skilltree.py`) does the deterministic work (fetch
the docs from a folder, a git repo or a website, draw the taxonomy, validate,
package, install) and hands the judgment calls
(planning the tree, writing each skill) to a CLI agent (`claude -p` by default).

## Requirements

- [uv](https://docs.astral.sh/uv/): runs the scripts and fetches their dependencies
- `git`: fetches docs from repositories
- a CLI agent for the plan and generate steps (`claude -p` by default)

Install uv if you don't have it:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Installation

### Method 1: installer, into one project (recommended)

Run from the root of your project:

```sh
curl -fsSL https://raw.githubusercontent.com/anteloc/iskills/master/install.sh | sh
```

It copies the skill into each agent directory the project has (`.claude/`,
`.agents/`, `.qwen/`, `.codex/`, `.gemini/`, `.opencode/`), or `.claude/` if
there is none. Run it again to update.

To pick the agent directory, e.g. Qwen Code:

```sh
curl -fsSL https://raw.githubusercontent.com/anteloc/iskills/master/install.sh | sh -s -- --agent qwen
```

### Method 2: installer, for all your projects

Installs into your personal skill directories (`~/.claude/skills/`, ...):

```sh
curl -fsSL https://raw.githubusercontent.com/anteloc/iskills/master/install.sh | sh -s -- --global
```

### Method 3: skills CLI

```sh
npx skills add anteloc/iskills
```

### Method 4: git clone

Into one project (Claude Code):

```sh
git clone --depth 1 https://github.com/anteloc/iskills .claude/skills/iskills
```

Or for all projects:

```sh
git clone --depth 1 https://github.com/anteloc/iskills ~/.claude/skills/iskills
```

For other agents, replace `.claude` with `.agents`, `.qwen`, ...

### Installer options

Pass them after `sh -s --`:

| Option | Does |
| --- | --- |
| `DIR` | install into that project instead of the current directory |
| `--global` | install into your personal skill directories |
| `--agent NAME` | agent directory: `claude`, `agents`, `qwen`, `codex`, `gemini`, `opencode` (repeatable) |
| `--ref REF` | install a branch, tag or commit (default: `master`) |
| `--force` | replace an `iskills/` folder the installer did not create |

## Usage

Start a new agent session in the project and ask, for example:

> make a skill for the mujoco API and install it in this project

The agent fetches the docs, builds the skill tree in `~/.cache/iskills/<api>`
and installs it in the project. It also offers to do this by itself when your
code starts using an API it has no skill for. Commit the installed skills to
share them with your team.

## Use the script directly

Only [uv](https://docs.astral.sh/uv/) is needed: the script declares its
dependencies inline (PEP 723), and `uv run` fetches them on first use.

```sh
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

## Structure

```
iskills/
├── SKILL.md                 # the skill: how to run the pipeline
├── install.sh               # one-line installer into a project
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

## Develop

This is a [uv](https://docs.astral.sh/uv/) project: add dependencies with
`uv add <pkg>` (and add it to the script's inline `# /// script` block too),
run tools with `uv run scripts/<tool>.py`. To add a new tool,
follow [references/adding-tools.md](references/adding-tools.md).

## License

- Code: [AGPL-3.0](LICENSE)
- Documentation and research material: [CC BY-SA 4.0](CC-BY-SA-4.0)