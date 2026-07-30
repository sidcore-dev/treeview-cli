"""Command-line entry point for treeview-cli."""
from __future__ import annotations

import argparse
import os
import sys

from .core import build_tree, load_gitignore, render_tree


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="treeview-cli",
        description="Print a directory tree that automatically respects .gitignore.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Directory to display (default: current directory)")
    parser.add_argument("--all", action="store_true", help="Ignore .gitignore and show everything")
    parser.add_argument("--depth", type=int, default=None, help="Limit recursion depth")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not os.path.isdir(args.path):
        print(f"treeview-cli: error: not a directory: {args.path}", file=sys.stderr)
        return 2

    if args.depth is not None and args.depth < 0:
        print("treeview-cli: error: --depth must be 0 or greater", file=sys.stderr)
        return 2

    matcher = None if args.all else load_gitignore(args.path)
    tree = build_tree(args.path, matcher, args.depth)

    for line in render_tree(tree):
        print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
