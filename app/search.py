"""Search inventory items by name or category."""

from app.importer import Item


def search_items(items: list[Item], name: str | None = None, category: str | None = None) -> list[Item]:
    """Return items whose name contains `name` and whose category equals `category`.

    Both comparisons are case-insensitive. A criterion left as None is not applied;
    when both are given, an item must match both.
    """
    results = items
    if name is not None:
        needle = name.casefold()
        results = [item for item in results if needle in item.name.casefold()]
    if category is not None:
        wanted = category.strip().casefold()
        results = [item for item in results if item.category.casefold() == wanted]
    return results
