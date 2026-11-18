# Process — Run 2

Date: 2026-11-18

## Sources used
Only `SPEC.md` (including "Decisions (added after Run 1)") and
`samples/inventory_sample.csv`, as TASK.md requires. The `feature/v1` branch,
the existing `.venv/`, `inventory_csv_tool.egg-info/` and the old
`__pycache__` folders in `app/` and `tests/` were left unread.

## Steps and commands

1. Synced and checked branches.
   ```
   git pull                      # "Already up to date."
   git branch -a                 # feature/v1 and main only
   git ls-remote --heads origin  # feature/v1 and main only
   ```
   No `feature/v1-run2` existed locally or on origin, so there was nothing to delete.
2. Read `TASK.md`, `SPEC.md`, `.gitignore`, `samples/inventory_sample.csv`.
   Checked `git ls-files` / `git status --ignored`: `app/` and `tests/` only
   held stale, untracked `__pycache__` files from Run 1.
3. Created the branch from main and removed the stale caches so Run 1
   bytecode could not affect test runs:
   ```
   git checkout -b feature/v1-run2
   rm -rf app/__pycache__ tests/__pycache__
   ```
4. Created a fresh Python 3.11 virtualenv **outside the repo** (in a session
   scratch folder) rather than reusing Run 1's `.venv`:
   ```
   python3.11 -m venv <scratch>/venv
   <scratch>/venv/bin/pip install typer pytest   # typer 0.29.1, pytest 9.2.0
   <scratch>/venv/bin/pip install -e .
   ```
   (`pip install -e .` regenerates `inventory_csv_tool.egg-info/`, which is
   gitignored.)
5. Wrote the code in `app/`: `importer.py`, `search.py`, `reports.py`,
   `exporter.py`, `state.py`, `cli.py`, plus `pyproject.toml`.
6. Smoke-tested every command by hand in an empty scratch folder
   (`summary` before import, `import`, `search --name/--category`,
   `low-stock --export`, `summary --export`, `search` without filters).
   Totals were checked by hand, e.g. Electronics = 45×4.99 + 8×12.50 + 3×15.00 = 369.55.
7. Wrote tests in `tests/` and ran them:
   ```
   <scratch>/venv/bin/python -m pytest -q    # 86 passed
   ```
8. Checked with a small `ast` script that every function in `app/` has a
   return type hint and is under ~30 lines (the longest is ~20).
