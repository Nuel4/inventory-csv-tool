# PROCESS — Run 3

Date: 2026-11-18

## Sources used

Only `SPEC.md` and `samples/inventory_sample.csv`, as TASK.md says. Where
the two Decisions sections overlap, "Decisions (added after Run 2)" wins over
"Decisions (added after Run 1)", which wins over the rest of the spec. I did
not look at the code on the `feature/v1` or `feature/v1-run2` branches, or at
the old `.pyc` / `egg-info` / `.venv` leftovers in the folder.

## Steps and commands

1. Read the task, spec and sample:
   `cat TASK.md`, `cat SPEC.md`, `cat samples/inventory_sample.csv`,
   `cat .gitignore`, `git ls-files`.
2. Checked the starting state: `git branch -a`, `git remote -v`,
   `gh auth status`. Main had only `.gitignore`, `SPEC.md`, `TASK.md` and
   the sample tracked. `app/` and `tests/` held only stale `__pycache__`
   folders (untracked).
3. `git pull` on main → "Already up to date."
4. `git ls-remote --heads origin feature/v1-run3` and `git branch -a` → the
   branch did not exist locally or on GitHub, so nothing had to be deleted.
   `git checkout -b feature/v1-run3`.
5. Removed the untracked stale caches: `rm -rf app/__pycache__ tests/__pycache__ .pytest_cache`.
6. Wrote `pyproject.toml` (package `app`, console script `inventory`,
   Python >= 3.11, dependency `typer`, dev extra `pytest`).
7. Wrote the code, one module per job:
   - `app/importer.py` – read the CSV, trim cells, validate rows, duplicate SKUs.
   - `app/state.py` – save/load `.inventory_state`.
   - `app/search.py` – name / category search.
   - `app/reports.py` – low-stock and summary.
   - `app/exporter.py` – CSV export of items and of the summary.
   - `app/updater.py` – `update` command logic and `.bak` backup.
   - `app/cli.py` – Typer commands.
8. `.venv/bin/pip install -q -e .` into the existing local `.venv`
   (Python 3.11.13, typer 0.29.1, pytest 9.2.0), then ran every command by
   hand against a copy of the sample file in a temporary folder.
9. Wrote tests, one file per module (`tests/test_<module>.py`) plus
   `tests/conftest.py`. An autouse fixture moves every test into its own
   `tmp_path`, so no test touches the real folder or depends on the machine.
10. `.venv/bin/python -m pytest -q` → **92 passed**.
11. Checked conventions with a small `ast` script: every function in `app/`
    and `tests/` has type hints and is under 25 lines.
12. Mutation check: temporarily changed the importer so invalid rows also
    claim a SKU → 4 tests failed (as they should); restored the file →
    92 passed again.
13. Wrote `README.md` and ran its import example for real to make sure the
    shown output matches exactly.
14. Wrote `PROMPTS.md` (TASK.md copied verbatim, checked with `diff`) and
    this file.
15. Checked `git status` so that no `.venv`, `.bak`, `.inventory_state`,
    `.env`, `egg-info` or cache files are staged, committed, pushed the
    branch and opened the PR with `gh pr create --base main`.

## How each Decision / feature is implemented and tested

| Requirement | Code | Tests |
|---|---|---|
| Import + validate every row, row number + reason | `importer.validate_rows`, `cli.import_file` | `test_importer.py` (parametrized invalid cases), `test_cli.py::test_import_saves_state_and_lists_every_invalid_row` |
| Search by name (partial, any case) / category | `search.search_items` | `test_search.py`, `test_cli.py::test_search_*` |
| Low stock (quantity ≤ reorder_level) | `reports.low_stock` | `test_reports.py`, `test_cli.py::test_low_stock` |
| Export on search, low-stock **and** summary | `exporter.py`, `--export` on all three | `test_exporter.py`, `test_cli.py::test_*_export` |
| Summary: total items (distinct SKUs) and total units | `reports.summarize` | `test_reports.py`, `test_cli.py::test_summary_shows_items_units_and_all_categories` |
| State in `.inventory_state`, no default file, "No file imported yet" + exit 1 | `state.py`, `cli.load_current` | `test_state.py`, `test_cli.py::test_commands_without_import_*`, `test_commands_read_file_from_state_not_a_default` |
| `.inventory_state` in `.gitignore` | `.gitignore` (already there on main) | `test_state.py::test_state_file_is_gitignored` |
| Full invalid list only on import, one line elsewhere | `cli.import_file`, `cli.load_current` | `test_cli.py::test_other_commands_show_one_line_warning` |
| Duplicate SKU: keep first; only VALID rows claim a SKU | `importer.validate_rows` (`sku_rows` only filled by valid rows) | `test_importer.py::test_duplicate_sku_keeps_first_row`, `::test_invalid_first_row_does_not_claim_sku` |
| Summary export: one row per category, category/items/units/value | `exporter.export_summary` | `test_exporter.py`, `test_cli.py::test_summary_export_has_all_four_categories` |
| All four categories always shown, 0 when empty (screen + export) | `reports.summarize` loops over `CATEGORIES` | `test_reports.py::test_summary_always_lists_all_four_categories_with_zeros`, CLI summary tests |
| No stray blank lines at the start of output | output starts directly with content | `test_cli.py::test_no_blank_line_at_start_of_output` |
| Python 3.11+ only | `requires-python = ">=3.11"` in `pyproject.toml` | Not tested on purpose — the Run 2 decision forbids tests that check the Python version in use. |
| Tests check behaviour only, nothing machine-dependent | all tests use `tmp_path`, relative sample path, `CliRunner` | — |
| Trim leading/trailing spaces before validation; documented in README | `importer.validate_rows`, `importer.check_header` | `test_importer.py::test_cells_are_trimmed_before_validation`, `::test_trimmed_skus_count_as_duplicates`, `::test_header_with_spaces_is_accepted`; README "Validation details" |
| `update SKU --quantity N` | `updater.py`, `cli.update` | `test_updater.py`, `test_cli.py::test_update_*` |
| N must be whole number ≥ 0, else error + exit 1 | `updater.parse_quantity` | `-1`, `2.5`, `abc`, `""`, `1e3`, `+4` rejected |
| SKU not among valid rows → error + exit 1 | `updater.find_record` | unknown SKU and SKU that is only in an invalid row |
| Backup to `FILE.bak` before writing | `updater.update_quantity` (`shutil.copy2`) | `.bak` equals original byte for byte; no `.bak` on failure |
| Other rows (incl. invalid) and order unchanged | only the one raw record is rebuilt; every other record is written back as read | byte-for-byte test with invalid row, `""` quotes, spaces, CRLF, a quoted newline and no final newline |
| Nothing imported → same "No file imported yet" error | `cli.load_current` | `test_cli.py::test_commands_without_import_show_message_and_exit_1[update…]` |

