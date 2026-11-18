from decimal import Decimal

from app.importer import CATEGORIES
from app.reports import low_stock, summarize
from tests.conftest import make_item


def test_low_stock_includes_items_at_or_below_reorder_level() -> None:
    items = [
        make_item("A", quantity=2, reorder_level=5),
        make_item("B", quantity=5, reorder_level=5),
        make_item("C", quantity=6, reorder_level=5),
        make_item("D", quantity=0, reorder_level=0),
    ]
    assert [item.sku for item in low_stock(items)] == ["A", "B", "D"]


def test_summary_totals_items_units_and_value() -> None:
    items = [
        make_item("A", category="Kitchen", quantity=3, unit_price="2.50"),
        make_item("B", category="Kitchen", quantity=4, unit_price="1.25"),
        make_item("C", category="Cleaning", quantity=10, unit_price="0.99"),
    ]
    summary = summarize(items)
    assert summary.total_items == 3
    assert summary.total_units == 17
    assert summary.total_value == Decimal("22.40")


def test_summary_per_category_totals() -> None:
    items = [make_item("A", category="Kitchen", quantity=3, unit_price="2.50")]
    kitchen = {totals.category: totals for totals in summarize(items).categories}["Kitchen"]
    assert (kitchen.items, kitchen.units, kitchen.value) == (1, 3, Decimal("7.50"))


def test_summary_always_lists_all_four_categories_with_zeros() -> None:
    summary = summarize([make_item("A", category="Kitchen")])
    assert [totals.category for totals in summary.categories] == CATEGORIES
    empty = [totals for totals in summary.categories if totals.category != "Kitchen"]
    assert all((t.items, t.units, t.value) == (0, 0, Decimal("0")) for t in empty)


def test_summary_of_no_items_is_all_zero() -> None:
    summary = summarize([])
    assert (summary.total_items, summary.total_units, summary.total_value) == (0, 0, Decimal("0"))
    assert len(summary.categories) == 4
