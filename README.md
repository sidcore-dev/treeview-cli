# treeview-cli

A small, dependency-free command-line tool that prints a directory tree
like `tree` — but automatically respects `.gitignore` patterns found in
the directory you're viewing, so build artifacts and dependencies don't
clutter the output.

## Why

Running `tree` on a real project usually means staring at `node_modules`,
`__pycache__`, and `.venv` before you can see the files you actually
care about. `treeview-cli` reads the `.gitignore` in the directory it's
scanning and filters accordingly, no extra flags required.

## Install

```bash
pip install .
```

This installs a `treeview-cli` command on your PATH.

## Usage

```bash
treeview-cli
```

Example output for a small project:

```
myproject/
├── README.md
├── pyproject.toml
├── src/
│   └── myproject/
│       ├── __init__.py
│       └── core.py
└── tests/
    └── test_core.py
```

Files and directories matched by `.gitignore` (like `build/` or `*.pyc`)
are skipped automatically.

### Options

| Flag          | Description                                       |
|---------------|----------------------------------------------------|
| `path`        | Directory to display (default: current directory)  |
| `--all`       | Ignore `.gitignore` and show everything             |
| `--depth N`   | Limit recursion depth                               |

### Exit codes

- `0` — tree printed successfully
- `2` — the given path isn't a directory, or arguments are invalid

## Development

```bash
pip install -e .
python -m unittest discover -s tests -v
```

## License

All rights reserved. This code is public for viewing and reference only —
no license is granted to use, copy, modify, or redistribute it. See
[LICENSE](LICENSE) for details.
