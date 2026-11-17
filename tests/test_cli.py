"""Tests for app/cli.py."""

from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

from app.cli import app

runner = CliRunner()


def run(*args: str) -> Result:
    return runner.invoke(app, list(args))


def test_import_reports_counts_and_invalid_rows(sample_csv: Path) -> None:
    result = run("import", str(sample_csv))
    assert result.exit_code == 0
    assert "Imported 12 valid item(s); 3 invalid row(s)." in result.stdout
    assert "Invalid row 14: quantity must be >= 0, got -2" in result.stderr
    assert "Invalid row 15:" in result.stderr
    assert "Invalid row 16: duplicate sku 'EL-001'" in result.stderr


def test_import_missing_file_exits_1(tmp_path: Path) -> None:
    result = run("import", str(tmp_path / "missing.csv"))
    assert result.exit_code == 1
    assert "file not found" in result.stderr


def test_import_missing_column_exits_1(write_csv: Callable[..., Path]) -> None:
    path = write_csv("A,x,Kitchen,1,1", header="sku,name,category,quantity,unit_price\n")
    result = run("import", str(path))
    assert result.exit_code == 1
    assert "missing required column(s): reorder_level" in result.stderr


def test_search_by_name(sample_csv: Path) -> None:
    result = run("search", "--name", "pen", "--file", str(sample_csv))
    assert result.exit_code == 0
    assert "ST-001" in result.stdout
    assert "EL-001" not in result.stdout


def test_search_by_category(sample_csv: Path) -> None:
    result = run("search", "--category", "kitchen", "--file", str(sample_csv))
    assert result.exit_code == 0
    for sku in ("KI-001", "KI-002", "KI-003"):
        assert sku in result.stdout
    assert "ST-001" not in result.stdout


def test_search_requires_a_criterion(sample_csv: Path) -> None:
    result = run("search", "--file", str(sample_csv))
    assert result.exit_code == 2
    assert "--name and/or --category" in result.stderr


def test_search_no_match(sample_csv: Path) -> None:
    result = run("search", "--name", "zzz", "--file", str(sample_csv))
    assert "No matching items." in result.stdout


def test_search_export(sample_csv: Path, tmp_path: Path) -> None:
    out = tmp_path / "pens.csv"
    result = run("search", "--name", "pen", "--file", str(sample_csv), "--export", str(out))
    assert result.exit_code == 0
    assert out.read_text(encoding="utf-8").splitlines()[1].startswith("ST-001,")


def test_low_stock_export(sample_csv: Path, tmp_path: Path) -> None:
    out = tmp_path / "low_stock.csv"
    result = run("low-stock", "--file", str(sample_csv), "--export", str(out))
    assert result.exit_code == 0
    assert "Exported 6 item(s)" in result.stdout
    exported = [line.split(",")[0] for line in out.read_text(encoding="utf-8").splitlines()[1:]]
    assert exported == ["EL-002", "EL-003", "ST-002", "KI-002", "CL-002", "CL-003"]


def test_low_stock_reports_invalid_rows(sample_csv: Path) -> None:
    result = run("low-stock", "--file", str(sample_csv))
    assert "Invalid row 14" in result.stderr
    assert "EL-004" not in result.stdout


def test_summary(sample_csv: Path) -> None:
    result = run("summary", "--file", str(sample_csv))
    assert result.exit_code == 0
    assert "Total items: 12" in result.stdout
    assert "Total stock value: 1302.16" in result.stdout
    assert "Electronics" in result.stdout and "369.55" in result.stdout


def test_default_file_is_sample(monkeypatch: pytest.MonkeyPatch, sample_csv: Path) -> None:
    monkeypatch.chdir(sample_csv.parent.parent)
    result = run("summary")
    assert result.exit_code == 0
    assert "Total items: 12" in result.stdout
