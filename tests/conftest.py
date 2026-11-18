"""Shared fixtures. Every test works in its own temporary folder."""

from decimal import Decimal
from pathlib import Path

import pytest

from app.importer import Item

HEADER = "sku,name,category,quantity,unit_price,reorder_level\n"


def write_csv(folder: Path, body: str, name: str = "inventory.csv") -> Path:
    """Write HEADER + body to folder/name and return the path."""
    path = folder / name
    path.write_text(HEADER + body, encoding="utf-8")
    return path


def make_item(
    sku: str = "EL-001",
    name: str = "Cable",
    category: str = "Electronics",
    quantity: int = 5,
    unit_price: str = "1.00",
    reorder_level: int = 2,
) -> Item:
    """Build an Item with sensible defaults."""
    return Item(sku, name, category, quantity, Decimal(unit_price), reorder_level)


@pytest.fixture(autouse=True)
def isolated_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Run every test inside its own empty temporary folder."""
    monkeypatch.chdir(tmp_path)
    return tmp_path
