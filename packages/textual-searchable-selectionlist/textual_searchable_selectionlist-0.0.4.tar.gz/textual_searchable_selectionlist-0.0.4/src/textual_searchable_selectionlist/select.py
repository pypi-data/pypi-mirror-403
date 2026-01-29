from enum import Enum
from typing import Iterable, Literal, Type, TypeAlias, TypeVar

from rich.text import TextType
from textual.widgets._option_list import Option  # noqa

from .options import FilteredItems, SelectionStrategy
from .searchable_list_app import SearchableListApp
from .searchable_list_widget import SelectionItemType, SelectionType

T = TypeVar('T')
T_Enum = TypeVar('T_Enum', bound=Enum)
SelectionResultType: TypeAlias = SelectionType | Option


def select(
    selections: Iterable[SelectionItemType],
    selection_strategy: SelectionStrategy,
    search_title: str | None = None,
    description: TextType | None = None,
    app_title: str | None = 'Select items',
    inline: bool = False,
    filtered_items: FilteredItems = FilteredItems.DIM,
    **kwargs,
) -> list[SelectionResultType]:
    """
    Select one or more items.

    See Textual's ``App.run(...)`` for more options.

    :param selections: The items to choose from.
    :param selection_strategy: What to do when more than one item is detected.
        See ``SelectionStrategy`` for more details.
    :param search_title: Title of the search.
    :param description: Description text. Can be formatted by using markup in ``Text``.
    :param app_title: Title of the Textual app.
    :param inline: Run the app inline (under the prompt).
    :param filtered_items: What happens to items as they are filtered out.
        See ``FilteredItems`` for more details.
    :param kwargs: Additional ``textual.app.App`` arguments.
    """
    # if selection_strategy is SelectionStrategy.ALL:
    #     return list(selections)

    app: SearchableListApp = SearchableListApp(
        selections,
        selection_strategy,
        search_title=search_title,
        description=description,
        filtered_items=filtered_items,
        **kwargs,
    )
    if app_title:
        app.title = app_title
    selected = app.run(inline=inline)
    return selected or []


def select_enum(
    enum_type: Type[T_Enum],
    selection_strategy: SelectionStrategy = SelectionStrategy.ONE,
    select_by: Literal['name', 'value'] = 'name',
    exclude: Iterable[T_Enum] | None = None,
    title: str = '',
    description: TextType | None = None,
    filtered_items: FilteredItems = FilteredItems.DIM,
) -> list[T_Enum]:
    """
    Select from an enum.

    :param enum_type: The enum type to select from.
    :param selection_strategy: What to do when more than one item is detected.
        See ``SelectionStrategy`` for more details.
    :param select_by: Whether to select by enum name or value.
    :param exclude: An iterable of enum values to exclude from selection.
    :param title: The title of the selection dialog.
    :param description: Description text. Can be formatted by using markup in ``Text``.
    :param filtered_items: What happens to items as they are filtered out.
        See ``FilteredItems`` for more details.
    """
    selectable_items = [item for item in enum_type if item not in (exclude or [])]

    selections = (
        [item.name for item in selectable_items]
        if select_by == 'name'
        else [item.value for item in enum_type]
    )

    title = title or f'Select from {enum_type.__name__}'
    selection = select(  # type: ignore
        selections=selections,
        selection_strategy=selection_strategy,
        search_title=title,
        description=description,
        filtered_items=filtered_items,
    )
    if selection and isinstance(selection[0], Option):
        selection_values = [item.value for item in selection]  # type: ignore
    else:
        selection_values = selection

    return (
        [enum_type[x] for x in selection_values]
        if select_by == 'name'
        else [enum_type(x) for x in selection_values]
    )
