"""Write search, low-stock and summary results to CSV files."""

import csv
from pathlib import Path

from app.importer import COLUMNS, Item
from app.reports import Summary

SUMMARY_COLUMNS: list[str] = ["category", "items", "units", "value"]


def item_row(item: Item) -> list[str]:
    """Return the cells for one item, in COLUMNS order."""
    return [
        item.sku,
        item.name,
        item.category,
        str(item.quantity),
        f"{item.unit_price:.2f}",
        str(item.reorder_level),
    ]


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    """Write a header and rows to a new CSV file (overwrites an existing one)."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def export_items(items: list[Item], path: Path) -> None:
    """Export items using the same columns as the input file."""
    write_csv(path, COLUMNS, [item_row(item) for item in items])


def export_summary(summary: Summary, path: Path) -> None:
    """Export one row per category: category, items, units, value."""
    rows = [
        [totals.category, str(totals.items), str(totals.units), f"{totals.value:.2f}"]
        for totals in summary.categories
    ]
    write_csv(path, SUMMARY_COLUMNS, rows)
