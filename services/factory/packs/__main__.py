"""Inspect one project pack file in isolation: `python -m factory.packs path/to/pack.py`.

Prints the pack description and tool metadata as JSON. Exit status 1 with the
error on stderr when the file cannot be imported or declares invalid tools.
"""
import json
import sys
from pathlib import Path

from . import describe_module, load


def main():
    path = Path(sys.argv[1])
    try:
        module = load(path.stem, [path.parent])
        print(json.dumps(describe_module(module)))
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
