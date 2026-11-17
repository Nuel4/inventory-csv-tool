"""Import inventory items from a CSV file and validate every row."""

import csv
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

COLUMNS: list[str] = ["sku", "name", "category", "quantity", "unit_price", "reorder_level"]
CATEGORIES: list[str] = ["Electronics", "Stationery", "Kitchen", "Cleaning"]
_INT_PATTERN = re.compile(r"[+-]?\d+")


@dataclass(frozen=True)
class Item:
    """One valid inventory row."""

    sku: str
    name: str
    category: str
    quantity: int
    unit_price: Decimal
    reorder_level: int


@dataclass(frozen=True)
class RowError:
    """An invalid row: its row number in the CSV file (header = row 1) and why."""

    row: int
    reason: str


@dataclass
class ImportResult:
    """Valid items plus every invalid row that was rejected."""

    items: list[Item] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)


class CsvFormatError(Exception):
    """Raised when the file itself cannot be used (missing file or columns)."""


def parse_whole_number(value: str, column: str) -> int:
    """Parse a whole number >= 0, raising ValueError with a readable reason."""
    text = value.strip()
    if not _INT_PATTERN.fullmatch(text):
        raise ValueError(f"{column} must be a whole number, got '{value}'")
    number = int(text)
    if number < 0:
        raise ValueError(f"{column} must be >= 0, got {number}")
    return number


def parse_price(value: str) -> Decimal:
    """Parse unit_price: a number >= 0 with at most 2 decimal places."""
    try:
        price = Decimal(value.strip())
    except InvalidOperation:
        raise ValueError(f"unit_price must be a number, got '{value}'") from None
    if not price.is_finite():
        raise ValueError(f"unit_price must be a number, got '{value}'")
    if price < 0:
        raise ValueError(f"unit_price must be >= 0, got {value.strip()}")
    exponent = price.as_tuple().exponent
    if isinstance(exponent, int) and exponent < -2:
        raise ValueError(f"unit_price must have at most 2 decimal places, got {value.strip()}")
    return price


def parse_row(row: dict[str, str], seen_skus: set[str]) -> Item:
    """Validate one CSV row and build an Item, raising ValueError on the first problem."""
    values = {column: (row.get(column) or "") for column in COLUMNS}
    sku = values["sku"].strip()
    if not sku:
        raise ValueError("sku is required")
    if sku in seen_skus:
        raise ValueError(f"duplicate sku '{sku}'")
    category = values["category"].strip()
    if category not in CATEGORIES:
        raise ValueError(f"category must be one of {', '.join(CATEGORIES)}, got '{category}'")
    return Item(
        sku=sku,
        name=values["name"].strip(),
        category=category,
        quantity=parse_whole_number(values["quantity"], "quantity"),
        unit_price=parse_price(values["unit_price"]),
        reorder_level=parse_whole_number(values["reorder_level"], "reorder_level"),
    )


def check_header(fieldnames: list[str] | None) -> None:
    """Raise CsvFormatError if any required column is missing from the header."""
    present = [name.strip() for name in (fieldnames or [])]
    missing = [column for column in COLUMNS if column not in present]
    if missing:
        raise CsvFormatError(f"missing required column(s): {', '.join(missing)}")


def load_csv(path: Path) -> ImportResult:
    """Read a CSV file, keeping valid items and reporting every invalid row."""
    if not path.is_file():
        raise CsvFormatError(f"file not found: {path}")
    result = ImportResult()
    seen_skus: set[str] = set()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        check_header(reader.fieldnames)
        reader.fieldnames = [name.strip() for name in reader.fieldnames or []]
        for row in reader:
            row_number = reader.line_num
            try:
                item = parse_row(row, seen_skus)
            except ValueError as error:
                result.errors.append(RowError(row=row_number, reason=str(error)))
                continue
            seen_skus.add(item.sku)
            result.items.append(item)
    return result
