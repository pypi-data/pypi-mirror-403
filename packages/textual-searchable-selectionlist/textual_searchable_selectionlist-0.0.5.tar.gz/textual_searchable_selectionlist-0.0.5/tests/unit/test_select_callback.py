from enum import Enum
from unittest.mock import MagicMock, patch

from rich.text import Text

from textual_searchable_selectionlist.options import SelectionStrategy
from textual_searchable_selectionlist.select import select, select_enum


class SampleEnum(Enum):
    ITEM_A = 'a'
    ITEM_B = 'b'


def test_select_passes_selected_callback_to_app():
    callback = MagicMock(return_value=Text('ok'))

    with patch('textual_searchable_selectionlist.select.SearchableListApp') as mock_app_class:
        mock_app_instance = MagicMock()
        mock_app_instance.run.return_value = []
        mock_app_class.return_value = mock_app_instance

        select(
            selections=['item1', 'item2'],
            selection_strategy=SelectionStrategy.ONE,
            selected_callback=callback,
        )

        mock_app_class.assert_called_once()
        assert mock_app_class.call_args.kwargs['selected_callback'] is callback


def test_select_enum_passes_selected_callback_to_select():
    callback = MagicMock(return_value=Text('ok'))

    with patch('textual_searchable_selectionlist.select.select') as mock_select:
        mock_select.return_value = []

        select_enum(
            enum_type=SampleEnum,
            selection_strategy=SelectionStrategy.ONE,
            select_by='name',
            selected_callback=callback,
        )

        mock_select.assert_called_once()
        assert mock_select.call_args.kwargs['selected_callback'] is callback
