"""Core directory-tree logic for treeview-cli.

Gitignore pattern parsing and matching is pure (operates on strings).
`build_tree` is the one function that touches the filesystem; it walks
a directory and returns a plain `Node` tree that `render_tree` (pure)
turns into printable lines.
"""
from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field


def parse_gitignore(text: str) -> list[str]:
    """Extract non-blank, non-comment pattern lines from .gitignore text."""
    patterns = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line)
    return patterns


@dataclass
class GitignoreMatcher:
    """A basic gitignore-style matcher covering common patterns.

    Supports `name`, `*.ext`, `dir/` (directory-only), `/anchored`
    (relative to the ignore root) and `!negated` patterns. It does not
    implement the full git matching algorithm (no `**`, no complex
    character classes), only the patterns people write most often.
    """

    patterns: list[str] = field(default_factory=list)

    def is_ignored(self, relpath: str, is_dir: bool) -> bool:
        relpath = relpath.replace(os.sep, "/")
        name = relpath.rsplit("/", 1)[-1]
        ignored = False
        for raw in self.patterns:
            pattern = raw
            negate = pattern.startswith("!")
            if negate:
                pattern = pattern[1:]
            if not pattern:
                continue
            dir_only = pattern.endswith("/")
            if dir_only:
                pattern = pattern.rstrip("/")
            if dir_only and not is_dir:
                continue
            anchored = pattern.startswith("/")
            if anchored:
                pattern = pattern.lstrip("/")

            if anchored:
                matched = fnmatch.fnmatch(relpath, pattern)
            else:
                matched = fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(relpath, pattern)
                if not matched and "/" not in pattern:
                    matched = any(fnmatch.fnmatch(part, pattern) for part in relpath.split("/"))

            if matched:
                ignored = not negate
        return ignored


def load_gitignore(root: str) -> GitignoreMatcher:
    """Load and parse a .gitignore file from `root`, if one exists."""
    path = os.path.join(root, ".gitignore")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return GitignoreMatcher(patterns=[])
    return GitignoreMatcher(patterns=parse_gitignore(text))


@dataclass
class Node:
    name: str
    is_dir: bool
    children: list["Node"] = field(default_factory=list)


def build_tree(root: str, matcher: GitignoreMatcher | None = None, max_depth: int | None = None) -> Node:
    """Walk `root` on disk and return a Node tree, applying `matcher` and `max_depth`."""
    clean_root = root.rstrip("/") or "/"
    name = os.path.basename(os.path.abspath(clean_root)) or clean_root
    return _build_node(clean_root, name, "", matcher, max_depth, 0)


def _build_node(
    abs_path: str,
    name: str,
    rel_path: str,
    matcher: GitignoreMatcher | None,
    max_depth: int | None,
    depth: int,
) -> Node:
    is_dir = os.path.isdir(abs_path)
    node = Node(name=name, is_dir=is_dir)
    if not is_dir:
        return node
    if max_depth is not None and depth >= max_depth:
        return node
    try:
        entries = sorted(os.listdir(abs_path), key=str.lower)
    except OSError:
        return node
    for entry in entries:
        entry_abs = os.path.join(abs_path, entry)
        entry_rel = entry if not rel_path else f"{rel_path}/{entry}"
        entry_is_dir = os.path.isdir(entry_abs)
        if matcher is not None and matcher.is_ignored(entry_rel, entry_is_dir):
            continue
        node.children.append(_build_node(entry_abs, entry, entry_rel, matcher, max_depth, depth + 1))
    return node


def render_tree(node: Node) -> list[str]:
    """Render a Node tree into `tree`-style lines, root first."""
    lines = [node.name + ("/" if node.is_dir else "")]
    lines.extend(_render_children(node.children, ""))
    return lines


def _render_children(children: list[Node], prefix: str) -> list[str]:
    lines = []
    for i, child in enumerate(children):
        is_last = i == len(children) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{child.name}{'/' if child.is_dir else ''}")
        extension = "    " if is_last else "│   "
        lines.extend(_render_children(child.children, prefix + extension))
    return lines
