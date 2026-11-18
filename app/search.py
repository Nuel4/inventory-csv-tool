"""Search items by name or category."""

from app.importer import Item


def search_items(items: list[Item], name: str | None = None, category: str | None = None) -> list[Item]:
    """Return items matching every filter given.

    name: case-insensitive partial match. category: case-insensitive exact match.
    """
    results = items
    if name is not None:
        needle = name.strip().casefold()
        results = [item for item in results if needle in item.name.casefold()]
    if category is not None:
        wanted = category.strip().casefold()
        results = [item for item in results if item.category.casefold() == wanted]
    return results
