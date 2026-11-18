import csv
from pathlib import Path

from app.exporter import export_items, export_summary
from app.reports import summarize
from tests.conftest import make_item


def read_rows(path: Path) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.reader(handle))


def test_export_items_uses_input_columns(tmp_path: Path) -> None:
    out = tmp_path / "out.csv"
    export_items([make_item("A", "Mug, large", "Kitchen", 3, "2.5", 1)], out)
    assert read_rows(out) == [
        ["sku", "name", "category", "quantity", "unit_price", "reorder_level"],
        ["A", "Mug, large", "Kitchen", "3", "2.50", "1"],
    ]


def test_export_empty_result_writes_header_only(tmp_path: Path) -> None:
    out = tmp_path / "out.csv"
    export_items([], out)
    assert len(read_rows(out)) == 1


def test_export_summary_one_row_per_category_including_empty(tmp_path: Path) -> None:
    out = tmp_path / "summary.csv"
    export_summary(summarize([make_item("A", category="Kitchen", quantity=2, unit_price="1.50")]), out)
    assert read_rows(out) == [
        ["category", "items", "units", "value"],
        ["Electronics", "0", "0", "0.00"],
        ["Stationery", "0", "0", "0.00"],
        ["Kitchen", "1", "2", "3.00"],
        ["Cleaning", "0", "0", "0.00"],
    ]
