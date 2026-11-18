"""Read an inventory CSV file and validate every row."""

import csv
import re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

COLUMNS: list[str] = ["sku", "name", "category", "quantity", "unit_price", "reorder_level"]
CATEGORIES: list[str] = ["Electronics", "Stationery", "Kitchen", "Cleaning"]
WHOLE_NUMBER = re.compile(r"[0-9]+")
PRICE = re.compile(r"[0-9]+(\.[0-9]{1,2})?")


class InventoryFileError(Exception):
    """The file as a whole cannot be read (missing, empty, wrong header)."""


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    category: str
    quantity: int
    unit_price: Decimal
    reorder_level: int


@dataclass(frozen=True)
class InvalidRow:
    row_number: int
    reason: str


@dataclass
class ImportResult:
    items: list[Item] = field(default_factory=list)
    invalid_rows: list[InvalidRow] = field(default_factory=list)
    sku_rows: dict[str, int] = field(default_factory=dict)


def parse_whole_number(text: str) -> int | None:
    """Return the value if text is a whole number >= 0, otherwise None."""
    return int(text) if WHOLE_NUMBER.fullmatch(text) else None


def parse_price(text: str) -> Decimal | None:
    """Return the value if text is a number >= 0 with at most 2 decimals."""
    return Decimal(text) if PRICE.fullmatch(text) else None


def row_errors(cells: dict[str, str]) -> list[str]:
    """Return every rule the row breaks (empty list when valid)."""
    errors: list[str] = []
    if not cells["sku"]:
        errors.append("sku is required")
    if cells["category"] not in CATEGORIES:
        errors.append(f"category '{cells['category']}' must be one of: {', '.join(CATEGORIES)}")
    for column in ("quantity", "reorder_level"):
        if parse_whole_number(cells[column]) is None:
            errors.append(f"{column} '{cells[column]}' must be a whole number >= 0")
    if parse_price(cells["unit_price"]) is None:
        errors.append(
            f"unit_price '{cells['unit_price']}' must be a number >= 0 with at most 2 decimal places"
        )
    return errors


def to_item(cells: dict[str, str]) -> Item:
    """Build an Item from cells that already passed validation."""
    return Item(
        sku=cells["sku"],
        name=cells["name"],
        category=cells["category"],
        quantity=int(cells["quantity"]),
        unit_price=Decimal(cells["unit_price"]),
        reorder_level=int(cells["reorder_level"]),
    )


def check_header(header: list[str]) -> list[str]:
    """Trim the header and make sure every required column is present."""
    trimmed = [name.strip() for name in header]
    missing = [column for column in COLUMNS if column not in trimmed]
    if missing:
        raise InventoryFileError(f"missing column(s): {', '.join(missing)}")
    return trimmed


def read_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    """Return the trimmed header and the raw data rows of a CSV file."""
    if not path.is_file():
        raise InventoryFileError(f"file not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        raise InventoryFileError(f"file is empty: {path}")
    return check_header(rows[0]), rows[1:]


def validate_rows(header: list[str], rows: list[list[str]]) -> ImportResult:
    """Validate data rows. Row numbers count the header as row 1."""
    result = ImportResult()
    for row_number, raw in enumerate(rows, start=2):
        if not any(cell.strip() for cell in raw):
            result.invalid_rows.append(InvalidRow(row_number, "row is empty"))
            continue
        if len(raw) != len(header):
            reason = f"expected {len(header)} cells, found {len(raw)}"
            result.invalid_rows.append(InvalidRow(row_number, reason))
            continue
        cells = {name: value.strip() for name, value in zip(header, raw)}
        errors = row_errors(cells)
        if not errors and cells["sku"] in result.sku_rows:
            errors = [f"duplicate sku '{cells['sku']}' (first valid row is kept)"]
        if errors:
            result.invalid_rows.append(InvalidRow(row_number, "; ".join(errors)))
            continue
        result.sku_rows[cells["sku"]] = row_number
        result.items.append(to_item(cells))
    return result


def load_inventory(path: Path) -> ImportResult:
    """Read and validate an inventory CSV file."""
    header, rows = read_rows(path)
    return validate_rows(header, rows)
