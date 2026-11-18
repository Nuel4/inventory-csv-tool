"""Search items by name or category."""

from app.importer import Item


def search_items(items: list[Item], name: str | None = None, category: str | None = None) -> list[Item]:
    """Return items matching all given filters.

    name: case-insensitive partial match. category: case-insensitive exact match.
    """
    results = items
    if name is not None:
        needle = name.strip().lower()
        results = [item for item in results if needle in item.name.lower()]
    if category is not None:
        wanted = category.strip().lower()
        results = [item for item in results if item.category.lower() == wanted]
    return results
