import csv
from pathlib import Path

import pytest
from typer.testing import CliRunner

from app.cli import app

runner = CliRunner()
NO_IMPORT = "No file imported yet. Run: inventory import FILE"
ONE_LINE_WARNING = "3 invalid rows skipped — run import for details"


@pytest.fixture(autouse=True)
def in_tmp_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Every CLI test runs in an empty folder so .inventory_state starts absent."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def run(*args: str):
    return runner.invoke(app, list(args))


def imported(sample_csv: Path) -> None:
    assert run("import", str(sample_csv)).exit_code == 0


# --- State --------------------------------------------------------------------

@pytest.mark.parametrize(
    "args", [["search", "--name", "pen"], ["low-stock"], ["summary"]]
)
def test_commands_without_import_fail_with_message(args: list[str]) -> None:
    result = run(*args)
    assert result.exit_code == 1
    assert result.output.strip() == NO_IMPORT


def test_import_saves_path_to_state_file(sample_csv: Path, in_tmp_folder: Path) -> None:
    imported(sample_csv)
    state = in_tmp_folder / ".inventory_state"
    assert Path(state.read_text().strip()) == sample_csv.resolve()


def test_other_commands_read_file_from_state(write_csv, in_tmp_folder: Path) -> None:
    path = write_csv("Z-9,Zebra Pen,Stationery,1,1.00,5\n")
    assert run("import", str(path)).exit_code == 0
    result = run("search", "--name", "zebra")
    assert result.exit_code == 0
    assert "Z-9" in result.stdout


def test_latest_import_replaces_previous(sample_csv: Path, write_csv) -> None:
    imported(sample_csv)
    run("import", str(write_csv("Z-9,Zebra Pen,Stationery,1,1.00,5\n")))
    result = run("summary")
    assert "Total items: 1" in result.stdout


def test_no_hardcoded_default_file() -> None:
    # Even though samples/inventory_sample.csv exists in the repo, nothing is used
    # unless it was imported in this folder.
    assert run("summary").exit_code == 1


def test_import_missing_file_fails_and_saves_nothing(in_tmp_folder: Path) -> None:
    result = run("import", "nope.csv")
    assert result.exit_code == 1
    assert "cannot read" in result.output
    assert not (in_tmp_folder / ".inventory_state").exists()


def test_imported_file_deleted_later(write_csv) -> None:
    path = write_csv("A,x,Kitchen,1,1,0\n")
    run("import", str(path))
    path.unlink()
    result = run("summary")
    assert result.exit_code == 1
    assert "Run: inventory import FILE" in result.output


def test_inventory_state_is_gitignored() -> None:
    gitignore = Path(__file__).resolve().parent.parent / ".gitignore"
    lines = [line.strip() for line in gitignore.read_text().splitlines()]
    assert ".inventory_state" in lines


# --- Invalid-row warnings -----------------------------------------------------

def test_import_shows_full_list_of_invalid_rows(sample_csv: Path) -> None:
    result = run("import", str(sample_csv))
    assert result.exit_code == 0
    assert "Imported 12 items" in result.output
    assert "3 invalid rows:" in result.output
    assert "Row 14: quantity must be a whole number >= 0 (got '-2')" in result.output
    assert "Row 15: category must be one of" in result.output
    assert "Row 16: duplicate sku 'EL-001' (first seen on row 2)" in result.output


@pytest.mark.parametrize(
    "args", [["search", "--name", "pen"], ["low-stock"], ["summary"]]
)
def test_other_commands_show_one_line_only(sample_csv: Path, args: list[str]) -> None:
    imported(sample_csv)
    result = run(*args)
    assert result.exit_code == 0
    assert result.output.count(ONE_LINE_WARNING) == 1
    assert "Row 14" not in result.output
    assert "duplicate" not in result.output


def test_one_line_warning_singular(write_csv) -> None:
    run("import", str(write_csv("A,x,Kitchen,1,1,0\nB,x,Toys,1,1,0\n")))
    assert "1 invalid row skipped — run import for details" in run("summary").output


def test_no_warning_when_all_rows_valid(write_csv) -> None:
    run("import", str(write_csv("A,x,Kitchen,1,1,0\n")))
    assert "invalid" not in run("summary").output


# --- Duplicate SKU ------------------------------------------------------------

