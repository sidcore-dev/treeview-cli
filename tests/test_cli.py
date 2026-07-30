import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from treeview_cli.cli import main


class TestCli(unittest.TestCase):
    def test_exit_code_2_for_missing_directory(self) -> None:
        code = main(["/nonexistent/path/xyz"])
        self.assertEqual(code, 2)

    def test_prints_root_and_children(self) -> None:
        with TemporaryDirectory() as tmp:
            (Path(tmp) / "a.txt").write_text("x")
            out = io.StringIO()
            with redirect_stdout(out):
                code = main([tmp])
            self.assertEqual(code, 0)
            self.assertIn("a.txt", out.getvalue())

    def test_gitignore_respected_by_default(self) -> None:
        with TemporaryDirectory() as tmp:
            (Path(tmp) / ".gitignore").write_text("secret.txt\n")
            (Path(tmp) / "secret.txt").write_text("x")
            (Path(tmp) / "visible.txt").write_text("y")
            out = io.StringIO()
            with redirect_stdout(out):
                main([tmp])
            self.assertNotIn("secret.txt", out.getvalue())
            self.assertIn("visible.txt", out.getvalue())

    def test_all_flag_shows_ignored_files(self) -> None:
        with TemporaryDirectory() as tmp:
            (Path(tmp) / ".gitignore").write_text("secret.txt\n")
            (Path(tmp) / "secret.txt").write_text("x")
            out = io.StringIO()
            with redirect_stdout(out):
                main([tmp, "--all"])
            self.assertIn("secret.txt", out.getvalue())

    def test_negative_depth_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            code = main([tmp, "--depth", "-1"])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
