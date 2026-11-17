# inventory-csv-tool

A small command-line tool for checking stock kept in a spreadsheet. Export your
inventory as CSV, then use it to validate the file, search items, see what's
running low, export a filtered list for a supplier, and get a stock-value summary.

CSV in, CSV out. There's no database, no web interface and no accounts.

## Install

Requires Python 3.11+.

```bash
git clone https://github.com/Nuel4/inventory-csv-tool.git
cd inventory-csv-tool
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"     # installs the `inventory` command, plus pytest
```

Run the tests:

```bash
pytest
```

## Usage

```bash
inventory import samples/inventory_sample.csv
inventory search --name "pen"
inventory search --category kitchen
inventory search --name "cable" --category Electronics --export cables.csv
inventory low-stock --export low_stock.csv
inventory summary
inventory --help            # or: inventory <command> --help
```

| Command | What it does |
|---|---|
| `import FILE` | Reads and validates every row. Prints how many items are valid and lists each invalid row with its row number and reason. |
| `search --name TEXT` / `--category NAME` | `--name` is a case-insensitive partial match on the item name. `--category` is a case-insensitive exact match on the category. If you give both, items must match both. You need at least one. |
| `low-stock` | Lists items whose `quantity` is at or below their `reorder_level`. |
| `summary` | Shows the total number of items and the total stock value (`quantity × unit_price`), overall and per category. |

Options:

- `--file / -f PATH`: the CSV to read for `search`, `low-stock` and `summary`. Defaults to
  `samples/inventory_sample.csv`, relative to where you run the command.
- `--export / -e PATH`: on `search` and `low-stock`, also writes the result to a new
  CSV file in the same format as the input.

Invalid rows are never dropped silently. Every command prints them to stderr as
`Invalid row <n>: <reason>` and then works with the valid rows only. If the file is
missing or doesn't have the required columns, the command exits with code 1.

### Example output

```text
$ inventory import samples/inventory_sample.csv
Invalid row 14: quantity must be >= 0, got -2
Invalid row 15: category must be one of Electronics, Stationery, Kitchen, Cleaning, got 'Toys'
Invalid row 16: duplicate sku 'EL-001'
Imported 12 valid item(s); 3 invalid row(s).

$ inventory low-stock --export low_stock.csv
SKU      NAME                           CATEGORY       QTY    PRICE REORDER
EL-002   Wireless Mouse                 Electronics      8    12.50      10
EL-003   Phone Charger 20W              Electronics      3    15.00       5
ST-002   A4 Notebook                    Stationery      15     3.75      20
KI-002   Chef Knife 20cm                Kitchen          4    24.99       5
CL-002   Microfibre Cloth (5 pack)      Cleaning         9     6.40      10
CL-003   Glass Cleaner                  Cleaning         0     3.10       5
Exported 6 item(s) to low_stock.csv

$ inventory summary
Total items: 12
Total stock value: 1302.16
By category:
  Cleaning     items:   3  value:     174.60
  Electronics  items:   3  value:     369.55
  Kitchen      items:   3  value:     382.56
  Stationery   items:   3  value:     375.45
```

(The `Invalid row` lines also appear before `search`, `low-stock` and `summary` output when you use the sample file. They're left out above to save space.)

## CSV format

The first line must be this header. Column order doesn't matter, but all six columns are required:

```csv
sku,name,category,quantity,unit_price,reorder_level
EL-001,USB-C Cable 1m,Electronics,45,4.99,20
ST-001,Blue Ballpoint Pen (10 pack),Stationery,120,2.30,50
```

| Column | Rule |
|---|---|
| `sku` | Required and unique. If a SKU appears again, the later row is reported as a duplicate and the first one is kept. |
| `name` | Free text. |
| `category` | Exactly one of `Electronics`, `Stationery`, `Kitchen`, `Cleaning` (case-sensitive). |
| `quantity` | Whole number ≥ 0. |
| `unit_price` | Number ≥ 0 with at most 2 decimal places. |
| `reorder_level` | Whole number ≥ 0. |

Examples of invalid rows and the reported reason:

```csv
EL-004,HDMI Cable 2m,Electronics,-2,8.99,5      -> quantity must be >= 0, got -2
ST-004,Highlighter Set,Toys,25,4.50,10          -> category must be one of ..., got 'Toys'
EL-005,Adapter,Electronics,3,1.999,5            -> unit_price must have at most 2 decimal places
```

Row numbers count the header as row 1, so they match the row numbers you see in a spreadsheet.
Exported files use the same columns, with `unit_price` always written to 2 decimal places.

## Project layout

```text
app/        importer.py (load + validate), search.py, reports.py, exporter.py, cli.py
tests/      one test file per module
samples/    inventory_sample.csv
```
