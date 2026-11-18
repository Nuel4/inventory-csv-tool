from app.search import search_items
from tests.conftest import make_item

ITEMS = [
    make_item("ST-001", "Blue Ballpoint Pen", "Stationery"),
    make_item("ST-002", "A4 Notebook", "Stationery"),
    make_item("KI-001", "Pen Holder Mug", "Kitchen"),
]


def skus(items: list) -> list[str]:
    return [item.sku for item in items]


def test_name_search_is_partial_and_case_insensitive() -> None:
    assert skus(search_items(ITEMS, name="PEN")) == ["ST-001", "KI-001"]


def test_category_search() -> None:
    assert skus(search_items(ITEMS, category="Stationery")) == ["ST-001", "ST-002"]


def test_category_search_ignores_case() -> None:
    assert skus(search_items(ITEMS, category="kitchen")) == ["KI-001"]


def test_category_search_is_not_partial() -> None:
    assert search_items(ITEMS, category="Station") == []


def test_name_and_category_combine() -> None:
    assert skus(search_items(ITEMS, name="pen", category="Kitchen")) == ["KI-001"]


def test_no_match_returns_empty_list() -> None:
    assert search_items(ITEMS, name="laptop") == []
