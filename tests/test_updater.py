from pathlib import Path

import pytest

from app.updater import UpdateError, parse_quantity, split_records, update_quantity
from tests.conftest import HEADER, write_csv

BODY = (
    "EL-1,Cable,Electronics,5,1.00,2\n"
    "EL-2,Mouse,Electronics,-3,9.00,2\n"
    "EL-3,Charger,Electronics,8,15.00,5\n"
)


def test_update_changes_only_target_quantity(tmp_path: Path) -> None:
    path = write_csv(tmp_path, BODY)
    update_quantity(path, "EL-3", 42)
    expected = HEADER + BODY.replace("EL-3,Charger,Electronics,8,", "EL-3,Charger,Electronics,42,")
    assert path.read_text(encoding="utf-8") == expected


def test_update_saves_original_as_bak(tmp_path: Path) -> None:
    path = write_csv(tmp_path, BODY)
    original = path.read_bytes()
    backup = update_quantity(path, "EL-1", 0)
    assert backup == tmp_path / "inventory.csv.bak"
    assert backup.read_bytes() == original


def test_update_keeps_invalid_rows_spacing_quotes_and_line_endings(tmp_path: Path) -> None:
    path = tmp_path / "raw.csv"
    raw = (
        "sku,name,category,quantity,unit_price,reorder_level\r\n"
        ' BAD ,"Odd ""quoted""",Toys,x,1,1\r\n'
        'EL-1,"Two\nlines",Electronics,5,1.00,2\r\n'
        "EL-2, Spaced , Kitchen ,1,1.0,0"
    )
    path.write_bytes(raw.encode("utf-8"))
    update_quantity(path, "EL-2", 9)
    assert path.read_bytes() == raw.replace("Kitchen ,1,", "Kitchen ,9,").encode("utf-8")


def test_update_targets_first_valid_row_of_duplicate_sku(tmp_path: Path) -> None:
    body = "EL-1,Bad,Electronics,-1,1.00,2\nEL-1,Good,Electronics,5,1.00,2\nEL-1,Dup,Electronics,7,1.00,2\n"
    path = write_csv(tmp_path, body)
    update_quantity(path, "EL-1", 11)
    assert path.read_text(encoding="utf-8") == HEADER + body.replace("Good,Electronics,5", "Good,Electronics,11")


def test_unknown_sku_raises_and_leaves_file_untouched(tmp_path: Path) -> None:
    path = write_csv(tmp_path, BODY)
    with pytest.raises(UpdateError, match="not found"):
        update_quantity(path, "NOPE", 1)
    assert path.read_text(encoding="utf-8") == HEADER + BODY
    assert not (tmp_path / "inventory.csv.bak").exists()


def test_sku_only_in_invalid_row_is_not_found(tmp_path: Path) -> None:
    path = write_csv(tmp_path, BODY)
    with pytest.raises(UpdateError, match="not found"):
        update_quantity(path, "EL-2", 1)


@pytest.mark.parametrize("text", ["-1", "2.5", "abc", "", "1e3", "+4"])
def test_parse_quantity_rejects_non_whole_numbers(text: str) -> None:
    with pytest.raises(UpdateError, match="whole number"):
        parse_quantity(text)


def test_parse_quantity_accepts_whole_numbers() -> None:
    assert parse_quantity("0") == 0
    assert parse_quantity(" 12 ") == 12


def test_negative_quantity_rejected_by_update(tmp_path: Path) -> None:
    path = write_csv(tmp_path, BODY)
    with pytest.raises(UpdateError):
        update_quantity(path, "EL-1", -1)


def test_split_records_keeps_quoted_newlines_together() -> None:
    assert split_records('a,b\n"x\ny",z\nlast') == ["a,b\n", '"x\ny",z\n', "last"]
