"""Change the quantity of one item in the imported CSV file, keeping a .bak backup."""

import csv
import io
import re
import shutil
from pathlib import Path

from app.importer import InventoryFileError, check_header, parse_whole_number, validate_rows

LINE = re.compile(r"[^\n]*\n|[^\n]+$")


class UpdateError(Exception):
    """The update cannot be made (bad quantity, unknown SKU)."""


def parse_quantity(text: str) -> int:
    """Return the new quantity, or raise UpdateError if it is not a whole number >= 0."""
    value = parse_whole_number(text.strip())
    if value is None:
        raise UpdateError(f"Quantity must be a whole number >= 0, got '{text}'.")
    return value


def split_records(text: str) -> list[str]:
    """Split CSV text into raw records, keeping line endings and quoted newlines."""
    records: list[str] = []
    pending = ""
    for line in LINE.findall(text):
        pending += line
        if pending.count('"') % 2 == 0:
            records.append(pending)
            pending = ""
    if pending:
        records.append(pending)
    return records


def parse_record(record: str) -> list[str]:
    """Parse one raw record into its cells."""
    return next(csv.reader(io.StringIO(record)), [])


def line_ending(record: str) -> str:
    """Return the line ending a raw record uses ('' for a last line without one)."""
    if record.endswith("\r\n"):
        return "\r\n"
    return "\n" if record.endswith("\n") else ""


def rewrite_record(record: str, column: int, value: str) -> str:
    """Return the record with one cell replaced and its line ending kept."""
    cells = parse_record(record)
    cells[column] = value
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator=line_ending(record)).writerow(cells)
    return buffer.getvalue()


def find_record(records: list[str], sku: str) -> tuple[int, int]:
    """Return (record index, quantity column) of the kept valid row for sku."""
    if not records:
        raise InventoryFileError("file is empty")
    header = check_header(parse_record(records[0].lstrip("\ufeff")))
    result = validate_rows(header, [parse_record(record) for record in records[1:]])
    row_number = result.sku_rows.get(sku)
    if row_number is None:
        raise UpdateError(f"SKU '{sku}' not found among valid rows.")
    return row_number - 1, header.index("quantity")


def update_quantity(path: Path, sku: str, quantity: int) -> Path:
    """Set the quantity of sku in path, saving the original as path.bak first.

    Returns the backup path. Every other record is written back byte for byte.
    """
    if quantity < 0:
        raise UpdateError(f"Quantity must be a whole number >= 0, got '{quantity}'.")
    with path.open(newline="", encoding="utf-8") as handle:
        records = split_records(handle.read())
    index, column = find_record(records, sku.strip())
    records[index] = rewrite_record(records[index], column, str(quantity))
    backup = path.with_name(path.name + ".bak")
    shutil.copy2(path, backup)
    with path.open("w", newline="", encoding="utf-8") as handle:
        handle.write("".join(records))
    return backup
