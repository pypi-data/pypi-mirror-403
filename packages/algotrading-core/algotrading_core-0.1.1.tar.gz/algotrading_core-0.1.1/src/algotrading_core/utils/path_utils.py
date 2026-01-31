"""Path utilities for algotrading projects.

Works for any project that has pyproject.toml at the root. Supports:
- algotrading-core: src layout (use subpath=\"src\" when adding to sys.path).
- algotrading-research, algotrading-backend, algotrading-execution: package
  dirs at project root (use subpath=None when adding to sys.path).
"""

import sys
from pathlib import Path

_PYPROJECT_FILENAME = "pyproject.toml"


def get_project_root() -> Path:
    """Return the project root directory (directory containing pyproject.toml).

    Walks up from this file's location until pyproject.toml is found.
    Works when run from an installed package or from source.

    Returns:
        Absolute path to project root.

    Raises:
        FileNotFoundError: If pyproject.toml is not found in any parent directory.
    """
    current = Path(__file__).resolve().parent
    for parent in current.parents:
        if (parent / _PYPROJECT_FILENAME).exists():
            return parent
    raise FileNotFoundError(
        f"❌ '{_PYPROJECT_FILENAME}' not found in any parent of {current}\n"
        "   Run from the project tree."
    )


def get_project_subpath(relative_path: str = "") -> Path:
    """Return a path under project root.

    Use for any project layout: e.g. "src/algotrading_core", "ml", "backend",
    "execution_agent". Empty string returns project root.

    Args:
        relative_path: Path relative to project root (forward slashes). Use ""
            for project root.

    Returns:
        Absolute path: project_root / relative_path.

    Raises:
        FileNotFoundError: If relative_path is non-empty and the resolved path
            does not exist.
    """
    root = get_project_root()
    if not relative_path:
        return root
    resolved = (root / relative_path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(
            f"❌ Path not found: {resolved}\n   Relative to project root: {relative_path!r}"
        )
    return resolved


def add_project_to_sys_path(subpath: str | None = None) -> str:
    """Prepend a path under project root to sys.path if not already present.

    Use so that top-level packages are importable without installing.
    Idempotent.

    - algotrading-core (src layout): use subpath=\"src\" so ``import algotrading_core`` works.
    - algotrading-research, algotrading-backend, algotrading-execution (packages
      at root): use subpath=None so ``import ml``, ``import backend``, etc. work.

    Args:
        subpath: Path relative to project root to add (e.g. "src"). None adds
            project root.

    Returns:
        The path that was ensured in sys.path (as string).

    Raises:
        FileNotFoundError: If subpath is given and that directory does not exist.
    """
    root = get_project_root()
    if subpath is None:
        path_to_add = root
    else:
        path_to_add = root / subpath
        if not path_to_add.is_dir():
            raise FileNotFoundError(
                f"❌ Directory not found: {path_to_add}\n   Subpath: {subpath!r}"
            )
    path_str = str(path_to_add)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
    return path_str
