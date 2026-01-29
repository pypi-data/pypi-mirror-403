from enum import StrEnum


class SelectionStrategy(StrEnum):
    """
    What to do when more than one item is detected.
    """

    MULTIPLE = 'multiple'
    """Show menu and allow user to select any number of items."""

    ONE = 'one'
    """Show menu and allow user to select one of the items."""

    ALL = 'all'
    """Select all the items without showing the menu."""

    FAIL = 'fail'
    """Raise ``ValueError``."""

    def multiple(self) -> bool:
        """
        Returns ``True`` if more than one item can be chosen with the current selection strategy,
        ``False`` otherwise."""
        return self in [SelectionStrategy.MULTIPLE, SelectionStrategy.ALL]


class FilteredItems(StrEnum):
    """
    What happens to items as they are filtered out.
    """

    DIM = 'dim'
    """Dim the filtered items."""

    HIDE = 'hide'
    """Hide (remove) the filtered items from the list."""

    SHOW = 'show'
    """Show the filtered items (do nothing)."""
