"""Low-stock report and stock summary."""

from dataclasses import dataclass
from decimal import Decimal

from app.importer import CATEGORIES, Item


@dataclass(frozen=True)
class CategoryTotals:
    category: str
    items: int
    units: int
    value: Decimal


@dataclass(frozen=True)
class Summary:
    total_items: int
    total_units: int
    total_value: Decimal
    categories: list[CategoryTotals]


def low_stock(items: list[Item]) -> list[Item]:
    """Items whose quantity is at or below their reorder_level."""
    return [item for item in items if item.quantity <= item.reorder_level]


def stock_value(items: list[Item]) -> Decimal:
    """Sum of quantity x unit_price."""
    return sum((item.quantity * item.unit_price for item in items), Decimal("0"))


def category_totals(items: list[Item], category: str) -> CategoryTotals:
    """Totals for one category."""
    in_category = [item for item in items if item.category == category]
    return CategoryTotals(
        category=category,
        items=len({item.sku for item in in_category}),
        units=sum(item.quantity for item in in_category),
        value=stock_value(in_category),
    )


def summarize(items: list[Item]) -> Summary:
    """Total items (distinct SKUs), total units, total value, per category.

    Categories appear in the order listed in the spec, only if they have items.
    """
    present = {item.category for item in items}
    return Summary(
        total_items=len({item.sku for item in items}),
        total_units=sum(item.quantity for item in items),
        total_value=stock_value(items),
        categories=[category_totals(items, c) for c in CATEGORIES if c in present],
    )
