"""Low-stock report and inventory summary."""

from dataclasses import dataclass, field
from decimal import Decimal

from app.importer import Item


@dataclass
class Totals:
    """Item count and stock value (quantity x unit_price) for a group of items."""

    item_count: int = 0
    stock_value: Decimal = Decimal("0.00")


@dataclass
class Summary:
    """Overall totals plus totals per category."""

    overall: Totals = field(default_factory=Totals)
    by_category: dict[str, Totals] = field(default_factory=dict)


def low_stock(items: list[Item]) -> list[Item]:
    """Return items whose quantity is at or below their reorder_level."""
    return [item for item in items if item.quantity <= item.reorder_level]


def stock_value(item: Item) -> Decimal:
    """Return quantity x unit_price for one item."""
    return item.unit_price * item.quantity


def summarize(items: list[Item]) -> Summary:
    """Compute total items and total stock value, overall and per category."""
    summary = Summary()
    for item in items:
        value = stock_value(item)
        group = summary.by_category.setdefault(item.category, Totals())
        for totals in (summary.overall, group):
            totals.item_count += 1
            totals.stock_value += value
    return summary
