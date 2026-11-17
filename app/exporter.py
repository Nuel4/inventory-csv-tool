"""Export a list of items to a new CSV file."""

import csv
from pathlib import Path

from app.importer import COLUMNS, Item


def item_to_row(item: Item) -> list[str]:
    """Convert an item to CSV cells in the same column order as the import format."""
    return [
        item.sku,
        item.name,
        item.category,
        str(item.quantity),
        f"{item.unit_price:.2f}",
        str(item.reorder_level),
    ]


def export_items(items: list[Item], path: Path) -> int:
    """Write items (with a header row) to `path` and return how many were written."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        writer.writerows(item_to_row(item) for item in items)
    return len(items)
