# PROCESS - Run 1 (2026-11-17)

## Steps and commands

1. **Read the inputs.** I read `TASK.md`, `SPEC.md` and `samples/inventory_sample.csv` and used nothing else as a source.
   - `ls -la`, `cat TASK.md`, `cat SPEC.md`, `cat samples/inventory_sample.csv`
2. **Checked the environment.**
   - `git remote -v` showed origin `https://github.com/Nuel4/inventory-csv-tool.git`
   - `gh auth status` showed I was logged in as `Nuel4` with `repo` scope
   - `python3 --version` gave 3.10.9, which is not the 3.11 the spec asks for. `which python3.11` found `/usr/local/bin/python3.11` (3.11.13), so I used that.
3. **Created the branch.** `git checkout -b feature/v1`. All work was done on this branch.
4. **Created a virtual environment.** `.venv` is git-ignored.
   - `python3.11 -m venv .venv`
   - `.venv/bin/pip install --upgrade pip`
   - `.venv/bin/pip install "typer>=0.12" pytest` installed typer 0.29.1 and pytest 9.2.0
5. **Wrote the code** in `app/`: `importer.py`, `search.py`, `reports.py`, `exporter.py`, `cli.py`. I also added `pyproject.toml` (declares the `inventory` command) and `.gitignore`.
6. **Installed and ran the spec's example commands** against the sample:
   - `.venv/bin/pip install -e ".[dev]"`
   - `inventory import samples/inventory_sample.csv`, `inventory search --name pen`,
     `inventory search -c kitchen`, `inventory low-stock --export <scratch>/low.csv`, `inventory summary`
   - I checked one result by hand. The Electronics stock value is 45×4.99 + 8×12.50 + 3×15.00 = 369.55, which matches the output.
7. **Wrote the tests** in `tests/`, one file per module: `test_importer.py`, `test_search.py`, `test_reports.py`, `test_exporter.py`, `test_cli.py`. Shared fixtures are in `conftest.py`.
8. **First test run: `.venv/bin/pytest -q` gave 2 failed, 49 passed.** Both failures were mistakes in my test fixture, not in the code: the item "Pencil Case" contains "pen", so it correctly matched `--name pen`. I renamed it to "Notebook" and updated the expected results.
9. **Added type hints to the test functions and fixtures.** The spec asks for type hints on all functions. My first try imported `click.testing.Result`, but click isn't installed with typer 0.29, so test collection failed. I switched to `typer.testing.Result`.
10. **Second test run: `.venv/bin/pytest -q` gave 51 passed.**
11. **Checked the conventions** with a small `ast` script. Every function in `app/` and `tests/` has a return type hint, and none is longer than 25 lines.
12. **Wrote the docs.** `README.md`, this file, and `PROMPTS.md`. I checked with `diff` that the TASK.md copy in PROMPTS.md matches the original; the only difference is a trailing newline.
13. **Committed, pushed `feature/v1`, and opened a PR into `main`** with `gh pr create`. Nothing was pushed to `main`.

## Design decisions

- **Module layout.** Each module has one job: `importer` (parse and validate), `search`, `reports` (low-stock and summary), `exporter`, `cli` (Typer). Each one has its own test file, as the spec asks.
- **Money uses `Decimal`, not `float`.** This makes the "max 2 decimal places" check exact and keeps stock values like 1302.16 from picking up float rounding errors.
- **Validation stops at the first problem in a row.** Each invalid row gets one reason. Validation order: sku required → sku unique → category → quantity → unit_price → reorder_level.
- **Every invalid row is reported** as `Invalid row <n>: <reason>` on stderr by every command, not only `import`. That way rows are never silently dropped, whichever command you run.
- **A file that can't be used at all** (missing, or missing a required column) is a hard error with exit code 1. That isn't a row problem, so there's no row number to report.
- **`--export` writes the input's six columns**, with `unit_price` at 2 decimal places, so an exported file can be imported again. There's a round-trip test for this.
- **Packaging.** `pyproject.toml` declares an `inventory` script so the spec's example commands work exactly as written.

## Points I was unsure about (and what I chose)

1. **How `import` relates to the other commands.** The spec shows `inventory import FILE` followed by `inventory search --name "pen"` with no file. That suggests import remembers the data, but the spec also says "No database - CSV in, CSV out". I didn't add any saved state, since that would be close to building a database. Instead:
   - `import FILE` validates the file and reports the results.
   - `search`, `low-stock` and `summary` read the CSV every time they run, from `--file/-f`, which defaults to `samples/inventory_sample.csv`. That default makes the spec's examples work as written. If the owner wants `import` to set the file for later commands, that needs a decision.
2. **Duplicate SKUs.** The sample has `EL-001` twice. I keep the first occurrence and report the later one as `duplicate sku`. The alternative would be rejecting both rows.
3. **Row numbering.** Row numbers count the header as row 1, so the first data row is row 2. This matches what a spreadsheet shows. In the sample, the invalid rows are 14, 15 and 16.
4. **What "total items" means in `summary`.** I used the number of valid items (distinct SKUs), not the total units in stock (sum of quantity). I didn't add a units total, to avoid building outside the spec.
5. **"Export any search or report result."** `--export` is on `search` and `low-stock`. I didn't add it to `summary`, because the spec lists summary separately from "search or report" and its output doesn't fit the item-row CSV format. This needs confirming.
6. **Search details.** `--category` is a case-insensitive *exact* match; only `--name` is described as partial. Giving both means AND. Giving neither is a usage error (exit code 2).
7. **Category in the data file is case-sensitive.** `electronics` in the CSV is rejected, because the spec lists the exact values. Only the search option is case-insensitive.
8. **`name` has no rules.** The spec gives none, so an empty name is accepted.
9. **Number formats.** Quantity and reorder level must be written as plain integers, so `5.0` is rejected. `unit_price` accepts anything Python's `Decimal` parses (for example `3`, `12.5`, `1e1`) as long as it's finite, ≥ 0 and has at most 2 decimal places. `NaN` and `Infinity` are rejected.
10. **Python version.** The default `python3` on this machine is 3.10. Development and tests ran on 3.11.13, and `pyproject.toml` sets `requires-python = ">=3.11"`. I didn't test 3.12 or later.
11. **The `--file` default is relative to the current directory**, so it only works when you run the command from the repo root. Elsewhere, pass `--file`.
12. **PROMPTS.md.** The task said to copy TASK.md "with today's date and the heading 'Run 1'". I used `# Run 1` as the heading and put the date under it, then the TASK.md text verbatim in a code block.

## Out of scope (not built, as the spec says)

No database or saved state, no web API or frontend, no auth. No secrets or `.env` files. `.env` is git-ignored, and `.venv/` is not committed.
