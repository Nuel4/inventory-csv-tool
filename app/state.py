"""Remember which CSV file was imported, in .inventory_state in the current folder."""

from pathlib import Path

STATE_FILE = ".inventory_state"
NO_IMPORT_MESSAGE = "No file imported yet. Run: inventory import FILE"


class NoImportError(Exception):
    """No file has been imported in the current folder yet."""


def state_path(folder: Path | None = None) -> Path:
    """Return the path of the state file in folder (default: current folder)."""
    return (folder or Path.cwd()) / STATE_FILE


def save_imported_file(csv_path: Path, folder: Path | None = None) -> None:
    """Store the absolute path of the imported CSV file."""
    state_path(folder).write_text(str(csv_path.resolve()), encoding="utf-8")


def load_imported_file(folder: Path | None = None) -> Path:
    """Return the path of the imported CSV file, or raise NoImportError."""
    path = state_path(folder)
    if not path.is_file():
        raise NoImportError(NO_IMPORT_MESSAGE)
    stored = path.read_text(encoding="utf-8").strip()
    if not stored:
        raise NoImportError(NO_IMPORT_MESSAGE)
    return Path(stored)
