"""Tests for app/search.py."""

from app.importer import Item
from app.search import search_items


def skus(items: list[Item]) -> list[str]:
    return [item.sku for item in items]


def test_name_partial_case_insensitive(items: list[Item]) -> None:
    assert skus(search_items(items, name="PEN")) == ["ST-001"]
    assert skus(search_items(items, name="c")) == ["EL-001", "KI-001"]


def test_category_case_insensitive(items: list[Item]) -> None:
    assert skus(search_items(items, category="stationery")) == ["ST-001", "ST-002"]


def test_category_is_not_partial(items: list[Item]) -> None:
    assert search_items(items, category="Station") == []


def test_name_and_category_combined(items: list[Item]) -> None:
    assert skus(search_items(items, name="pen", category="Stationery")) == ["ST-001"]
    assert search_items(items, name="mug", category="Stationery") == []


def test_no_match_returns_empty(items: list[Item]) -> None:
    assert search_items(items, name="zzz") == []


def test_no_criteria_returns_all(items: list[Item]) -> None:
    assert search_items(items) == items
