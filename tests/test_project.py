"""Project-level decisions that do not belong to a single app/ module."""

import sys
import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def test_requires_python_311_or_newer() -> None:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    assert data["project"]["requires-python"] == ">=3.11"


def test_running_on_python_311_or_newer() -> None:
    assert sys.version_info >= (3, 11)


def test_cli_entry_point_is_inventory() -> None:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    assert data["project"]["scripts"]["inventory"] == "app.cli:app"
