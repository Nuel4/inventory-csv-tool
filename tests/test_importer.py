from decimal import Decimal
from pathlib import Path

import pytest

from app.importer import ImportFileError, load_inventory, parse_price, parse_whole_number


def reasons(path: Path) -> dict[int, str]:
    return {e.row: e.reason for e in load_inventory(path).errors}


def test_sample_file_valid_and_invalid_rows(sample_csv: Path) -> None:
    result = load_inventory(sample_csv)
    assert len(result.items) == 12
    assert [e.row for e in result.errors] == [14, 15, 16]
    assert "quantity" in result.errors[0].reason
    assert "category" in result.errors[1].reason
    assert "duplicate" in result.errors[2].reason


def test_valid_row_parsed(write_csv) -> None:
    item = load_inventory(write_csv("A-1,Pen,Stationery,5,2.30,3\n")).items[0]
    assert (item.sku, item.name, item.category) == ("A-1", "Pen", "Stationery")
    assert (item.quantity, item.unit_price, item.reorder_level) == (5, Decimal("2.30"), 3)


def test_duplicate_sku_keeps_first_and_reports_later(write_csv) -> None:
    path = write_csv(
        "A-1,First,Kitchen,1,1.00,0\n"
        "A-1,Second,Kitchen,2,2.00,0\n"
        "A-1,Third,Kitchen,3,3.00,0\n"
    )
    result = load_inventory(path)
    assert [i.name for i in result.items] == ["First"]
    assert [e.row for e in result.errors] == [3, 4]
    assert all("duplicate sku 'A-1'" in e.reason for e in result.errors)
    assert "first seen on row 2" in result.errors[0].reason


@pytest.mark.parametrize(
    "row, expected",
    [
        (",Pen,Stationery,1,1.00,0", "sku is required"),
        ("A-1,Pen,Toys,1,1.00,0", "category must be one of"),
        ("A-1,Pen,stationery,1,1.00,0", "category must be one of"),
        ("A-1,Pen,Stationery,-1,1.00,0", "quantity must be a whole number"),
        ("A-1,Pen,Stationery,1.5,1.00,0", "quantity must be a whole number"),
        ("A-1,Pen,Stationery,abc,1.00,0", "quantity must be a whole number"),
        ("A-1,Pen,Stationery,,1.00,0", "quantity must be a whole number"),
        ("A-1,Pen,Stationery,1,1.00,-3", "reorder_level must be a whole number"),
        ("A-1,Pen,Stationery,1,-0.50,0", "unit_price must be >= 0"),
        ("A-1,Pen,Stationery,1,1.999,0", "at most 2 decimal places"),
        ("A-1,Pen,Stationery,1,free,0", "unit_price must be a number"),
        ("A-1,Pen,Stationery,1,NaN,0", "unit_price must be a number"),
        ("A-1,Pen,Stationery", "quantity must be a whole number"),
    ],
)
def test_invalid_rows_reported_with_row_and_reason(write_csv, row: str, expected: str) -> None:
    result = load_inventory(write_csv("B-1,Ok,Kitchen,1,1.00,0\n" + row + "\n"))
    assert [i.sku for i in result.items] == ["B-1"]
    assert len(result.errors) == 1
    assert result.errors[0].row == 3
    assert expected in result.errors[0].reason


def test_invalid_rows_never_silently_dropped(write_csv) -> None:
    path = write_csv("A,x,Kitchen,1,1,0\nB,x,Toys,1,1,0\nC,x,Kitchen,-1,1,0\n")
    result = load_inventory(path)
    assert len(result.items) + len(result.errors) == 3


def test_blank_line_does_not_shift_row_numbers(write_csv) -> None:
    assert list(reasons(write_csv("A,x,Kitchen,1,1,0\n\nB,x,Toys,1,1,0\n"))) == [4]


@pytest.mark.parametrize("value", ["0", "7", " 12 "])
def test_parse_whole_number_ok(value: str) -> None:
    assert parse_whole_number(value, "quantity") == int(value)


@pytest.mark.parametrize("value", ["0", "4.99", "12.5", "100"])
def test_parse_price_ok(value: str) -> None:
    assert parse_price(value) == Decimal(value)


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ImportFileError, match="cannot read"):
        load_inventory(tmp_path / "nope.csv")


def test_empty_file_raises(write_csv) -> None:
    with pytest.raises(ImportFileError, match="empty"):
        load_inventory(write_csv("", header=False))


def test_missing_column_raises(write_csv) -> None:
    path = write_csv("sku,name,category,quantity\nA,x,Kitchen,1\n", header=False)
    with pytest.raises(ImportFileError, match="unit_price, reorder_level"):
        load_inventory(path)


def test_excel_bom_header_accepted(tmp_path: Path) -> None:
    path = tmp_path / "bom.csv"
    path.write_text("﻿sku,name,category,quantity,unit_price,reorder_level\nA,x,Kitchen,1,1,0\n", encoding="utf-8")
    assert len(load_inventory(path).items) == 1
