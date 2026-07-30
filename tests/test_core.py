import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from treeview_cli.core import (
    GitignoreMatcher,
    build_tree,
    load_gitignore,
    parse_gitignore,
    render_tree,
)


class TestParseGitignore(unittest.TestCase):
    def test_ignores_comments_and_blanks(self) -> None:
        patterns = parse_gitignore("# comment\n\n*.pyc\nbuild/\n")
        self.assertEqual(patterns, ["*.pyc", "build/"])

    def test_strips_whitespace(self) -> None:
        patterns = parse_gitignore("  node_modules/  \n")
        self.assertEqual(patterns, ["node_modules/"])


class TestGitignoreMatcher(unittest.TestCase):
    def test_matches_extension_pattern(self) -> None:
        matcher = GitignoreMatcher(patterns=["*.pyc"])
        self.assertTrue(matcher.is_ignored("foo.pyc", False))
        self.assertFalse(matcher.is_ignored("foo.py", False))

    def test_matches_exact_name_anywhere(self) -> None:
        matcher = GitignoreMatcher(patterns=["node_modules"])
        self.assertTrue(matcher.is_ignored("node_modules", True))
        self.assertTrue(matcher.is_ignored("src/node_modules", True))

    def test_dir_only_pattern_skips_files(self) -> None:
        matcher = GitignoreMatcher(patterns=["build/"])
        self.assertTrue(matcher.is_ignored("build", True))
        self.assertFalse(matcher.is_ignored("build", False))

    def test_anchored_pattern_only_matches_root(self) -> None:
        matcher = GitignoreMatcher(patterns=["/dist"])
        self.assertTrue(matcher.is_ignored("dist", True))
        self.assertFalse(matcher.is_ignored("src/dist", True))

    def test_negation_reincludes_file(self) -> None:
        matcher = GitignoreMatcher(patterns=["*.log", "!keep.log"])
        self.assertTrue(matcher.is_ignored("debug.log", False))
        self.assertFalse(matcher.is_ignored("keep.log", False))


class TestBuildTree(unittest.TestCase):
    def test_builds_nested_structure(self) -> None:
        with TemporaryDirectory() as tmp:
            (Path(tmp) / "a.txt").write_text("x")
            (Path(tmp) / "sub").mkdir()
            (Path(tmp) / "sub" / "b.txt").write_text("y")

            tree = build_tree(tmp)
            names = {child.name for child in tree.children}
            self.assertEqual(names, {"a.txt", "sub"})
            sub_node = next(c for c in tree.children if c.name == "sub")
            self.assertTrue(sub_node.is_dir)
            self.assertEqual([c.name for c in sub_node.children], ["b.txt"])

    def test_respects_gitignore(self) -> None:
        with TemporaryDirectory() as tmp:
            (Path(tmp) / ".gitignore").write_text("*.log\n")
            (Path(tmp) / "keep.txt").write_text("x")
            (Path(tmp) / "debug.log").write_text("y")

            matcher = load_gitignore(tmp)
            tree = build_tree(tmp, matcher)
            names = {child.name for child in tree.children}
            self.assertIn("keep.txt", names)
            self.assertNotIn("debug.log", names)

    def test_max_depth_limits_recursion(self) -> None:
        with TemporaryDirectory() as tmp:
            (Path(tmp) / "sub").mkdir()
            (Path(tmp) / "sub" / "deep.txt").write_text("y")

            tree = build_tree(tmp, max_depth=1)
            sub_node = next(c for c in tree.children if c.name == "sub")
            self.assertEqual(sub_node.children, [])

    def test_render_tree_uses_connectors(self) -> None:
        with TemporaryDirectory() as tmp:
            (Path(tmp) / "a.txt").write_text("x")
            (Path(tmp) / "b.txt").write_text("y")
            tree = build_tree(tmp)
            lines = render_tree(tree)
            self.assertEqual(len(lines), 3)
            self.assertTrue(lines[1].startswith("├── ") or lines[1].startswith("└── "))
            self.assertTrue(lines[2].startswith("└── "))


if __name__ == "__main__":
    unittest.main()
