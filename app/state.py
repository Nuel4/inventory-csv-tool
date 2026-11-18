"""Remember which CSV was imported, in .inventory_state in the current folder."""

from pathlib import Path

STATE_FILE: str = ".inventory_state"
NO_IMPORT_MESSAGE: str = "No file imported yet. Run: inventory import FILE"


class NoImportError(Exception):
    """Nothing has been imported in this folder yet."""


def state_path() -> Path:
    """Path of the state file in the current working directory."""
    return Path.cwd() / STATE_FILE


def save_imported_path(csv_path: Path) -> None:
    """Store the absolute path of the imported CSV."""
    state_path().write_text(str(csv_path.resolve()) + "\n", encoding="utf-8")


def load_imported_path() -> Path:
    """Return the stored CSV path, or raise NoImportError."""
    path = state_path()
    if not path.is_file():
        raise NoImportError(NO_IMPORT_MESSAGE)
    stored = path.read_text(encoding="utf-8").strip()
    if not stored:
        raise NoImportError(NO_IMPORT_MESSAGE)
    return Path(stored)
