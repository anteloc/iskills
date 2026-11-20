---
name: iskills
license: AGPL-3.0
description: >
  Installable skill scaffold with bundled Python tools. Includes text_stats,
  which counts lines, words, and characters in files or piped stdin, with
  optional JSON output. Use when the user asks for text or file statistics
  (line, word, or character counts), or when adding new tools to this skill.
---

# iskills

An installable agent skill with bundled command-line tools. All paths below
are relative to this skill's directory.

## Tools

### text_stats

Count lines, words, and characters in one or more files, or in stdin.
Standard library only — run it with any Python 3.10+.

```bash
# One or more files
python3 scripts/text_stats.py README.md SKILL.md

# Piped input
cat notes.txt | python3 scripts/text_stats.py

# Machine-readable output (JSON array, one object per source)
python3 scripts/text_stats.py --json README.md
```

Exit code is 0 on success, 1 if any input could not be read (details on
stderr).

## Adding tools

See [references/adding-tools.md](references/adding-tools.md) for the tool
conventions and the checklist for registering a new tool in this skill.

## Conventions

- Prefer standard-library-only scripts so the skill works without setup.
- When a tool needs third-party packages, add them with `uv add <pkg>` and
  run the tool with `uv run --directory <skill-dir> scripts/<tool>.py`.
- Every tool supports `--help` and `--json`, and exits non-zero on failure.