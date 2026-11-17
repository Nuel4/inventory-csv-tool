"""Command-line interface for inventory-csv-tool (built with Typer)."""

from pathlib import Path
from typing import Annotated, Optional

import typer

from app.exporter import export_items
from app.importer import CsvFormatError, ImportResult, Item, load_csv
from app.reports import low_stock, summarize
from app.search import search_items

DEFAULT_FILE = Path("samples/inventory_sample.csv")

app = typer.Typer(help="Check stock levels in an inventory CSV file.", no_args_is_help=True)

FileOption = Annotated[
    Path, typer.Option("--file", "-f", help="Inventory CSV file to read.")
]
ExportOption = Annotated[
    Optional[Path], typer.Option("--export", "-e", help="Write the results to this CSV file.")
]


def load_or_exit(path: Path) -> ImportResult:
    """Load and validate the CSV, printing every invalid row; exit 1 if the file is unusable."""
    try:
        result = load_csv(path)
    except CsvFormatError as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from None
    for row_error in result.errors:
        typer.echo(f"Invalid row {row_error.row}: {row_error.reason}", err=True)
    return result


def print_items(items: list[Item]) -> None:
    """Print items as an aligned plain-text table."""
    if not items:
        typer.echo("No matching items.")
        return
    typer.echo(f"{'SKU':<8} {'NAME':<30} {'CATEGORY':<12} {'QTY':>5} {'PRICE':>8} {'REORDER':>7}")
    for item in items:
        typer.echo(
            f"{item.sku:<8} {item.name:<30} {item.category:<12} "
            f"{item.quantity:>5} {item.unit_price:>8.2f} {item.reorder_level:>7}"
        )


def show_and_export(items: list[Item], export: Path | None) -> None:
    """Print the items and, if requested, export them to a CSV file."""
    print_items(items)
    if export is not None:
        count = export_items(items, export)
        typer.echo(f"Exported {count} item(s) to {export}")


@app.command("import")
def import_command(
    path: Annotated[Path, typer.Argument(help="Inventory CSV file to import and validate.")],
) -> None:
    """Import a CSV file, validate every row and report the result."""
    result = load_or_exit(path)
    typer.echo(f"Imported {len(result.items)} valid item(s); {len(result.errors)} invalid row(s).")


@app.command("search")
def search_command(
    name: Annotated[Optional[str], typer.Option("--name", "-n", help="Part of the item name (case-insensitive).")] = None,
    category: Annotated[Optional[str], typer.Option("--category", "-c", help="Category (case-insensitive).")] = None,
    file: FileOption = DEFAULT_FILE,
    export: ExportOption = None,
) -> None:
    """Search items by name (partial match) and/or category."""
    if name is None and category is None:
        typer.echo("Error: give --name and/or --category.", err=True)
        raise typer.Exit(code=2)
    result = load_or_exit(file)
    show_and_export(search_items(result.items, name=name, category=category), export)


@app.command("low-stock")
def low_stock_command(file: FileOption = DEFAULT_FILE, export: ExportOption = None) -> None:
    """List items whose quantity is at or below their reorder_level."""
    result = load_or_exit(file)
    show_and_export(low_stock(result.items), export)


@app.command("summary")
def summary_command(file: FileOption = DEFAULT_FILE) -> None:
    """Show total items and total stock value, overall and per category."""
    summary = summarize(load_or_exit(file).items)
    typer.echo(f"Total items: {summary.overall.item_count}")
    typer.echo(f"Total stock value: {summary.overall.stock_value:.2f}")
    typer.echo("By category:")
    for category in sorted(summary.by_category):
        totals = summary.by_category[category]
        typer.echo(f"  {category:<12} items: {totals.item_count:>3}  value: {totals.stock_value:>10.2f}")


if __name__ == "__main__":
    app()
