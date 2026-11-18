"""Command-line interface: inventory import / search / low-stock / summary."""

from collections.abc import Callable
from pathlib import Path

import typer

from app import exporter, reports, search, state
from app.importer import ImportFileError, ImportResult, Item, RowError, load_inventory

app = typer.Typer(help="Check stock levels in an inventory CSV.", no_args_is_help=True)

ITEM_HEADERS: list[str] = ["SKU", "Name", "Category", "Qty", "Unit price", "Reorder"]
SUMMARY_HEADERS: list[str] = ["Category", "Items", "Units", "Value"]
EXPORT_HELP: str = "Also write the result to this CSV file."


def fail(message: str) -> None:
    """Print an error to stderr and exit with code 1."""
    typer.echo(message, err=True)
    raise typer.Exit(code=1)


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    """Left-aligned plain-text table."""
    widths = [max(len(cell) for cell in column) for column in zip(headers, *rows)]
    lines = [headers, ["-" * width for width in widths], *rows]
    return "\n".join(
        "  ".join(cell.ljust(width) for cell, width in zip(line, widths)).rstrip()
        for line in lines
    )


def plural_rows(count: int) -> str:
    """'1 invalid row' / '3 invalid rows'."""
    return f"{count} invalid row{'' if count == 1 else 's'}"


def show_row_errors(errors: list[RowError]) -> None:
    """Full list of invalid rows (used by import only)."""
    typer.echo(f"{plural_rows(len(errors))}:")
    for error in errors:
        typer.echo(f"  Row {error.row}: {error.reason}")


def load_current() -> ImportResult:
    """Load the CSV recorded by the last import, with a one-line warning for bad rows."""
    try:
        csv_path = state.load_imported_path()
        result = load_inventory(csv_path)
    except state.NoImportError as error:
        fail(str(error))
    except ImportFileError as error:
        fail(f"Error: {error}. Run: inventory import FILE")
    if result.errors:
        typer.echo(f"{plural_rows(len(result.errors))} skipped — run import for details", err=True)
    return result


def show_items(items: list[Item]) -> None:
    """Print items as a table, or a short message when there are none."""
    if not items:
        typer.echo("No items found.")
        return
    rows = [exporter.item_to_row(item) for item in items]
    typer.echo(format_table(ITEM_HEADERS, rows))


def write_export(path: Path, write: Callable[[Path], None], count: int) -> None:
    """Run an export function and report where the rows went."""
    try:
        write(path)
    except OSError as error:
        fail(f"Error: cannot write {path}: {error}")
    typer.echo(f"Exported {count} row{'' if count == 1 else 's'} to {path}")


@app.command("import")
def import_command(file: Path = typer.Argument(..., help="Inventory CSV file.")) -> None:
    """Validate a CSV file and remember it for the other commands."""
    try:
        result = load_inventory(file)
    except ImportFileError as error:
        fail(f"Error: {error}")
    state.save_imported_path(file)
    typer.echo(f"Imported {len(result.items)} items from {file}")
    if result.errors:
        show_row_errors(result.errors)


@app.command("search")
def search_command(
    name: str | None = typer.Option(None, "--name", help="Part of the item name (any case)."),
    category: str | None = typer.Option(None, "--category", help="Category name (any case)."),
    export: Path | None = typer.Option(None, "--export", help=EXPORT_HELP),
) -> None:
    """Search items by name and/or category."""
    if name is None and category is None:
        fail("Error: give --name and/or --category")
    items = search.search_items(load_current().items, name=name, category=category)
    show_items(items)
    if export is not None:
        write_export(export, lambda path: exporter.export_items(items, path), len(items))


@app.command("low-stock")
def low_stock_command(
    export: Path | None = typer.Option(None, "--export", help=EXPORT_HELP),
) -> None:
    """List items at or below their reorder level."""
    items = reports.low_stock(load_current().items)
    show_items(items)
    if export is not None:
        write_export(export, lambda path: exporter.export_items(items, path), len(items))


def show_summary(summary: reports.Summary) -> None:
    """Print totals and the per-category table."""
    typer.echo(f"Total items: {summary.total_items}")
    typer.echo(f"Total units: {summary.total_units}")
    typer.echo(f"Total stock value: {exporter.format_money(summary.total_value)}")
    if summary.categories:
        rows = [
            [c.category, str(c.items), str(c.units), exporter.format_money(c.value)]
            for c in summary.categories
        ]
        typer.echo("")
        typer.echo(format_table(SUMMARY_HEADERS, rows))


@app.command("summary")
def summary_command(
    export: Path | None = typer.Option(None, "--export", help=EXPORT_HELP),
) -> None:
    """Total items, total units, stock value, and totals per category."""
    summary = reports.summarize(load_current().items)
    show_summary(summary)
    if export is not None:
        count = len(summary.categories)
        write_export(export, lambda path: exporter.export_summary(summary, path), count)
