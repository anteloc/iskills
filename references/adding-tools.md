# Adding a tool to this skill

Tools are subcommands of [scripts/skilltree.py](../scripts/skilltree.py), a
self-contained script: it declares its dependencies inline (PEP 723), so
`uv run <skill-dir>/scripts/skilltree.py <command>` works with no install or
sync step. Keep it that way: no packaging, no entry points.

## Checklist

1. Write a `cmd_<name>(args) -> dict` function in `scripts/skilltree.py`.
2. Register it in `main()` with `sub.add_parser(...)` and
   `set_defaults(func=cmd_<name>)`; reuse the `common` / `workspace` /
   `agent` parent parsers for the shared options.
3. Document it in `SKILL.md` (pipeline table plus a short section): the
   agent only discovers tools that are documented there.
4. Third-party packages: add them to the script's inline `# /// script`
   `dependencies` block (that is what `uv run` installs), and `uv add <pkg>`
   from the repo root so the dev environment matches. Prefer a ready-made
   package over ad-hoc code.
5. Test it (see below) before committing.

## Tool contract

- Return a dict: `main()` prints it as `key: value` lines, or as JSON with
  `--json`. Put a `problems` list in it to report failures (exit 1).
- Raise `Error("...")` for a user-facing failure: printed without a
  traceback, exit 1.
- No network calls or writes outside the paths the user asked about, unless
  the tool's documented purpose requires it.
- Files the tool needs at runtime go in `references/` and are read through
  `REFS`.

## Template

```python
def cmd_hello(args) -> dict:
    """One-line purpose."""
    path = Path(args.path)
    if not path.exists():
        raise Error(f"{path} not found")
    return {"path": str(path), "problems": []}

# in main():
p = sub.add_parser("hello", parents=[common], help="one-line purpose")
p.add_argument("path", help="what this tool consumes")
p.set_defaults(func=cmd_hello)
```

## Testing

```bash
uv run scripts/skilltree.py <name> --help
uv run scripts/skilltree.py <name> <example-input>
uv run scripts/skilltree.py <name> --json <example-input>
```

Verify the exit code (`echo $?`) for both a successful and a failing run.
