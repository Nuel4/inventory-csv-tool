import csv
from pathlib import Path

import pytest
from typer.testing import CliRunner

from app.cli import app
from tests.conftest import HEADER, write_csv

runner = CliRunner()
NO_IMPORT = "No file imported yet. Run: inventory import FILE"

BODY = (
    "EL-001,USB-C Cable,Electronics,45,4.99,20\n"
    "EL-002,Wireless Mouse,Electronics,8,12.50,10\n"
    "ST-001,Blue Ballpoint Pen,Stationery,120,2.30,50\n"
    "KI-001,Ceramic Mug,Kitchen,4,5.50,10\n"
    "EL-003,HDMI Cable,Electronics,-2,8.99,5\n"
    "ST-002,Highlighter Set,Toys,25,4.50,10\n"
    "EL-001,USB-C Cable 2m,Electronics,10,6.49,5\n"
)


@pytest.fixture
def imported(isolated_folder: Path) -> Path:
    path = write_csv(isolated_folder, BODY)
    assert runner.invoke(app, ["import", str(path)]).exit_code == 0
    return path


def read_rows(path: Path) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.reader(handle))


# --- import and state -------------------------------------------------------


def test_import_saves_state_and_lists_every_invalid_row(isolated_folder: Path) -> None:
    path = write_csv(isolated_folder, BODY)
    result = runner.invoke(app, ["import", str(path)])
    assert result.exit_code == 0
    assert (isolated_folder / ".inventory_state").read_text(encoding="utf-8") == str(path.resolve())
    assert "Imported 4 valid items" in result.output
    assert "3 invalid rows skipped:" in result.output
    for row in ("Row 6: quantity", "Row 7: category 'Toys'", "Row 8: duplicate sku 'EL-001'"):
        assert row in result.output


def test_import_missing_file_fails_and_saves_no_state(isolated_folder: Path) -> None:
    result = runner.invoke(app, ["import", "missing.csv"])
    assert result.exit_code == 1
    assert "file not found" in result.output
    assert not (isolated_folder / ".inventory_state").exists()


@pytest.mark.parametrize(
    "args", [["search", "--name", "pen"], ["low-stock"], ["summary"], ["update", "EL-001", "--quantity", "3"]]
)
def test_commands_without_import_show_message_and_exit_1(args: list[str]) -> None:
    result = runner.invoke(app, args)
    assert result.exit_code == 1
    assert result.output.strip() == NO_IMPORT


def test_commands_read_file_from_state_not_a_default(imported: Path, isolated_folder: Path) -> None:
    other = write_csv(isolated_folder, "XX-1,Only Item,Kitchen,1,1.00,0\n", name="other.csv")
    runner.invoke(app, ["import", str(other)])
    result = runner.invoke(app, ["search", "--category", "Kitchen"])
    assert "Only Item" in result.output
    assert "Ceramic Mug" not in result.output


# --- invalid-row warnings ---------------------------------------------------


@pytest.mark.parametrize("args", [["search", "--name", "pen"], ["low-stock"], ["summary"]])
def test_other_commands_show_one_line_warning(imported: Path, args: list[str]) -> None:
    result = runner.invoke(app, args)
    assert result.exit_code == 0
    assert result.stderr == "3 invalid rows skipped — run import for details\n"
    assert "Row 6" not in result.output


def test_no_warning_when_all_rows_valid(isolated_folder: Path) -> None:
    path = write_csv(isolated_folder, "A,Mug,Kitchen,1,1.00,0\n")
    runner.invoke(app, ["import", str(path)])
    assert "invalid" not in runner.invoke(app, ["summary"]).output


@pytest.mark.parametrize(
    "args",
    [["import", "inventory.csv"], ["search", "--name", "pen"], ["low-stock"], ["summary"], ["update", "KI-001", "--quantity", "5"]],
)
def test_no_blank_line_at_start_of_output(imported: Path, args: list[str]) -> None:
    result = runner.invoke(app, args)
    assert result.output
    for stream in (result.output, result.stdout, result.stderr):
        assert not stream[:1].isspace()


# --- search / low-stock / summary ------------------------------------------


def test_search_by_name(imported: Path) -> None:
    result = runner.invoke(app, ["search", "--name", "PEN"])
    assert "Blue Ballpoint Pen" in result.stdout
    assert "Ceramic Mug" not in result.stdout


