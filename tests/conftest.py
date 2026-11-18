"""Shared test fixtures."""

from collections.abc import Callable
from pathlib import Path

import pytest

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
SAMPLE_CSV: Path = REPO_ROOT / "samples" / "inventory_sample.csv"
HEADER: str = "sku,name,category,quantity,unit_price,reorder_level\n"


@pytest.fixture
def sample_csv() -> Path:
    return SAMPLE_CSV


@pytest.fixture
def write_csv(tmp_path: Path) -> Callable[..., Path]:
    """Write CSV text (header added unless header=False) to a temp file."""

    def _write(body: str, name: str = "inv.csv", header: bool = True) -> Path:
        path = tmp_path / name
        path.write_text((HEADER if header else "") + body, encoding="utf-8")
        return path

    return _write
