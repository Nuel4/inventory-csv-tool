from decimal import Decimal
from pathlib import Path

import pytest

from app.importer import InventoryFileError, load_inventory, parse_price, parse_whole_number
from tests.conftest import write_csv

SAMPLE = Path(__file__).resolve().parent.parent / "samples" / "inventory_sample.csv"


def reasons(path: Path) -> dict[int, str]:
    return {row.row_number: row.reason for row in load_inventory(path).invalid_rows}


def test_valid_row_is_loaded(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "EL-001,Cable,Electronics,5,4.99,2\n")
    result = load_inventory(path)
    assert len(result.items) == 1
    item = result.items[0]
    assert (item.sku, item.quantity, item.unit_price, item.reorder_level) == ("EL-001", 5, Decimal("4.99"), 2)
    assert result.invalid_rows == []


def test_sample_file_reports_three_invalid_rows() -> None:
    result = load_inventory(SAMPLE)
    assert len(result.items) == 12
    assert [row.row_number for row in result.invalid_rows] == [14, 15, 16]


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        (",Cable,Electronics,5,1.00,2", "sku is required"),
        ("EL-1,Cable,Toys,5,1.00,2", "category 'Toys'"),
        ("EL-1,Cable,electronics,5,1.00,2", "category 'electronics'"),
        ("EL-1,Cable,Electronics,-2,1.00,2", "quantity '-2'"),
        ("EL-1,Cable,Electronics,2.5,1.00,2", "quantity '2.5'"),
        ("EL-1,Cable,Electronics,abc,1.00,2", "quantity 'abc'"),
        ("EL-1,Cable,Electronics,5,1.00,-1", "reorder_level '-1'"),
        ("EL-1,Cable,Electronics,5,1.999,2", "unit_price '1.999'"),
        ("EL-1,Cable,Electronics,5,-1.00,2", "unit_price '-1.00'"),
        ("EL-1,Cable,Electronics,5,free,2", "unit_price 'free'"),
        ("EL-1,Cable,Electronics,5", "expected 6 cells, found 4"),
    ],
)
def test_invalid_row_reported_with_row_number_and_reason(tmp_path: Path, row: str, expected: str) -> None:
    path = write_csv(tmp_path, row + "\n")
    result = load_inventory(path)
    assert result.items == []
    assert len(result.invalid_rows) == 1
    assert result.invalid_rows[0].row_number == 2
    assert expected in result.invalid_rows[0].reason


def test_row_with_several_problems_lists_all_reasons(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "EL-1,Cable,Toys,-1,1.00,2\n")
    reason = reasons(path)[2]
    assert "category" in reason and "quantity" in reason


def test_blank_row_is_reported_not_dropped(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "EL-1,Cable,Electronics,5,1.00,2\n,,,,,\nEL-2,Mug,Kitchen,1,2.00,1\n")
    assert reasons(path) == {3: "row is empty"}


def test_price_with_one_or_no_decimals_is_valid(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "A,x,Kitchen,1,3,0\nB,y,Kitchen,1,3.5,0\nC,z,Kitchen,1,0,0\n")
    assert len(load_inventory(path).items) == 3


def test_duplicate_sku_keeps_first_row(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "EL-1,First,Electronics,5,1.00,2\nEL-1,Second,Electronics,9,1.00,2\n")
    result = load_inventory(path)
    assert [item.name for item in result.items] == ["First"]
    assert "duplicate sku 'EL-1'" in reasons(path)[3]


def test_invalid_first_row_does_not_claim_sku(tmp_path: Path) -> None:
    body = "EL-1,Bad,Electronics,-5,1.00,2\nEL-1,Good,Electronics,5,1.00,2\nEL-1,Later,Electronics,7,1.00,2\n"
    path = write_csv(tmp_path, body)
    result = load_inventory(path)
    assert [item.name for item in result.items] == ["Good"]
    found = reasons(path)
    assert "quantity" in found[2]
    assert "duplicate" in found[4]
    assert 3 not in found


def test_cells_are_trimmed_before_validation(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "  EL-1 ,  Cable  , Electronics , 5 , 4.99 , 2 \n")
    result = load_inventory(path)
    assert result.invalid_rows == []
    item = result.items[0]
    assert (item.sku, item.name, item.category, item.quantity) == ("EL-1", "Cable", "Electronics", 5)


def test_trimmed_skus_count_as_duplicates(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "EL-1,A,Electronics,5,1.00,2\n EL-1 ,B,Electronics,5,1.00,2\n")
    assert len(load_inventory(path).items) == 1


def test_header_with_spaces_is_accepted(tmp_path: Path) -> None:
    path = tmp_path / "spaced.csv"
    path.write_text(" sku , name ,category,quantity,unit_price, reorder_level\nA,x,Kitchen,1,1.00,0\n", encoding="utf-8")
    assert len(load_inventory(path).items) == 1


def test_missing_column_is_a_file_error(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("sku,name,category,quantity,unit_price\n", encoding="utf-8")
    with pytest.raises(InventoryFileError, match="reorder_level"):
        load_inventory(path)


def test_missing_file_is_a_file_error(tmp_path: Path) -> None:
    with pytest.raises(InventoryFileError, match="file not found"):
        load_inventory(tmp_path / "nope.csv")


def test_empty_file_is_a_file_error(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(InventoryFileError, match="empty"):
        load_inventory(path)


def test_parse_helpers() -> None:
    assert parse_whole_number("0") == 0
    assert parse_whole_number("+3") is None
    assert parse_price("2.30") == Decimal("2.30")
    assert parse_price("1e2") is None
