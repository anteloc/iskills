---
name: iskills
license: AGPL-3.0
description: >
  Turn a set of API docs (markdown, e.g. a mkdocs site) into an installable
  tree of agent skills: a root SKILL.md with the API's core concepts and
  linked subskills for each task, so agents load only the part of the API a
  task needs. Use when the user wants to make a skill from API documentation,
  convert docs into skills or subskills, map a docs taxonomy, or install a
  generated skill tree.
---

# iskills: API docs → skill tree

Large API docsets bloat an agent's context and mix concerns. This skill
turns a docs tree into a **skill tree** that agents navigate like a person
navigates the docs: start at the root, open only the subskill for the task.

Run the script with [uv](https://docs.astral.sh/uv/); it declares its own
dependencies inline, so there is nothing to install first:

```bash
uv run <skill-dir>/scripts/skilltree.py <command> ...
```

It runs from any directory, so relative paths for the docs and `--out` are
relative to where you run it.

## Pipeline

Every step reads and writes files in a workspace (`-o/--out`, default
`build/`), so you can stop, review or hand-edit between steps.

| Step | Command | Writes | Who |
| --- | --- | --- | --- |
| 1. Map | `map <root.md>` | `taxonomy.json`, `taxonomy.md` | script |
| 2. Plan | `plan` | `plan.json`, `plan.md` | agent |
| 3. Generate | `generate` | `<skill-name>/**/SKILL.md` | agent |
| 4. Check | `check <out>/<skill-name>` | report | script |
| 5. Package | `package <out>/<skill-name>` | `<skill-name>.zip` | script |
| 6. Install | `install <dir-or-zip> --to <skills-dir>` | skill copy | script |

`build <root.md> [--install <skills-dir>]` runs 1-4 (and 6) in one go.

```bash
uv run <skill-dir>/scripts/skilltree.py map docs/index.md -o work
uv run <skill-dir>/scripts/skilltree.py plan -o work
uv run <skill-dir>/scripts/skilltree.py generate -o work
uv run <skill-dir>/scripts/skilltree.py check work/<skill-name>
uv run <skill-dir>/scripts/skilltree.py package work/<skill-name>  # -> work/<skill-name>.zip
uv run <skill-dir>/scripts/skilltree.py install work/<skill-name>.zip --to ~/.claude/skills
```

All commands accept `--json`, and exit non-zero on failure.

### 1. Map

Crawls the docs from the root doc. If a `mkdocs.yml` with a `nav:` sits above
the root, its nav is the hierarchy (the authors' own). Otherwise the script
follows local `.md` links breadth-first. Show the user `taxonomy.md` (a
mermaid diagram) before planning.

### 2. Plan

An agent groups the docs into a skill tree following
[references/planning.md](references/planning.md): root = core concepts, one
subskill per task, reference pages in their own branch, non-usage pages
(license, support, ...) left out. Review `plan.md` with the user. Edit
`plan.json` by hand when needed: `generate` re-validates it.

### 3. Generate

An agent writes each node in parallel (`-j`, default 4) following
[references/writing.md](references/writing.md), from that node's source docs.
The script adds the frontmatter, a linked **Subskills** list, and verbatim
copies of the source docs under `references/`. Rewrite single nodes with
`--only <name> ...`. To regenerate from scratch, delete `<out>/<skill-name>`
first (`generate` does not remove skills that left the plan).

### 4. Check

Runs the official [`skills-ref`](https://agentskills.io) validator on every
SKILL.md, then checks local links, the 500-line limit, and that every
subskill is linked from its parent. Fix problems with `generate --only` or by
editing the file.

### 5. Package

Checks the tree (as in step 4), then zips it into a single installer with
one top-level `<skill-name>/` folder (`-o` sets the zip path). That is the
layout skill upload forms expect, and what `install` accepts, so share the
zip instead of a folder.

### 6. Install

Only when the user asks. Installs a skill directory or a `package` zip into a
skills directory (`--to`, default `~/.agents/skills`; Claude Code uses
`~/.claude/skills`). Refuses to overwrite unless `--force`.

## Choosing the agent

Agent steps pipe a prompt to any CLI agent on stdin and read its answer on
stdout: `claude -p` by default. Override with `--agent "<command>"` or the
`SKILLTREE_AGENT` environment variable.

You can also do steps 2 and 3 yourself, without the CLI: read
`taxonomy.json`, write `plan.json` (`{"docs_dir": ..., "skill": {...}}`, with
`docs_dir` relative to the workspace, as `map` writes it) following
references/planning.md, then write each SKILL.md following
references/writing.md, and finish with `check`.

## Output layout

```
<out>/
├── taxonomy.json / taxonomy.md   docs tree (+ mermaid)
├── plan.json / plan.md           skill tree (+ mermaid)
└── <api-name>/                   the skill to install
    ├── SKILL.md                  core concepts + Subskills list
    ├── references/               verbatim source docs
    └── <task>/SKILL.md           subskill, same shape, nested
```

Subskills are plain SKILL.md files in subdirectories, linked from their
parent. Agents discover only the root skill and follow the links on demand.

Worked example: [examples/moonshine/](examples/moonshine/) (Moonshine Voice).

## Adding tools

See [references/adding-tools.md](references/adding-tools.md).