def test_search_by_category(imported: Path) -> None:
    result = runner.invoke(app, ["search", "--category", "electronics"])
    assert "USB-C Cable" in result.stdout and "Wireless Mouse" in result.stdout
    assert "Ceramic Mug" not in result.stdout


def test_search_without_filters_fails(imported: Path) -> None:
    result = runner.invoke(app, ["search"])
    assert result.exit_code == 1
    assert "--name" in result.output


def test_search_no_results(imported: Path) -> None:
    assert "No items found." in runner.invoke(app, ["search", "--name", "laptop"]).stdout


def test_low_stock(imported: Path) -> None:
    result = runner.invoke(app, ["low-stock"])
    assert "Wireless Mouse" in result.stdout and "Ceramic Mug" in result.stdout
    assert "USB-C Cable" not in result.stdout


def test_summary_shows_items_units_and_all_categories(imported: Path) -> None:
    result = runner.invoke(app, ["summary"])
    assert "Total items: 4" in result.stdout
    assert "Total units: 177" in result.stdout
    assert "Total stock value: 622.55" in result.stdout
    cleaning = [line for line in result.stdout.splitlines() if line.startswith("Cleaning")]
    assert cleaning and cleaning[0].split() == ["Cleaning", "0", "0", "0.00"]


# --- export ----------------------------------------------------------------


def test_search_export(imported: Path, isolated_folder: Path) -> None:
    result = runner.invoke(app, ["search", "--name", "cable", "--export", "found.csv"])
    assert result.exit_code == 0
    rows = read_rows(isolated_folder / "found.csv")
    assert rows[0] == ["sku", "name", "category", "quantity", "unit_price", "reorder_level"]
    assert [row[0] for row in rows[1:]] == ["EL-001"]


def test_low_stock_export(imported: Path, isolated_folder: Path) -> None:
    runner.invoke(app, ["low-stock", "--export", "low.csv"])
    assert [row[0] for row in read_rows(isolated_folder / "low.csv")[1:]] == ["EL-002", "KI-001"]


def test_summary_export_has_all_four_categories(imported: Path, isolated_folder: Path) -> None:
    result = runner.invoke(app, ["summary", "--export", "sum.csv"])
    assert result.exit_code == 0
    assert read_rows(isolated_folder / "sum.csv") == [
        ["category", "items", "units", "value"],
        ["Electronics", "2", "53", "324.55"],
        ["Stationery", "1", "120", "276.00"],
        ["Kitchen", "1", "4", "22.00"],
        ["Cleaning", "0", "0", "0.00"],
    ]


# --- update ----------------------------------------------------------------


def test_update_changes_quantity_and_writes_backup(imported: Path) -> None:
    original = imported.read_text(encoding="utf-8")
    result = runner.invoke(app, ["update", "KI-001", "--quantity", "30"])
    assert result.exit_code == 0
    assert "Updated KI-001: quantity is now 30" in result.stdout
    assert Path(str(imported) + ".bak").read_text(encoding="utf-8") == original
    expected = HEADER + BODY.replace("Ceramic Mug,Kitchen,4,", "Ceramic Mug,Kitchen,30,")
    assert imported.read_text(encoding="utf-8") == expected


def test_update_result_seen_by_other_commands(imported: Path) -> None:
    runner.invoke(app, ["update", "KI-001", "--quantity", "30"])
    assert "Ceramic Mug" not in runner.invoke(app, ["low-stock"]).stdout


@pytest.mark.parametrize("value", ["-1", "2.5", "abc"])
def test_update_bad_quantity_exits_1_and_changes_nothing(imported: Path, value: str) -> None:
    original = imported.read_text(encoding="utf-8")
    result = runner.invoke(app, ["update", "KI-001", "--quantity", value])
    assert result.exit_code == 1
    assert "whole number" in result.stderr
    assert imported.read_text(encoding="utf-8") == original
    assert not Path(str(imported) + ".bak").exists()


@pytest.mark.parametrize("sku", ["NOPE-1", "EL-003"])
def test_update_unknown_or_invalid_sku_exits_1(imported: Path, sku: str) -> None:
    original = imported.read_text(encoding="utf-8")
    result = runner.invoke(app, ["update", sku, "--quantity", "5"])
    assert result.exit_code == 1
    assert "not found among valid rows" in result.stderr
    assert imported.read_text(encoding="utf-8") == original
    assert not Path(str(imported) + ".bak").exists()


def test_update_missing_quantity_option_fails(imported: Path) -> None:
    assert runner.invoke(app, ["update", "KI-001"]).exit_code != 0