## Decisions I made (things the spec does not say exactly)

- **Row numbers** count the header as row 1, so the first item is row 2 —
  this matches what the shop owner sees in a spreadsheet. If a quoted cell
  contains a line break, the number is the CSV record number, not the text
  line number.
- **Blank rows** are reported as invalid ("row is empty") instead of being
  skipped, because the spec says rows are never silently dropped.
- **Rows with the wrong number of cells** are reported as invalid.
- **Missing / empty file or missing required column**: the whole file is
  rejected with an error and exit code 1, and `.inventory_state` is not
  written. Extra columns are ignored.
- **Header names** are trimmed too (same reason as the cell trimming
  decision). A UTF-8 BOM at the start of the file (common in spreadsheet
  exports) is ignored.
- **A row with several problems** lists all of them in one reason, separated
  by `;`.
- **A row that is both invalid and has an already-used SKU** is reported for
  its own problems (not as a duplicate).
- **Number formats**: whole numbers must be plain digits (`+4`, `4.0`, `1e3`
  are invalid). Prices must be plain digits with an optional `.` and 1–2
  decimals (`3`, `3.5`, `3.75` valid; `.5`, `1e2` invalid).
- **Category** must match exactly, case included (`electronics` is invalid),
  because the spec lists the exact names.
- **Search by category** ignores case and must be the whole name. `--name`
  and `--category` together means both must match. With neither, an error
  is shown and exit code 1.
- **Warnings and errors go to stderr**, results go to stdout. This keeps the
  one-line warning separate from the result.
- **The one-line warning** uses the right word for one row ("1 invalid row
  skipped …"). Duplicate rows count as invalid rows in this number.
- **`.inventory_state` stores the full (absolute) path**, so commands keep
  working even if the CSV was given with a relative path.
- **Export** overwrites an existing file. Prices are written with 2 decimals.
  After exporting, a line "Exported N rows to FILE" is printed.
- **Summary screen** shows total stock value too (it is in the v1 feature
  list), with 2 decimals.
- **update**: the "No file imported yet" check runs first, then the quantity
  check, then the SKU check. The SKU argument is trimmed. If a SKU is
  duplicated, the kept (first valid) row is updated. An existing `.bak` is
  replaced. Nothing is written and no `.bak` is created when the command
  fails. Only the quantity cell of that one row is changed; that row is
  re-written with standard CSV quoting, every other row stays byte for byte.
- **update** also shows the one-line invalid-rows warning, like the other
  non-import commands.
- **`pyproject.toml`** was added so `pip install -e .` gives the
  `inventory` command shown in the spec's example usage. It is packaging
  only, not a new feature.

## Things I was unsure about

- **`name` column**: the spec gives no rule for it, so an empty name is
  accepted. If names should be required, that needs a new decision.
- **Category case**: I kept categories case-sensitive for validation but
  case-insensitive for `search --category`. The spec doesn't say either way.
- **Search with no filters**: I made it an error rather than listing every
  item, since the spec only describes searching by name or by category.
- **Line endings**: `update` keeps `\n` and `\r\n` endings. Files that use
  only `\r` (very old Mac format) are not handled specially.
- **Python 3.11+** is enforced only through `requires-python` in
  `pyproject.toml`; per the Run 2 decision there is no test for it.
- The local `.venv` and an old `inventory_csv_tool.egg-info` folder were
  already in the working folder. I reused the `.venv` (reinstalled the
  package into it) and did not commit either; both are in `.gitignore`.
