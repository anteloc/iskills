# iskills

An installable [Agent Skill](https://agentskills.io) that turns API docs into
a **skill tree**: a root `SKILL.md` with the API's core concepts, plus linked
subskills for each task, so agents load only the part of the API they need.

A Python script (`scripts/skilltree.py`) does the deterministic work (fetch
the docs from a folder, a git repo or a website, draw the taxonomy, validate,
package, install) and hands the judgment calls
(planning the tree, writing each skill) to a CLI agent (`claude -p` by default).

## Install into a project

From the project's root:

```bash
curl -fsSL https://raw.githubusercontent.com/anteloc/iskills/master/install.sh | sh
```

That's it. It copies the skill into every agent directory the project
already has (`.claude/`, `.agents/`, `.qwen/`, `.codex/`, `.gemini/`,
`.opencode/`; `.claude/` if none), and pre-loads the script's dependencies.
Start a new agent session and ask for an API skill, e.g. *"make a skill for
the mujoco API and install it in this project"*. The agent also offers to do
it by itself when the code starts using an API it has no skill for. It
fetches the docs, builds the skill tree in `~/.cache/iskills/<api>`, and
installs it next to iskills in the project. Commit both to share them with
your team.

Options go after `sh -s --`:

| Option | Does |
| --- | --- |
| `DIR` | install into that project instead of the current directory |
| `--global` | install into your personal skill directories (`~/.claude/skills`, ...) for all projects |
| `--agent NAME` | pick the agent directory (`claude`, `agents`, `qwen`, ...; repeatable) |
| `--ref REF` | install a branch, tag or commit (default: `master`) |
| `--force` | replace an `iskills/` folder the installer did not create |

```bash
curl -fsSL https://raw.githubusercontent.com/anteloc/iskills/master/install.sh | sh -s -- --global
```

Run it again to update. From a clone, `./install.sh <project-dir>`
installs that clone instead of downloading.

**Requirements:** [uv](https://docs.astral.sh/uv/) (it runs the scripts and
fetches their dependencies itself), `git` (to fetch docs from repositories),
and a CLI agent for the plan and generate steps (`claude -p` by default; the
skill tells the agent how to pass its own command). Only the runtime files are
installed (`SKILL.md`, `scripts/`, `references/`, licenses), not the examples.

Other ways: `npx skills add anteloc/iskills`, or clone this repo into a skills
directory (`git clone https://github.com/anteloc/iskills ~/.claude/skills/iskills`).

## Use the script directly

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