9. Wrote `README.md`, `PROMPTS.md` (TASK.md copied verbatim under "Run 2"
   with today's date) and this file.
10. Committed on `feature/v1-run2`, pushed the branch, opened a PR into
    `main` with `gh pr create`. Nothing was pushed to main.

## How each Decision is implemented and tested

| Decision | Implementation | Tests |
|---|---|---|
| `import FILE` saves the path to `.inventory_state` in the current folder; other commands read it; no hardcoded default | `app/state.py`; `cli.load_current()` | `test_state.py` (all); `test_cli.py::test_import_saves_path_to_state_file`, `test_other_commands_read_file_from_state`, `test_latest_import_replaces_previous`, `test_no_hardcoded_default_file` |
| Nothing imported → exact message, exit code 1 | `state.NO_IMPORT_MESSAGE`, `cli.fail()` | `test_cli.py::test_commands_without_import_fail_with_message` (search, low-stock, summary); `test_state.py::test_no_state_file_raises` |
| `.inventory_state` in `.gitignore` | Already present in `.gitignore` on main | `test_cli.py::test_inventory_state_is_gitignored` |
| Full invalid-row list only on `import`; one line elsewhere | `cli.show_row_errors()` vs. one-line warning in `cli.load_current()` | `test_cli.py::test_import_shows_full_list_of_invalid_rows`, `test_other_commands_show_one_line_only` (×3), `test_one_line_warning_singular`, `test_no_warning_when_all_rows_valid` |
| Duplicate SKU: keep first, report later ones | `importer.validate_rows()` | `test_importer.py::test_duplicate_sku_keeps_first_and_reports_later`, `test_sample_file_valid_and_invalid_rows`; `test_cli.py::test_duplicate_sku_first_row_kept` |
| Summary shows total items (distinct SKUs) AND total units | `reports.summarize()`, `cli.show_summary()` | `test_reports.py::test_summary_items_and_units_are_both_reported`, `test_summary_sample`; `test_cli.py::test_summary_shows_items_and_units` |
| `--export` on search, low-stock and summary; summary export = category, items, units, value | `exporter.export_items()`, `exporter.export_summary()`, `--export` option on all three commands | `test_exporter.py` (all); `test_cli.py::test_search_export`, `test_low_stock_export`, `test_summary_export_one_row_per_category` |
| No stray blank lines at the start of any output | Every command's first `echo` is real content | `test_cli.py::test_no_leading_blank_lines` (×5), `test_no_leading_blank_line_before_error` |
| Python 3.11+ only | `requires-python = ">=3.11"` in `pyproject.toml`; code uses 3.10+ syntax and `tomllib` (3.11) in tests | `test_project.py::test_requires_python_311_or_newer`, `test_running_on_python_311_or_newer` |

## Decisions I made (not spelled out in the spec)

- **Module layout:** `importer`, `search`, `reports` (low-stock + summary),
  `exporter`, `state`, `cli`. One test file per module.
- **Row numbers** are file line numbers: header = row 1, first data row =
  row 2 (what a spreadsheet shows). Blank lines are counted, so numbers still
  match the file.
- **Validation messages** use `>=` (ASCII) rather than `≥`, to avoid
  terminal encoding issues.
- **Category** must match exactly (case-sensitive) when importing, because
  the spec lists exact values. `search --category` matches case-insensitively
  because the spec says search is case-insensitive.
- **Search** with both `--name` and `--category` returns items matching both.
  With neither, it prints `Error: give --name and/or --category` and exits 1.
- **Header problems** (missing file, empty file, missing required column)
  stop `import` with an error and exit code 1, and the state file is *not*
  written. Extra columns are ignored. A UTF-8 BOM (Excel export) is accepted.
- **Stored path** is absolute, so the commands still work if a relative path
  was given to `import`.
- **If the imported file was deleted/moved later**, other commands print
  `Error: cannot read …. Run: inventory import FILE` and exit 1.
- **The one-line warning** goes to stderr so stdout stays clean for the
  table; it is the first line printed. It uses singular "1 invalid row
  skipped" for one row.
- **Export:** results are still printed; the export file is overwritten if
  it exists; a header-only CSV is written when there are no results; the
  command prints `Exported N rows to FILE`. Prices are written with 2
  decimals (e.g. `2.3` → `2.30`). Unwritable export path → error, exit 1.
- **Summary** lists only categories that have items, in the spec's order
  (Electronics, Stationery, Kitchen, Cleaning). Money is shown with 2
  decimals. Calculations use `Decimal`, not float.
- **`import` exit code** is 0 even when some rows are invalid (they are
  reported, and the valid rows are usable).

## Things I was unsure about

- **Duplicate of an invalid row:** if the first row with a SKU is *invalid*
  and a later row with the same SKU is valid, I keep the later valid row
  (only valid rows "claim" a SKU). The spec says "keep the first row"; it
  doesn't say whether an invalid first row counts.
- **Empty `name`:** the spec only marks `sku` as required, so an empty name is
  accepted. Tell me if name should be required.
- **Leading/trailing spaces** in cells are trimmed before validation. The
  spec doesn't say whether `" Kitchen"` should be valid.
- **Categories with no items** are left out of the summary and summary
  export. Showing all four with zeros would also be reasonable.
- **Where the one-line warning goes:** I chose stderr, printed first. The
  spec only says "one line only".
- **Search without filters:** I made it an error rather than listing all
  items, since listing everything isn't a v1 feature.
- **Test file for project-level checks:** "one test file per module" — the
  `requires-python` checks don't belong to an `app/` module, so they are in
  `tests/test_project.py`. The `.gitignore` check is in `test_cli.py`
  next to the other state tests.
- **The sample file has a duplicate `EL-001`** and two other invalid rows,
  so importing it always prints 3 invalid rows. I took this to be on purpose
  and did not change the sample.

## What was not built (out of scope)
No database, web API, frontend, accounts or auth. No extra commands or options
beyond the spec and Decisions.
