"""Select items textual app."""

from typing import Generic, Iterable

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from .options import FilteredItems, SelectionStrategy
from .searchable_list_widget import SearchableListWidget, SelectionItemType, SelectionType
from rich.text import TextType


class SearchableListApp(App, Generic[SelectionType]):
    """App that uses ``SearchableListWidget`` widget to show and select items."""

    CSS = """
    Screen {
        align: center middle;
    }

    SearchableListWidget {
        width: auto;
        height: auto;
        border: round $accent;
        padding: 1;
    }
    """

    BINDINGS = [
        Binding('escape', 'quit', 'Quit', show=False),
    ]

    def __init__(
        self,
        selections: Iterable[SelectionItemType],
        selection_strategy: SelectionStrategy,
        search_title: str | None = None,
        description: TextType | None = None,
        filtered_items: FilteredItems = FilteredItems.DIM,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.selections = selections
        self.selection_strategy = selection_strategy
        self.search_title = search_title
        self.description = description
        self.filtered_items = filtered_items

    def compose(self) -> ComposeResult:
        if not self.is_inline:
            yield Header()
        yield SearchableListWidget[SelectionType](
            *self.selections,
            title=self.search_title,
            description=self.description,
            selection_strategy=self.selection_strategy,
            selected_callback=self._action_select,
            filtered_items=self.filtered_items,
        )
        if not self.is_inline:
            yield Footer()

    def on_mount(self):
        if self.selection_strategy is SelectionStrategy.ALL:
            all_selections = self.query_one(SearchableListWidget).selection_list_widget.options
            self.exit(list(all_selections))

    def _action_select(self, selected_items: list[SelectionType]):
        """Handle the ``select`` action."""
        if selected_items:
            self.exit(selected_items)
