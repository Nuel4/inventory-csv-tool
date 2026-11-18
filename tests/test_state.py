from pathlib import Path

import pytest

from app.state import NO_IMPORT_MESSAGE, NoImportError, load_imported_path, save_imported_path


def test_save_and_load_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    csv_path = tmp_path / "data" / "inv.csv"
    save_imported_path(csv_path)
    assert (tmp_path / ".inventory_state").is_file()
    assert load_imported_path() == csv_path.resolve()


def test_relative_path_stored_as_absolute(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    save_imported_path(Path("inv.csv"))
    assert load_imported_path() == (tmp_path / "inv.csv").resolve()


def test_no_state_file_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(NoImportError, match="No file imported yet. Run: inventory import FILE"):
        load_imported_path()


def test_empty_state_file_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".inventory_state").write_text("", encoding="utf-8")
    with pytest.raises(NoImportError):
        load_imported_path()


def test_message_text_matches_spec() -> None:
    assert NO_IMPORT_MESSAGE == "No file imported yet. Run: inventory import FILE"
