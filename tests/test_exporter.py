"""Tests for app/exporter.py."""

from pathlib import Path

from app.exporter import export_items, item_to_row
from app.importer import Item, load_csv
from tests.conftest import make_item


def test_export_writes_header_and_rows(tmp_path: Path, items: list[Item]) -> None:
    path = tmp_path / "out.csv"
    assert export_items(items[:2], path) == 2
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines == [
        "sku,name,category,quantity,unit_price,reorder_level",
        "EL-001,USB-C Cable,Electronics,45,4.99,20",
        "ST-001,Blue Pen,Stationery,120,2.30,50",
    ]


def test_export_empty_list_writes_header_only(tmp_path: Path) -> None:
    path = tmp_path / "out.csv"
    assert export_items([], path) == 0
    assert path.read_text(encoding="utf-8").splitlines() == [
        "sku,name,category,quantity,unit_price,reorder_level"
    ]


def test_price_always_two_decimals() -> None:
    assert item_to_row(make_item("X", "x", "Kitchen", 1, "12.5", 1))[4] == "12.50"


def test_names_with_commas_round_trip(tmp_path: Path) -> None:
    item = make_item("X-1", "Pens, blue (10 pack)", "Stationery", 3, "2.30", 5)
    path = tmp_path / "out.csv"
    export_items([item], path)
    result = load_csv(path)
    assert result.errors == []
    assert result.items == [item]
