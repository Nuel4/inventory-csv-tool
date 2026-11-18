"""Write search, low-stock and summary results to CSV."""

import csv
from decimal import Decimal
from pathlib import Path

from app.importer import COLUMNS, Item
from app.reports import Summary

SUMMARY_COLUMNS: list[str] = ["category", "items", "units", "value"]


def format_money(value: Decimal) -> str:
    """Format a Decimal amount with exactly 2 decimal places."""
    return f"{value:.2f}"


def item_to_row(item: Item) -> list[str]:
    """One item as CSV cells, in the same column order as the input file."""
    return [
        item.sku,
        item.name,
        item.category,
        str(item.quantity),
        format_money(item.unit_price),
        str(item.reorder_level),
    ]


def export_items(items: list[Item], path: Path) -> None:
    """Write items to a CSV with the standard inventory columns."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        writer.writerows(item_to_row(item) for item in items)


def export_summary(summary: Summary, path: Path) -> None:
    """Write one row per category: category, items, units, value."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(SUMMARY_COLUMNS)
        for totals in summary.categories:
            writer.writerow(
                [totals.category, totals.items, totals.units, format_money(totals.value)]
            )
