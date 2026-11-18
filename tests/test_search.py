from decimal import Decimal

from app.importer import Item
from app.search import search_items

ITEMS = [
    Item("ST-001", "Blue Ballpoint Pen", "Stationery", 120, Decimal("2.30"), 50),
    Item("ST-005", "Pencil", "Stationery", 3, Decimal("0.50"), 5),
    Item("KI-001", "Ceramic Mug", "Kitchen", 30, Decimal("5.50"), 10),
]


def skus(items: list[Item]) -> list[str]:
    return [i.sku for i in items]


def test_name_partial_case_insensitive() -> None:
    assert skus(search_items(ITEMS, name="PEN")) == ["ST-001", "ST-005"]


def test_name_no_match() -> None:
    assert search_items(ITEMS, name="laptop") == []


def test_category_case_insensitive() -> None:
    assert skus(search_items(ITEMS, category="kitchen")) == ["KI-001"]


def test_category_is_exact_not_partial() -> None:
    assert search_items(ITEMS, category="kitch") == []


def test_name_and_category_combined() -> None:
    assert skus(search_items(ITEMS, name="mug", category="Stationery")) == []
    assert skus(search_items(ITEMS, name="pencil", category="Stationery")) == ["ST-005"]


def test_no_filters_returns_everything() -> None:
    assert search_items(ITEMS) == ITEMS
