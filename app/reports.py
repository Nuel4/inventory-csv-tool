"""Low-stock report and summary."""

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
    """Return items whose quantity is at or below their reorder level."""
    return [item for item in items if item.quantity <= item.reorder_level]


def stock_value(items: list[Item]) -> Decimal:
    """Return the sum of quantity x unit_price."""
    return sum((item.quantity * item.unit_price for item in items), Decimal("0"))


def category_totals(items: list[Item], category: str) -> CategoryTotals:
    """Return totals for one category (zeros when it has no items)."""
    in_category = [item for item in items if item.category == category]
    units = sum(item.quantity for item in in_category)
    return CategoryTotals(category, len(in_category), units, stock_value(in_category))


def summarize(items: list[Item]) -> Summary:
    """Return overall totals plus one entry for every category."""
    return Summary(
        total_items=len({item.sku for item in items}),
        total_units=sum(item.quantity for item in items),
        total_value=stock_value(items),
        categories=[category_totals(items, category) for category in CATEGORIES],
    )
