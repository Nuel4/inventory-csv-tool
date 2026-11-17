"""Tests for app/importer.py."""

from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import pytest

from app.importer import CsvFormatError, RowError, load_csv, parse_price, parse_whole_number


def test_sample_file_valid_and_invalid_rows(sample_csv: Path) -> None:
    result = load_csv(sample_csv)
    assert len(result.items) == 12
    assert result.errors == [
        RowError(14, "quantity must be >= 0, got -2"),
        RowError(15, "category must be one of Electronics, Stationery, Kitchen, Cleaning, got 'Toys'"),
        RowError(16, "duplicate sku 'EL-001'"),
    ]


def test_valid_row_is_parsed(write_csv: Callable[..., Path]) -> None:
    result = load_csv(write_csv("EL-001,Cable,Electronics,45,4.99,20"))
    assert result.errors == []
    item = result.items[0]
    assert (item.sku, item.name, item.category) == ("EL-001", "Cable", "Electronics")
    assert (item.quantity, item.unit_price, item.reorder_level) == (45, Decimal("4.99"), 20)


@pytest.mark.parametrize(
    ("row", "reason"),
    [
        (",Cable,Electronics,1,1.00,1", "sku is required"),
        ("EL-1,Cable,Toys,1,1.00,1", "category must be one of"),
        ("EL-1,Cable,electronics,1,1.00,1", "category must be one of"),
        ("EL-1,Cable,Electronics,-1,1.00,1", "quantity must be >= 0"),
        ("EL-1,Cable,Electronics,1.5,1.00,1", "quantity must be a whole number"),
        ("EL-1,Cable,Electronics,abc,1.00,1", "quantity must be a whole number"),
        ("EL-1,Cable,Electronics,,1.00,1", "quantity must be a whole number"),
        ("EL-1,Cable,Electronics,1,1.00,-3", "reorder_level must be >= 0"),
        ("EL-1,Cable,Electronics,1,1.00,x", "reorder_level must be a whole number"),
        ("EL-1,Cable,Electronics,1,-0.01,1", "unit_price must be >= 0"),
        ("EL-1,Cable,Electronics,1,1.999,1", "unit_price must have at most 2 decimal places"),
        ("EL-1,Cable,Electronics,1,abc,1", "unit_price must be a number"),
        ("EL-1,Cable,Electronics,1,NaN,1", "unit_price must be a number"),
        ("EL-1,Cable,Electronics,1", "unit_price must be a number"),
    ],
)
def test_invalid_row_reported_with_row_number_and_reason(write_csv: Callable[..., Path], row: str, reason: str) -> None:
    result = load_csv(write_csv("OK-1,Fine,Kitchen,1,1.00,1", row))
    assert [item.sku for item in result.items] == ["OK-1"]
    assert len(result.errors) == 1
    assert result.errors[0].row == 3
    assert reason in result.errors[0].reason


def test_duplicate_sku_keeps_first_and_reports_later(write_csv: Callable[..., Path]) -> None:
    result = load_csv(write_csv("A-1,First,Kitchen,1,1.00,1", "A-1,Second,Kitchen,2,2.00,2"))
    assert [item.name for item in result.items] == ["First"]
    assert result.errors == [RowError(3, "duplicate sku 'A-1'")]


def test_every_invalid_row_is_reported(write_csv: Callable[..., Path]) -> None:
    result = load_csv(write_csv("A,x,Toys,1,1,1", "B,x,Kitchen,-1,1,1", "C,x,Kitchen,1,1,1"))
    assert [error.row for error in result.errors] == [2, 3]
    assert [item.sku for item in result.items] == ["C"]


def test_zero_values_are_valid(write_csv: Callable[..., Path]) -> None:
    result = load_csv(write_csv("Z-1,Free,Cleaning,0,0,0"))
    assert result.errors == []
    assert result.items[0].unit_price == Decimal("0")


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(CsvFormatError, match="file not found"):
        load_csv(tmp_path / "nope.csv")


def test_missing_column_raises(write_csv: Callable[..., Path]) -> None:
    path = write_csv("A,x,Kitchen,1,1", header="sku,name,category,quantity,unit_price\n")
    with pytest.raises(CsvFormatError, match="reorder_level"):
        load_csv(path)


def test_parse_whole_number() -> None:
    assert parse_whole_number(" 7 ", "quantity") == 7
    with pytest.raises(ValueError):
        parse_whole_number("7.0", "quantity")


def test_parse_price() -> None:
    assert parse_price("12.5") == Decimal("12.5")
    assert parse_price("3") == Decimal("3")
    with pytest.raises(ValueError):
        parse_price("1e-5")
