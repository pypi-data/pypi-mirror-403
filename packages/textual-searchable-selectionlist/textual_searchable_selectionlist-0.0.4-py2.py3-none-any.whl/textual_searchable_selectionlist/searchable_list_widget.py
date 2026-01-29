from functools import cached_property
from typing import Callable, Generic, TypeAlias

from rich.text import TextType
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.events import Key
from textual.reactive import Reactive, reactive
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import Input, Label, SelectionList
from textual.widgets._option_list import Option  # noqa
from textual.widgets._selection_list import Selection, SelectionType  # noqa

from .options import FilteredItems, SelectionStrategy

SelectionItemType: TypeAlias = (
    Selection[SelectionType]
    | tuple[TextType, SelectionType]
    | tuple[TextType, SelectionType, bool]
    | TextType
)


class _HideableButtonSelectionList(SelectionList[SelectionType], Generic[SelectionType]):
    """SelectionList subclass that can hide selection buttons."""

    def __init__(self, *args, hide_buttons: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.hide_buttons = hide_buttons

    def render_line(self, y: int) -> Strip:
        """Render a line, optionally hiding the selection button."""
        if self.hide_buttons:
            # Render without the button - just return the parent OptionList rendering
            return super(SelectionList, self).render_line(y)
        return super().render_line(y)


class SearchableListWidget(Widget, Generic[SelectionType]):
    """
    A selection list Textual widget with search functionality and configurable selection mode.

    Search is case-insensitive.
    """

    DEFAULT_CSS = """
    Vertical {
        height: auto;
        margin-bottom: 1;
        padding: 1;
    }

    #search_title {
        width: 1fr;
        text-align: center;
        margin-bottom: 1;
        text-style: bold;
    }

    #search_description {
        width: 1fr;
        text-align: center;
        margin-bottom: 1;
    }
    """

    search_term: Reactive[str] = reactive('')
    """Store current search term"""

    def __init__(
        self,
        *selections: SelectionItemType,
        selection_strategy: SelectionStrategy,
        title: str | None = None,
        description: TextType | None = None,
        selected_callback: Callable[[list[SelectionType]], None] | None = None,
        filtered_items: FilteredItems = FilteredItems.DIM,
        **kwargs,
    ):
        """
        Initialize the selection list.

        :param selections: The content for the selection list.
            Note: While the items can be of type ``Selection`` or ``tuple``, they are internally
            converted to ``Selection`` on initialization.
        :param selection_strategy: How selections are handled (single, all, fail, etc).
        :param title: Optional title shown above the search input.
        :param description: Optional description shown below the title.
        :param selected_callback: Callback invoked with selected values when a selection is made.
        :param filtered_items: What happens to items as they are filtered out.
        :param kwargs: Additional ``Widget`` arguments (for example, ``name``, ``id``, ``classes``,
            ``disabled``).
        """
        if len(selections) > 1:
            if selection_strategy is SelectionStrategy.FAIL:
                raise ValueError(
                    f'Multiple selections not allowed with `{SelectionStrategy.FAIL}` strategy. '
                    f'{len(selections)} found.'
                )

        super().__init__(**kwargs)

        # If a selection item is a string, make it a tuple for downstream compatibility
        _selections = [(item, item) if isinstance(item, str) else item for item in selections]

        self.selections = _selections
        self.selection_strategy = selection_strategy
        self.selected_callback: Callable[[list[SelectionType]], None] | None = selected_callback
        self.multiple = self.selection_strategy.multiple()
        self.title = title
        self.description = description
        self.filtered_items = filtered_items
        self._all_options: list[tuple[int, Option]] = []  # Track all options for REMOVE mode

    def compose(self) -> ComposeResult:
        with Vertical():
            if self.title:
                yield Label(self.title, id='search_title')
            if self.description:
                yield Label(self.description, id='search_description')
            yield Input(placeholder='Search...', id='search_input')
            selection_list = _HideableButtonSelectionList[SelectionType](
                *self.selections,  # type: ignore
                id='selection_list',
                hide_buttons=not self.multiple,
            )
            yield selection_list

    def on_mount(self):
        """Initialize the widget once mounted."""
        # Store all options for REMOVE mode
        if self.filtered_items is FilteredItems.HIDE:
            self._all_options = [
                (i, option) for i, option in enumerate(self.selection_list_widget.options)
            ]

        if len(self.selections) == 1 and self.selected_callback:
            self.selected_callback([self.selection_list_widget.get_option_at_index(0).value])

        if self.multiple:
            if self.selection_strategy is SelectionStrategy.ALL:
                self.selection_list_widget.select_all()

        self.selection_list_widget.focus()

    @cached_property
    def selection_list_widget(self) -> _HideableButtonSelectionList[SelectionType]:
        """Access the ``SelectionList`` widget."""
        return self.query_one('#selection_list', _HideableButtonSelectionList)

    @cached_property
    def input_widget(self) -> Input:
        return self.query_one('#search_input', Input)

    def on_key(self, event: Key):
        # Override base class `OptionList` behavior for `enter`
        if event.key == 'enter':
            event.stop()
            if self.selected_callback:
                if self.multiple:
                    # Return all selected
                    self.selected_callback(self.selection_list_widget.selected)
                else:
                    # Return the highlighted option if it's active, otherwise first active item
                    option_index = self.selection_list_widget.highlighted
                    if option_index is None:
                        # No item highlighted, find first active item
                        option_index = self._get_first_active_index()
                        if option_index is None:
                            return  # No active items to select
                    else:
                        # Check if highlighted item is disabled
                        highlighted_option = self.selection_list_widget.get_option_at_index(
                            option_index
                        )
                        if highlighted_option.disabled:
                            # Find first active (non-disabled) item
                            option_index = self._get_first_active_index()
                            if option_index is None:
                                return  # No active items to select
                    value = self.selection_list_widget.get_option_at_index(option_index).value
                    self.selected_callback([value])
        elif event.key == 'down':
            if self.input_widget.has_focus:
                self.selection_list_widget.focus()
                event.stop()
        elif event.key == 'up':
            if self.selection_list_widget.has_focus:
                selected_options = self.get_selected_options()
                if (
                    not selected_options
                    or self.selection_list_widget.highlighted == selected_options[0][0]
                ):
                    self.input_widget.focus()
                    event.stop()
            elif self.input_widget.has_focus:
                selected_options = self.get_selected_options()
                if selected_options:
                    self.selection_list_widget.action_last()
                    self.selection_list_widget.focus()
                event.stop()
        elif event.key == 'escape':
            if self.selection_list_widget.has_focus:
                self.input_widget.focus()
                event.stop()
        elif event.key in ('ctrl+space', 'left', 'right'):
            if self.multiple:
                self.selection_list_widget._toggle_highlighted_selection()  # noqa
            event.stop()
        elif event.key == 'ctrl+a':
            if self.multiple:
                self.selection_list_widget.select_all()
            event.stop()
        elif event.key == 'ctrl+d':
            if self.multiple:
                self.selection_list_widget.deselect_all()
            event.stop()
        elif event.key in ('ctrl+z', 'ctrl+backspace'):
            self.input_widget.clear()
            event.stop()
        elif event.key == 'backspace':
            text_len = len(self.input_widget.value)
            if text_len > 0:
                self.input_widget.delete(text_len - 1, text_len)
            event.stop()
        elif (len(event.key) == 1 and event.key.isalnum()) or event.key == 'space':
            if self.selection_list_widget.has_focus:
                # Key without combination: add to search
                char = ' ' if event.key == 'space' else event.key
                self.input_widget.value += char
                # Manually trigger filtering since we're bypassing the input change event
                self.search_term = self.input_widget.value.lower()
                self._filter_items()
                event.stop()

    def on_input_changed(self, event: Input.Changed):
        """Handle changes to the search input."""
        event.stop()
        if event.input.id == 'search_input':
            self.search_term = event.value.lower()
            self._filter_items()

    def _get_first_active_index(self) -> int | None:
        """Get the index of the first active (non-disabled) item."""
        for index, option in enumerate(self.selection_list_widget.options):
            if not option.disabled:
                return index
        return None

    def _is_match(self, option: Option) -> bool:
        """Check if the option matches the search term."""
        text = str(option.prompt).lower()
        terms = self.search_term.split()
        return all(term in text for term in terms)

    def _filter_items(self):
        """Filter items based on the search term."""
        list_widget = self.selection_list_widget

        if self.filtered_items is FilteredItems.SHOW:
            # Don't filter anything
            return
        elif self.filtered_items is FilteredItems.DIM:
            # Dim (disable) non-matching items
            for index, option in enumerate(list_widget.options):
                is_match = self._is_match(option)
                list_widget.get_option_at_index(index).disabled = not is_match
            list_widget.refresh()
        elif self.filtered_items is FilteredItems.HIDE:
            # Remove non-matching items from the list
            if not self.search_term:
                # Restore all options when search is cleared
                list_widget.clear_options()
                for _, option in self._all_options:
                    list_widget.add_option(option)
            else:
                # Remove non-matching items
                list_widget.clear_options()
                for _, option in self._all_options:
                    if self._is_match(option):
                        list_widget.add_option(option)
            list_widget.refresh()

    def select(self, selection: Selection[SelectionType] | SelectionType):
        """Override to enforce single selection mode when enabled."""
        if not self.multiple:
            self.selection_list_widget.deselect_all()

        self.selection_list_widget.select(selection)

    def get_selected_options(self) -> list[tuple[int, Option]]:
        return [
            (i, option)
            for i, option in enumerate(self.selection_list_widget.options)
            if not option.disabled
        ]
