# inventory-csv-tool

A small command-line tool for checking a weekly inventory CSV export: validate
every row, search items, see what is running low, get a stock summary, export
any result to a new CSV, and change one item's quantity.

## Install

Requires Python 3.11 or newer.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

This installs the `inventory` command. Run the tests with:

```bash
pytest
```

## Usage

```bash
inventory import samples/inventory_sample.csv
inventory search --name "pen"
inventory search --category Kitchen
inventory search --name "cable" --category Electronics --export cables.csv
inventory low-stock
inventory low-stock --export low_stock.csv
inventory summary
inventory summary --export summary.csv
inventory update KI-002 --quantity 12
```

### How the imported file is remembered

`inventory import FILE` checks the file and saves its full path to
`.inventory_state` in the current folder. `search`, `low-stock`, `summary`
and `update` read the file named there, so run them from the same folder.
If nothing has been imported yet they print:

```
No file imported yet. Run: inventory import FILE
```

and exit with code 1. `.inventory_state` is listed in `.gitignore`.

### Commands

| Command | What it does |
|---|---|
| `import FILE` | Validates every row. Prints how many valid items were loaded and lists **every** invalid row with its row number and reason. |
| `search --name TEXT` | Items whose name contains TEXT (any case). |
| `search --category NAME` | Items in that category (any case, whole name). `--name` and `--category` can be combined; at least one is required. |
| `low-stock` | Items where `quantity` is at or below `reorder_level`. |
| `summary` | Total items (distinct SKUs), total units (sum of quantity), total stock value (quantity × unit_price), and items / units / value for each of the four categories. Categories with no items show 0. |
| `update SKU --quantity N` | Sets the quantity of one item in the imported file. See below. |

`search`, `low-stock` and `summary` accept `--export FILE.csv`. Search and
low-stock exports use the same columns as the input file. Summary exports
write one row per category with the columns `category, items, units, value`
(all four categories, always). An existing export file is overwritten.

When the imported file has invalid rows, commands other than `import` show a
single line instead of the full list, for example:

```
3 invalid rows skipped — run import for details
```

### Updating a quantity

```bash
inventory update KI-002 --quantity 12
```

- `N` must be a whole number ≥ 0 (`0`, `12`); otherwise an error is shown
  and the command exits with code 1.
- The SKU must belong to a valid row. If it does not exist, or appears only
  in invalid or duplicate rows, an error is shown and the command exits
  with code 1. For a duplicated SKU the kept (first valid) row is changed.
- Before writing, the original file is copied to `FILE.bak` next to it
  (for example `inventory.csv.bak`). An older `.bak` is replaced.
- Only that one quantity cell changes. Every other row — including invalid
  rows — and the row order stay exactly as they were.
- Nothing is written (and no `.bak` is made) when the command fails.

## CSV format

The first row is the header. Required columns (any order, extra columns are
ignored):

| Column | Rule |
|---|---|
| `sku` | Required and unique. |
| `name` | Free text. |
| `category` | One of `Electronics`, `Stationery`, `Kitchen`, `Cleaning` (exact spelling and case). |
| `quantity` | Whole number ≥ 0, digits only (e.g. `0`, `45`). |
| `unit_price` | Number ≥ 0 with at most 2 decimal places (e.g. `3`, `3.5`, `3.75`). |
| `reorder_level` | Whole number ≥ 0. |

Example:

```csv
sku,name,category,quantity,unit_price,reorder_level
EL-001,USB-C Cable 1m,Electronics,45,4.99,20
ST-002,A4 Notebook,Stationery,15,3.75,20
KI-002,Chef Knife 20cm,Kitchen,4,24.99,5
```

### Validation details

- **Spaces are trimmed.** Leading and trailing spaces in every cell (and in
  the header names) are removed before validation, so ` 45 ` is read as `45`
  and ` EL-001 ` as `EL-001`.
- **Invalid rows are never silently dropped.** Each one is reported with its
  row number (the header is row 1, so the first item is row 2) and every
  reason it failed. Empty rows and rows with the wrong number of cells are
  reported too.
- **Duplicate SKUs:** only valid rows claim a SKU. The first *valid* row with
  a SKU is kept; later valid rows with the same SKU are reported as
  duplicates. If the first row with a SKU is invalid, it is reported for its
  own problem and the next valid row with that SKU is kept.

Example — this file:

```csv
sku,name,category,quantity,unit_price,reorder_level
EL-004,HDMI Cable 2m,Electronics,-2,8.99,5
ST-004,Highlighter Set,Toys,25,4.50,10
EL-001,USB-C Cable 1m,Electronics,45,4.99,20
EL-001,USB-C Cable 2m,Electronics,10,6.49,5
```

gives on `inventory import`:

```
Imported 1 valid item from inventory.csv
3 invalid rows skipped:
  Row 2: quantity '-2' must be a whole number >= 0
  Row 3: category 'Toys' must be one of: Electronics, Stationery, Kitchen, Cleaning
  Row 5: duplicate sku 'EL-001' (first valid row is kept)
```

A file that is missing, empty, or lacks one of the required columns cannot be
imported at all: an error is shown and the command exits with code 1.
