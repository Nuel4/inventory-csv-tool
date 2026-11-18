# inventory-csv-tool

A small command-line tool for checking stock kept in a spreadsheet. Export
your inventory as CSV, import it once, then search items, list what's running
low, see a stock summary, and export any result to a new CSV (for example to
send to a supplier).

## Install

Requires **Python 3.11 or newer**.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"     # installs the `inventory` command and pytest
```

Run the tests:

```bash
pytest
```

## Usage

### 1. Import a file

```bash
inventory import samples/inventory_sample.csv
```

```
Imported 12 items from samples/inventory_sample.csv
3 invalid rows:
  Row 14: quantity must be a whole number >= 0 (got '-2')
  Row 15: category must be one of Electronics, Stationery, Kitchen, Cleaning (got 'Toys')
  Row 16: duplicate sku 'EL-001' (first seen on row 2)
```

`import` checks every row and lists every invalid row with its row number
(the header is row 1) and the reason. Invalid rows are skipped, never
silently dropped.

`import` also saves the file's path to `.inventory_state` in the current
folder. `search`, `low-stock` and `summary` read the file from there, so run
them from the same folder. Until a file has been imported they print
`No file imported yet. Run: inventory import FILE` and exit with code 1.
Importing another file replaces the saved path.

On the other commands, invalid rows are mentioned in one line only:

```
3 invalid rows skipped — run import for details
```

### 2. Search

```bash
inventory search --name "pen"            # case-insensitive, partial match
inventory search --category kitchen      # case-insensitive, exact category
inventory search --name mug --category Kitchen   # both filters must match
```

```
SKU     Name                          Category    Qty  Unit price  Reorder
------  ----------------------------  ----------  ---  ----------  -------
ST-001  Blue Ballpoint Pen (10 pack)  Stationery  120  2.30        50
```

### 3. Low-stock report

Items whose quantity is at or below their reorder level:

```bash
inventory low-stock
```

### 4. Summary

```bash
inventory summary
```

```
Total items: 12
Total units: 312
Total stock value: 1302.16

Category     Items  Units  Value
-----------  -----  -----  ------
Electronics  3      56     369.55
Stationery   3      141    375.45
Kitchen      3      46     382.56
Cleaning     3      69     174.60
```

- **Total items** = number of distinct SKUs
- **Total units** = sum of quantity
- **Stock value** = sum of quantity × unit_price

### 5. Export

`search`, `low-stock` and `summary` all accept `--export FILE`. The result is
still printed, and also written to `FILE` (an existing file is overwritten).

```bash
inventory search --name "pen" --export pens.csv
inventory low-stock --export low_stock.csv
inventory summary --export summary.csv
```

`search` and `low-stock` exports use the same columns as the input file:

```csv
sku,name,category,quantity,unit_price,reorder_level
EL-002,Wireless Mouse,Electronics,8,12.50,10
CL-003,Glass Cleaner,Cleaning,0,3.10,5
```

`summary` exports one row per category:

```csv
category,items,units,value
Electronics,3,56,369.55
Stationery,3,141,375.45
Kitchen,3,46,382.56
Cleaning,3,69,174.60
```

## CSV format

The first row must be this header (column order does not matter; extra
columns are ignored):

```csv
sku,name,category,quantity,unit_price,reorder_level
EL-001,USB-C Cable 1m,Electronics,45,4.99,20
ST-002,A4 Notebook,Stationery,15,3.75,20
```

| Column          | Rule                                                        |
|-----------------|-------------------------------------------------------------|
| `sku`           | Required and unique. If a SKU repeats, the first row is kept and later rows are reported as duplicates. |
| `name`          | Item name (used by `search --name`).                        |
| `category`      | One of `Electronics`, `Stationery`, `Kitchen`, `Cleaning` (exact spelling). |
| `quantity`      | Whole number ≥ 0                                            |
| `unit_price`    | Number ≥ 0 with at most 2 decimal places                    |
| `reorder_level` | Whole number ≥ 0                                            |

Examples of rows that are rejected:

```csv
EL-004,HDMI Cable 2m,Electronics,-2,8.99,5      # quantity below 0
ST-004,Highlighter Set,Toys,25,4.50,10          # unknown category
EL-001,USB-C Cable 2m,Electronics,10,6.49,5     # duplicate sku
XX-001,Thing,Kitchen,1,1.999,0                  # more than 2 decimal places
```

If the file is missing, empty, or its header lacks a required column,
`import` prints an error and exits with code 1 without saving anything.

## Project layout

```
app/        code (cli, importer, search, reports, exporter, state)
tests/      pytest tests, one file per module
samples/    sample inventory CSV
```