def test_duplicate_sku_first_row_kept(sample_csv: Path) -> None:
    imported(sample_csv)
    result = run("search", "--name", "usb-c")
    assert "USB-C Cable 1m" in result.stdout
    assert "USB-C Cable 2m" not in result.stdout


# --- Search / low-stock -------------------------------------------------------

def test_search_by_name(sample_csv: Path) -> None:
    imported(sample_csv)
    result = run("search", "--name", "PEN")
    assert "ST-001" in result.stdout
    assert "KI-001" not in result.stdout


def test_search_by_category(sample_csv: Path) -> None:
    imported(sample_csv)
    result = run("search", "--category", "kitchen")
    assert all(sku in result.stdout for sku in ["KI-001", "KI-002", "KI-003"])
    assert "EL-002" not in result.stdout


def test_search_no_results(sample_csv: Path) -> None:
    imported(sample_csv)
    result = run("search", "--name", "laptop")
    assert result.exit_code == 0
    assert "No items found." in result.stdout


def test_search_needs_a_filter(sample_csv: Path) -> None:
    imported(sample_csv)
    result = run("search")
    assert result.exit_code == 1
    assert "--name and/or --category" in result.output


def test_low_stock(sample_csv: Path) -> None:
    imported(sample_csv)
    result = run("low-stock")
    for sku in ["EL-002", "EL-003", "ST-002", "KI-002", "CL-002", "CL-003"]:
        assert sku in result.stdout
    assert "EL-001" not in result.stdout


# --- Summary ------------------------------------------------------------------

def test_summary_shows_items_and_units(sample_csv: Path) -> None:
    imported(sample_csv)
    result = run("summary")
    assert "Total items: 12" in result.stdout
    assert "Total units: 312" in result.stdout
    assert "Total stock value: 1302.16" in result.stdout
    assert "Electronics  3      56     369.55" in result.stdout


# --- Export -------------------------------------------------------------------

def read_csv(path: Path) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.reader(handle))


def test_search_export(sample_csv: Path, in_tmp_folder: Path) -> None:
    imported(sample_csv)
    result = run("search", "--category", "Kitchen", "--export", "kitchen.csv")
    assert result.exit_code == 0
    assert "Exported 3 rows to kitchen.csv" in result.stdout
    rows = read_csv(in_tmp_folder / "kitchen.csv")
    assert rows[0] == ["sku", "name", "category", "quantity", "unit_price", "reorder_level"]
    assert [r[0] for r in rows[1:]] == ["KI-001", "KI-002", "KI-003"]


def test_low_stock_export(sample_csv: Path, in_tmp_folder: Path) -> None:
    imported(sample_csv)
    result = run("low-stock", "--export", "low_stock.csv")
    assert result.exit_code == 0
    rows = read_csv(in_tmp_folder / "low_stock.csv")
    assert [r[0] for r in rows[1:]] == ["EL-002", "EL-003", "ST-002", "KI-002", "CL-002", "CL-003"]


def test_summary_export_one_row_per_category(sample_csv: Path, in_tmp_folder: Path) -> None:
    imported(sample_csv)
    result = run("summary", "--export", "summary.csv")
    assert result.exit_code == 0
    assert read_csv(in_tmp_folder / "summary.csv") == [
        ["category", "items", "units", "value"],
        ["Electronics", "3", "56", "369.55"],
        ["Stationery", "3", "141", "375.45"],
        ["Kitchen", "3", "46", "382.56"],
        ["Cleaning", "3", "69", "174.60"],
    ]


def test_export_to_unwritable_path_fails(sample_csv: Path, in_tmp_folder: Path) -> None:
    imported(sample_csv)
    result = run("low-stock", "--export", str(in_tmp_folder / "missing_dir" / "x.csv"))
    assert result.exit_code == 1
    assert "cannot write" in result.output


# --- No stray blank lines -----------------------------------------------------

@pytest.mark.parametrize(
    "args",
    [
        ["search", "--name", "pen"],
        ["search", "--name", "laptop"],
        ["low-stock"],
        ["summary"],
        ["summary", "--export", "s.csv"],
    ],
)
def test_no_leading_blank_lines(sample_csv: Path, args: list[str]) -> None:
    import_result = run("import", str(sample_csv))
    result = run(*args)
    for output in [import_result.output, result.output, result.stdout]:
        assert output == output.lstrip("\r\n")


def test_no_leading_blank_line_before_error() -> None:
    result = run("summary")
    assert result.output == result.output.lstrip("\r\n")
