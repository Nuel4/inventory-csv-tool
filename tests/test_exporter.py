import csv
from decimal import Decimal
from pathlib import Path

from app.exporter import export_items, export_summary
from app.importer import Item, load_inventory
from app.reports import summarize

ITEMS = [
    Item("A-1", "Pen, blue", "Stationery", 3, Decimal("2.3"), 5),
    Item("K-1", "Mug", "Kitchen", 10, Decimal("5.50"), 2),
]


def read_rows(path: Path) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.reader(handle))


def test_export_items_same_columns_as_input(tmp_path: Path) -> None:
    out = tmp_path / "out.csv"
    export_items(ITEMS, out)
    assert read_rows(out) == [
        ["sku", "name", "category", "quantity", "unit_price", "reorder_level"],
        ["A-1", "Pen, blue", "Stationery", "3", "2.30", "5"],
        ["K-1", "Mug", "Kitchen", "10", "5.50", "2"],
    ]


def test_exported_items_can_be_imported_again(tmp_path: Path) -> None:
    out = tmp_path / "out.csv"
    export_items(ITEMS, out)
    result = load_inventory(out)
    assert result.errors == []
    assert result.items == [
        Item("A-1", "Pen, blue", "Stationery", 3, Decimal("2.30"), 5),
        ITEMS[1],
    ]


def test_export_empty_items_writes_header_only(tmp_path: Path) -> None:
    out = tmp_path / "out.csv"
    export_items([], out)
    assert read_rows(out) == [["sku", "name", "category", "quantity", "unit_price", "reorder_level"]]


def test_export_summary_one_row_per_category(tmp_path: Path) -> None:
    out = tmp_path / "summary.csv"
    export_summary(summarize(ITEMS), out)
    assert read_rows(out) == [
        ["category", "items", "units", "value"],
        ["Stationery", "1", "3", "6.90"],
        ["Kitchen", "1", "10", "55.00"],
    ]
