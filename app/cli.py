"""Command-line interface: inventory import | search | low-stock | summary | update."""

from pathlib import Path
from typing import NoReturn, Optional

import typer

from app.exporter import export_items, export_summary
from app.importer import ImportResult, InventoryFileError, Item, load_inventory
from app.reports import Summary, low_stock, summarize
from app.search import search_items
from app.state import NoImportError, load_imported_file, save_imported_file
from app.updater import UpdateError, parse_quantity, update_quantity

app = typer.Typer(help="Check, search and report on an inventory CSV file.", no_args_is_help=True)

ExportOption = typer.Option(None, "--export", help="Write the result to this CSV file.")


def fail(message: str) -> NoReturn:
    """Print an error and exit with code 1."""
    typer.echo(message, err=True)
    raise typer.Exit(code=1)


def plural(count: int, word: str) -> str:
    """Return e.g. '1 row' or '3 rows'."""
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def load_current() -> tuple[Path, ImportResult]:
    """Load the imported file; print a one-line warning if rows were skipped."""
    try:
        path = load_imported_file()
        result = load_inventory(path)
    except (NoImportError, InventoryFileError) as error:
        fail(str(error))
    if result.invalid_rows:
        count = plural(len(result.invalid_rows), "invalid row")
        typer.echo(f"{count} skipped — run import for details", err=True)
    return path, result


def print_items(items: list[Item]) -> None:
    """Print items as an aligned table, or a message when there are none."""
    if not items:
        typer.echo("No items found.")
        return
    typer.echo(f"{'SKU':<10} {'NAME':<30} {'CATEGORY':<12} {'QTY':>5} {'PRICE':>9} {'REORDER':>7}")
    for item in items:
        typer.echo(
            f"{item.sku:<10} {item.name:<30} {item.category:<12} {item.quantity:>5} "
            f"{item.unit_price:>9.2f} {item.reorder_level:>7}"
        )


def print_summary(summary: Summary) -> None:
    """Print overall totals and one line per category."""
    typer.echo(f"Total items: {summary.total_items}")
    typer.echo(f"Total units: {summary.total_units}")
    typer.echo(f"Total stock value: {summary.total_value:.2f}")
    typer.echo(f"{'CATEGORY':<12} {'ITEMS':>5} {'UNITS':>6} {'VALUE':>10}")
    for totals in summary.categories:
        typer.echo(f"{totals.category:<12} {totals.items:>5} {totals.units:>6} {totals.value:>10.2f}")


def export_message(path: Path | None, count: int) -> None:
    """Confirm an export on screen."""
    if path is not None:
        typer.echo(f"Exported {plural(count, 'row')} to {path}")


@app.command("import")
def import_file(file: Path = typer.Argument(..., help="CSV file to import.")) -> None:
    """Validate FILE, list every invalid row and remember it for other commands."""
    try:
        result = load_inventory(file)
    except InventoryFileError as error:
        fail(f"Cannot import: {error}")
    save_imported_file(file)
    typer.echo(f"Imported {plural(len(result.items), 'valid item')} from {file}")
    if result.invalid_rows:
        typer.echo(f"{plural(len(result.invalid_rows), 'invalid row')} skipped:")
        for row in result.invalid_rows:
            typer.echo(f"  Row {row.row_number}: {row.reason}")


@app.command()
def search(
    name: Optional[str] = typer.Option(None, "--name", help="Part of the item name (any case)."),
    category: Optional[str] = typer.Option(None, "--category", help="Category name (any case)."),
    export: Optional[Path] = ExportOption,
) -> None:
    """Search items by name and/or category."""
    if name is None and category is None:
        fail("Give --name and/or --category.")
    _, result = load_current()
    items = search_items(result.items, name=name, category=category)
    print_items(items)
    if export is not None:
        export_items(items, export)
    export_message(export, len(items))


@app.command("low-stock")
def low_stock_command(export: Optional[Path] = ExportOption) -> None:
    """List items whose quantity is at or below their reorder level."""
    _, result = load_current()
    items = low_stock(result.items)
    print_items(items)
    if export is not None:
        export_items(items, export)
    export_message(export, len(items))


@app.command()
def summary(export: Optional[Path] = ExportOption) -> None:
    """Show total items, total units, stock value and per-category totals."""
    _, result = load_current()
    totals = summarize(result.items)
    print_summary(totals)
    if export is not None:
        export_summary(totals, export)
    export_message(export, len(totals.categories))


@app.command()
def update(
    sku: str = typer.Argument(..., help="SKU of the item to change."),
    quantity: str = typer.Option(..., "--quantity", help="New quantity (whole number >= 0)."),
) -> None:
    """Set the quantity of one item in the imported file (original saved as FILE.bak)."""
    path, _ = load_current()
    try:
        new_quantity = parse_quantity(quantity)
        backup = update_quantity(path, sku, new_quantity)
    except (UpdateError, InventoryFileError) as error:
        fail(str(error))
    typer.echo(f"Updated {sku.strip()}: quantity is now {new_quantity}")
    typer.echo(f"Backup saved to {backup}")
