"""Read an inventory CSV and validate every row."""

import csv
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

COLUMNS: list[str] = ["sku", "name", "category", "quantity", "unit_price", "reorder_level"]
CATEGORIES: list[str] = ["Electronics", "Stationery", "Kitchen", "Cleaning"]


class ImportFileError(Exception):
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
class RowError:
    row: int
    reason: str


@dataclass
class ImportResult:
    items: list[Item] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)


def parse_whole_number(value: str, column: str) -> int:
    """Parse a whole number >= 0, or raise ValueError with a readable reason."""
    text = value.strip()
    if not (text.isascii() and text.isdigit()):
        raise ValueError(f"{column} must be a whole number >= 0 (got '{value}')")
    return int(text)


def parse_price(value: str) -> Decimal:
    """Parse a price >= 0 with at most 2 decimal places."""
    try:
        price = Decimal(value.strip())
    except InvalidOperation:
        raise ValueError(f"unit_price must be a number (got '{value}')") from None
    if not price.is_finite():
        raise ValueError(f"unit_price must be a number (got '{value}')")
    if price < 0:
        raise ValueError(f"unit_price must be >= 0 (got '{value}')")
    if price.as_tuple().exponent < -2:
        raise ValueError(f"unit_price must have at most 2 decimal places (got '{value}')")
    return price


def parse_row(row: dict[str, str]) -> Item:
    """Turn one CSV row into an Item, or raise ValueError explaining why not."""
    sku = (row.get("sku") or "").strip()
    if not sku:
        raise ValueError("sku is required")
    category = (row.get("category") or "").strip()
    if category not in CATEGORIES:
        allowed = ", ".join(CATEGORIES)
        raise ValueError(f"category must be one of {allowed} (got '{category}')")
    return Item(
        sku=sku,
        name=(row.get("name") or "").strip(),
        category=category,
        quantity=parse_whole_number(row.get("quantity") or "", "quantity"),
        unit_price=parse_price(row.get("unit_price") or ""),
        reorder_level=parse_whole_number(row.get("reorder_level") or "", "reorder_level"),
    )


def check_header(fieldnames: list[str] | None) -> None:
    """Raise ImportFileError if the header is missing any required column."""
    if not fieldnames:
        raise ImportFileError("file is empty")
    missing = [column for column in COLUMNS if column not in fieldnames]
    if missing:
        raise ImportFileError(f"missing column(s): {', '.join(missing)}")


def validate_rows(rows: list[tuple[int, dict[str, str]]]) -> ImportResult:
    """Validate (row_number, row) pairs, keeping the first row for each sku."""
    result = ImportResult()
    first_seen: dict[str, int] = {}
    for row_number, row in rows:
        try:
            item = parse_row(row)
        except ValueError as error:
            result.errors.append(RowError(row_number, str(error)))
            continue
        if item.sku in first_seen:
            reason = f"duplicate sku '{item.sku}' (first seen on row {first_seen[item.sku]})"
            result.errors.append(RowError(row_number, reason))
            continue
        first_seen[item.sku] = row_number
        result.items.append(item)
    return result


def load_inventory(path: Path) -> ImportResult:
    """Read and validate an inventory CSV file.

    Row numbers are file line numbers, so the header is row 1 and the
    first data row is row 2, matching what a spreadsheet shows.
    """
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            check_header(reader.fieldnames)
            rows = [(reader.line_num, row) for row in reader]
    except (OSError, UnicodeDecodeError) as error:
        raise ImportFileError(f"cannot read {path}: {error}") from None
    return validate_rows(rows)
