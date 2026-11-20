# Adding a tool to this skill

## Checklist

1. Create `scripts/<tool_name>.py` (snake_case, executable via
   `python3 scripts/<tool_name>.py`).
2. Follow the tool contract below.
3. Register the tool in `SKILL.md` under `## Tools` with a short description
   and at least one usage example — the agent only discovers tools that are
   documented there.
4. If the tool needs third-party packages: `uv add <pkg>` from the repo root,
   then document running it with
   `uv run --directory <skill-dir> scripts/<tool_name>.py`.
5. Test the tool (see below) before committing.

## Tool contract

- Standard library only when possible; the skill must work without setup.
- `argparse` CLI with a useful `--help`.
- `--json` flag emitting machine-readable output (stable shape: always an
  array or always an object, not both).
- Exit 0 on success, non-zero on failure; error messages go to stderr.
- Accept files as arguments and stdin where it makes sense (`-` convention).
- No network calls or writes outside the paths the user asked about, unless
  the tool's documented purpose requires it.

## Template

```python
#!/usr/bin/env python3
"""One-line purpose."""

import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="what this tool consumes")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    result = {"input": args.input}  # replace with real work

    if args.json:
        json.dump(result, sys.stdout, indent=2)
        print()
    else:
        print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## Testing

```bash
python3 scripts/<tool_name>.py --help
python3 scripts/<tool_name>.py <example-input>
python3 scripts/<tool_name>.py --json <example-input>
echo "piped input" | python3 scripts/<tool_name>.py   # if stdin is supported
```

Verify the exit code (`echo $?`) for both a successful and a failing run.