from pathlib import Path

import pytest

from app.state import NO_IMPORT_MESSAGE, STATE_FILE, NoImportError, load_imported_file, save_imported_file


def test_save_writes_state_file_in_current_folder(isolated_folder: Path) -> None:
    csv_path = isolated_folder / "inv.csv"
    save_imported_file(Path("inv.csv"))
    assert (isolated_folder / STATE_FILE).read_text(encoding="utf-8") == str(csv_path.resolve())


def test_load_returns_saved_path(isolated_folder: Path) -> None:
    save_imported_file(Path("inv.csv"))
    assert load_imported_file() == (isolated_folder / "inv.csv").resolve()


def test_load_without_state_raises_no_import_error() -> None:
    with pytest.raises(NoImportError) as error:
        load_imported_file()
    assert str(error.value) == "No file imported yet. Run: inventory import FILE"
    assert NO_IMPORT_MESSAGE == str(error.value)


def test_empty_state_file_counts_as_nothing_imported(isolated_folder: Path) -> None:
    (isolated_folder / STATE_FILE).write_text("", encoding="utf-8")
    with pytest.raises(NoImportError):
        load_imported_file()


def test_state_file_is_gitignored() -> None:
    gitignore = Path(__file__).resolve().parent.parent / ".gitignore"
    assert STATE_FILE in gitignore.read_text(encoding="utf-8").split()
