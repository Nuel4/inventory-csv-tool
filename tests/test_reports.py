"""Tests for app/reports.py."""

from decimal import Decimal

from app.importer import Item
from app.reports import low_stock, stock_value, summarize
from tests.conftest import make_item


def test_low_stock_includes_at_and_below_reorder_level(items: list[Item]) -> None:
    # ST-002 is exactly at its reorder level, KI-001 is below it.
    assert [item.sku for item in low_stock(items)] == ["ST-002", "KI-001"]


def test_low_stock_zero_quantity() -> None:
    item = make_item("X-1", "Empty", "Kitchen", 0, "1.00", 0)
    assert low_stock([item]) == [item]


def test_low_stock_empty_list() -> None:
    assert low_stock([]) == []


def test_stock_value() -> None:
    assert stock_value(make_item("X-1", "x", "Kitchen", 3, "24.99", 1)) == Decimal("74.97")


def test_summary_totals_and_per_category(items: list[Item]) -> None:
    summary = summarize(items)
    assert summary.overall.item_count == 4
    # 45*4.99 + 120*2.30 + 5*3.00 + 2*5.50 = 224.55 + 276.00 + 15.00 + 11.00
    assert summary.overall.stock_value == Decimal("526.55")
    assert summary.by_category["Stationery"].item_count == 2
    assert summary.by_category["Stationery"].stock_value == Decimal("291.00")
    assert summary.by_category["Kitchen"].stock_value == Decimal("11.00")
    assert set(summary.by_category) == {"Electronics", "Stationery", "Kitchen"}


def test_summary_empty() -> None:
    summary = summarize([])
    assert summary.overall.item_count == 0
    assert summary.overall.stock_value == Decimal("0")
    assert summary.by_category == {}
