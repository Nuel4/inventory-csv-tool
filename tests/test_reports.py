from decimal import Decimal
from pathlib import Path

from app.importer import Item, load_inventory
from app.reports import low_stock, summarize


def item(sku: str, category: str, qty: int, price: str, reorder: int) -> Item:
    return Item(sku, sku, category, qty, Decimal(price), reorder)


def test_low_stock_includes_equal_and_below() -> None:
    items = [item("A", "Kitchen", 5, "1", 5), item("B", "Kitchen", 4, "1", 5), item("C", "Kitchen", 6, "1", 5)]
    assert [i.sku for i in low_stock(items)] == ["A", "B"]


def test_low_stock_sample(sample_csv: Path) -> None:
    result = low_stock(load_inventory(sample_csv).items)
    assert [i.sku for i in result] == ["EL-002", "EL-003", "ST-002", "KI-002", "CL-002", "CL-003"]


def test_summary_items_and_units_are_both_reported() -> None:
    items = [item("A", "Kitchen", 10, "2.50", 0), item("B", "Kitchen", 5, "1.00", 0), item("C", "Cleaning", 0, "9.99", 0)]
    summary = summarize(items)
    assert summary.total_items == 3  # distinct SKUs
    assert summary.total_units == 15  # sum of quantity
    assert summary.total_value == Decimal("30.00")


def test_summary_per_category_in_spec_order_only_present() -> None:
    items = [item("A", "Kitchen", 10, "2.50", 0), item("B", "Electronics", 1, "3.00", 0), item("C", "Kitchen", 2, "1.00", 0)]
    cats = summarize(items).categories
    assert [(c.category, c.items, c.units, c.value) for c in cats] == [
        ("Electronics", 1, 1, Decimal("3.00")),
        ("Kitchen", 2, 12, Decimal("27.00")),
    ]


def test_summary_sample(sample_csv: Path) -> None:
    summary = summarize(load_inventory(sample_csv).items)
    assert (summary.total_items, summary.total_units) == (12, 312)
    assert summary.total_value == Decimal("1302.16")


def test_summary_empty() -> None:
    summary = summarize([])
    assert (summary.total_items, summary.total_units, summary.total_value) == (0, 0, Decimal("0"))
    assert summary.categories == []
