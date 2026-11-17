"""Shared test fixtures."""

from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import pytest

from app.importer import Item

SAMPLE_CSV = Path(__file__).resolve().parent.parent / "samples" / "inventory_sample.csv"
HEADER = "sku,name,category,quantity,unit_price,reorder_level\n"


def make_item(sku: str, name: str, category: str, quantity: int, price: str, reorder: int) -> Item:
    """Build an Item for tests."""
    return Item(sku, name, category, quantity, Decimal(price), reorder)


@pytest.fixture
def sample_csv() -> Path:
    """Path to the sample inventory file shipped with the project."""
    return SAMPLE_CSV


@pytest.fixture
def write_csv(tmp_path: Path) -> Callable[..., Path]:
    """Write CSV rows (header added automatically) to a temp file and return its path."""

    def _write(*rows: str, header: str = HEADER) -> Path:
        path = tmp_path / "inventory.csv"
        path.write_text(header + "".join(row + "\n" for row in rows), encoding="utf-8")
        return path

    return _write


@pytest.fixture
def items() -> list[Item]:
    """A small set of valid items."""
    return [
        make_item("EL-001", "USB-C Cable", "Electronics", 45, "4.99", 20),
        make_item("ST-001", "Blue Pen", "Stationery", 120, "2.30", 50),
        make_item("ST-002", "Notebook", "Stationery", 5, "3.00", 5),
        make_item("KI-001", "Ceramic Mug", "Kitchen", 2, "5.50", 10),
    ]
