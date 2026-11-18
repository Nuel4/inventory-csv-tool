# inventory-csv-tool - Spec

## Purpose
A small command-line tool for a shop owner who keeps stock in spreadsheets.
They export a CSV every week and want to quickly see what's running low,
search items, and export a filtered list to send to a supplier.

## Features (v1)
- Import items from a CSV file and validate every row
- Search items by name (case-insensitive, partial match) or by category
- Low-stock report: list items where quantity is at or below reorder_level
- Export any search or report result to a new CSV file
- Summary: total items, total stock value (quantity × unit_price), per category

## Out of scope (do NOT build)
- No database - CSV in, CSV out
- No web API or frontend - CLI only
- No user accounts or authentication

## Stack & conventions
- Python 3.11, CLI built with Typer
- Tests: pytest, one test file per module in tests/
- Layout: app/ (code), tests/, samples/
- Type hints on all functions; functions under ~30 lines
- Invalid rows are reported with row number and reason, never silently dropped
- No secrets or .env files committed

## Data
- Sample file: samples/inventory_sample.csv
- Columns: sku, name, category, quantity, unit_price, reorder_level
- Rules:
  - sku is unique and required
  - quantity and reorder_level are whole numbers ≥ 0
  - unit_price is ≥ 0, max 2 decimal places
  - category is one of: Electronics, Stationery, Kitchen, Cleaning

## Example usage
inventory import samples/inventory_sample.csv
inventory search --name "pen"
inventory low-stock --export low_stock.csv
inventory summary

## Definition of done
- Every feature above works and has tests, including invalid-data cases
- pytest passes with no failures
- README explains install, usage, and the CSV format with examples






## Decisions (added after Run 1)
- State: `inventory import FILE` saves the file path to `.inventory_state`
  in the current folder. search, low-stock and summary read the file from
  there. No hardcoded default file. If nothing has been imported yet, show:
  "No file imported yet. Run: inventory import FILE" and exit with code 1.
- `.inventory_state` must be in .gitignore.
- Invalid-row warnings: show the full list only on `import`. Other commands
  show one line only, e.g. "3 invalid rows skipped — run import for details".
- Duplicate SKU: keep the first row, report later ones as duplicates.
- Summary shows BOTH: total items (distinct SKUs) and total units (sum of
  quantity).
- Export: available on search, low-stock AND summary. Summary export writes
  one row per category: category, items, units, value.
- No stray blank lines at the start of any output.
- Python 3.11+ only.





## Decisions (added after Run 2)
- Duplicate SKU: only VALID rows claim a SKU. If the first row with a SKU is
  invalid, the first valid row with that SKU is kept.
- Summary (screen and export) always shows all four categories, with 0 for
  categories that have no items.
- Tests must check the code's behaviour only. No tests that depend on the
  machine running them (e.g. checking the Python version in use).
- Leading/trailing spaces in cells are trimmed before validation. Document
  this in the README.

## New feature (added after Run 2)
- `inventory update SKU --quantity N` changes the quantity of one item in
  the currently imported CSV file.
- N must be a whole number >= 0, otherwise show an error and exit 1.
- If the SKU doesn't exist among valid rows, show an error and exit 1.
- Before writing, save a backup of the original file as FILE.bak.
- All other rows (including invalid ones) and their order stay unchanged.
- If nothing has been imported, use the same "No file imported yet" error.