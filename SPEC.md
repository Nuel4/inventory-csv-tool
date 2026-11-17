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