#!/usr/bin/env python3
"""Count lines, words, and characters in files or stdin."""

import argparse
import json
import sys


def count(text: str) -> dict:
    return {
        "lines": len(text.splitlines()),
        "words": len(text.split()),
        "characters": len(text),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Count lines, words, and characters in files or stdin."
    )
    parser.add_argument(
        "files", nargs="*", help="input files; reads stdin when omitted"
    )
    parser.add_argument(
        "--json", action="store_true", help="emit JSON instead of text"
    )
    args = parser.parse_args()

    results = []
    failed = False
    for path in args.files or ["-"]:
        try:
            if path == "-":
                label = "<stdin>"
                text = sys.stdin.read()
            else:
                label = path
                with open(path, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
        except OSError as exc:
            print(f"text_stats: {path}: {exc.strerror}", file=sys.stderr)
            failed = True
            continue
        results.append({"source": label, **count(text)})

    if args.json:
        json.dump(results, sys.stdout, indent=2)
        print()
    else:
        for r in results:
            print(
                f"{r['source']}: {r['lines']} lines, "
                f"{r['words']} words, {r['characters']} characters"
            )

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())