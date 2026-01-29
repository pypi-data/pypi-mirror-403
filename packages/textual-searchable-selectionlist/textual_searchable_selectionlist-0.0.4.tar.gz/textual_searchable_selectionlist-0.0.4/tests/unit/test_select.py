from enum import Enum
from unittest.mock import MagicMock, patch

from textual.widgets._option_list import Option  # noqa

from textual_searchable_selectionlist.options import FilteredItems, SelectionStrategy
from textual_searchable_selectionlist.select import select, select_enum


class TestSelect:
    """Tests for the ``select()`` function."""

    @patch('textual_searchable_selectionlist.select.SearchableListApp')
    def test_select_returns_empty_list_when_app_returns_none(self, mock_app_class: MagicMock):
        """Test that select returns an empty list when the app returns None."""
        mock_app_instance = MagicMock()
        mock_app_instance.run.return_value = None
        mock_app_class.return_value = mock_app_instance

        result = select(
            selections=['item1', 'item2'],
            selection_strategy=SelectionStrategy.ONE,
        )

        assert result == []

    @patch('textual_searchable_selectionlist.select.SearchableListApp')
    def test_select_returns_list_from_app(self, mock_app_class: MagicMock):
        """Test that select returns the list from the app run method."""
        expected_result = ['selected_item']
        mock_app_instance = MagicMock()
        mock_app_instance.run.return_value = expected_result
        mock_app_class.return_value = mock_app_instance

        result = select(
            selections=['item1', 'item2'],
            selection_strategy=SelectionStrategy.ONE,
        )

        assert result == expected_result

    @patch('textual_searchable_selectionlist.select.SearchableListApp')
    def test_select_passes_correct_parameters_to_app(self, mock_app_class: MagicMock):
        """Test that select passes correct parameters to SearchableListApp."""
        selections = ['item1', 'item2', 'item3']
        strategy = SelectionStrategy.MULTIPLE
        search_title = 'Test Search'
        extra_param = 'extra_value'

        mock_app_instance = MagicMock()
        mock_app_instance.run.return_value = []
        mock_app_class.return_value = mock_app_instance

        select(
            selections=selections,
            selection_strategy=strategy,
            search_title=search_title,
            custom_param=extra_param,
        )

        mock_app_class.assert_called_once_with(
            selections,
            strategy,
            search_title=search_title,
            description=None,
            filtered_items=FilteredItems.DIM,
            custom_param=extra_param,
        )

    @patch('textual_searchable_selectionlist.select.SearchableListApp')
    def test_select_sets_app_title_when_provided(self, mock_app_class: MagicMock):
        """Test that select sets the app title when app_title is provided."""
        app_title = 'Custom Title'
        mock_app_instance = MagicMock()
        mock_app_instance.run.return_value = []
        mock_app_class.return_value = mock_app_instance

        select(
            selections=['item1'],
            selection_strategy=SelectionStrategy.ONE,
            app_title=app_title,
        )

        assert mock_app_instance.title == app_title

    @patch('textual_searchable_selectionlist.select.SearchableListApp')
    def test_select_does_not_set_app_title_when_none(self, mock_app_class: MagicMock):
        """Test that select does not set app title when app_title is None."""
        mock_app_instance = MagicMock()
        mock_app_instance.run.return_value = []
        mock_app_class.return_value = mock_app_instance

        select(
            selections=['item1'],
            selection_strategy=SelectionStrategy.ONE,
            app_title=None,
        )

        # Title should not be set (no assignment should occur)
        mock_app_class.assert_called_once()

    @patch('textual_searchable_selectionlist.select.SearchableListApp')
    def test_select_passes_inline_parameter_to_run(self, mock_app_class: MagicMock):
        """Test that select passes inline parameter to app.run()."""
        mock_app_instance = MagicMock()
        mock_app_instance.run.return_value = []
        mock_app_class.return_value = mock_app_instance

        select(
            selections=['item1'],
            selection_strategy=SelectionStrategy.ONE,
            inline=True,
        )

        mock_app_instance.run.assert_called_once_with(inline=True)

    @patch('textual_searchable_selectionlist.select.SearchableListApp')
    def test_select_with_inline_false(self, mock_app_class: MagicMock):
        """Test that select passes inline=False to app.run()."""
        mock_app_instance = MagicMock()
        mock_app_instance.run.return_value = []
        mock_app_class.return_value = mock_app_instance

        select(
            selections=['item1'],
            selection_strategy=SelectionStrategy.ONE,
            inline=False,
        )

        mock_app_instance.run.assert_called_once_with(inline=False)

    @patch('textual_searchable_selectionlist.select.SearchableListApp')
    def test_select_with_different_selection_strategies(self, mock_app_class: MagicMock):
        """Test select with different selection strategies."""
        mock_app_instance = MagicMock()
        mock_app_instance.run.return_value = []
        mock_app_class.return_value = mock_app_instance

        strategies = [
            SelectionStrategy.ONE,
            SelectionStrategy.MULTIPLE,
            SelectionStrategy.ALL,
            SelectionStrategy.FAIL,
        ]

        for strategy in strategies:
            mock_app_class.reset_mock()
            select(selections=['item1'], selection_strategy=strategy)
            mock_app_class.assert_called_once()
            assert mock_app_class.call_args[0][1] == strategy

    @patch('textual_searchable_selectionlist.select.SearchableListApp')
    def test_select_with_empty_selections(self, mock_app_class: MagicMock):
        """Test select with an empty selections list."""
        mock_app_instance = MagicMock()
        mock_app_instance.run.return_value = []
        mock_app_class.return_value = mock_app_instance

        result = select(selections=[], selection_strategy=SelectionStrategy.ONE)

        assert result == []
        mock_app_class.assert_called_once_with(
            [],
            SelectionStrategy.ONE,
            search_title=None,
            description=None,
            filtered_items=FilteredItems.DIM,
        )

    @patch('textual_searchable_selectionlist.select.SearchableListApp')
    def test_select_with_option_objects(self, mock_app_class: MagicMock):
        """Test that select handles Option objects in the return value."""
        option1 = Option(prompt='Item 1', id='1')
        option2 = Option(prompt='Item 2', id='2')
        expected_result = [option1, option2]

        mock_app_instance = MagicMock()
        mock_app_instance.run.return_value = expected_result
        mock_app_class.return_value = mock_app_instance

        result = select(
            selections=['item1', 'item2'],
            selection_strategy=SelectionStrategy.MULTIPLE,
        )

        assert result == expected_result


class TestSelectEnum:
    """Tests for the ``select_enum()`` function."""

    class SampleEnum(Enum):
        OPTION_A = 'value_a'
        OPTION_B = 'value_b'
        OPTION_C = 'value_c'

    class NumberEnum(Enum):
        ONE = 1
        TWO = 2
        THREE = 3

    @patch('textual_searchable_selectionlist.select.select')
    def test_select_enum_by_name_returns_enum_values(self, mock_select: MagicMock):
        """Test that select_enum returns enum values when selecting by name."""
        mock_select.return_value = ['OPTION_A', 'OPTION_B']

        result = select_enum(
            enum_type=self.SampleEnum,
            selection_strategy=SelectionStrategy.MULTIPLE,
            select_by='name',
        )

        assert result == [self.SampleEnum.OPTION_A, self.SampleEnum.OPTION_B]

    @patch('textual_searchable_selectionlist.select.select')
    def test_select_enum_by_value_returns_enum_values(self, mock_select: MagicMock):
        """Test that select_enum returns enum values when selecting by value."""
        mock_select.return_value = ['value_a', 'value_c']

        result = select_enum(
            enum_type=self.SampleEnum,
            selection_strategy=SelectionStrategy.MULTIPLE,
            select_by='value',
        )

        assert result == [self.SampleEnum.OPTION_A, self.SampleEnum.OPTION_C]

    @patch('textual_searchable_selectionlist.select.select')
    def test_select_enum_passes_correct_names_to_select(self, mock_select: MagicMock):
        """Test that select_enum passes correct names to select function."""
        mock_select.return_value = []

        select_enum(
            enum_type=self.SampleEnum,
            selection_strategy=SelectionStrategy.ONE,
            select_by='name',
        )

        call_args = mock_select.call_args
        assert set(call_args.kwargs['selections']) == {'OPTION_A', 'OPTION_B', 'OPTION_C'}

    @patch('textual_searchable_selectionlist.select.select')
    def test_select_enum_passes_correct_values_to_select(self, mock_select: MagicMock):
        """Test that select_enum passes correct values to select function."""
        mock_select.return_value = []

        select_enum(
            enum_type=self.SampleEnum,
            selection_strategy=SelectionStrategy.ONE,
            select_by='value',
        )

        call_args = mock_select.call_args
        assert set(call_args.kwargs['selections']) == {'value_a', 'value_b', 'value_c'}

    @patch('textual_searchable_selectionlist.select.select')
    def test_select_enum_excludes_specified_items(self, mock_select: MagicMock):
        """Test that select_enum excludes specified enum values."""
        mock_select.return_value = []

        select_enum(
            enum_type=self.SampleEnum,
            selection_strategy=SelectionStrategy.ONE,
            select_by='name',
            exclude=[self.SampleEnum.OPTION_B],
        )

        call_args = mock_select.call_args
        assert set(call_args.kwargs['selections']) == {'OPTION_A', 'OPTION_C'}

    @patch('textual_searchable_selectionlist.select.select')
    def test_select_enum_excludes_multiple_items(self, mock_select: MagicMock):
        """Test that select_enum excludes multiple enum values."""
        mock_select.return_value = []

        select_enum(
            enum_type=self.SampleEnum,
            selection_strategy=SelectionStrategy.ONE,
            select_by='name',
            exclude=[self.SampleEnum.OPTION_A, self.SampleEnum.OPTION_C],
        )

        call_args = mock_select.call_args
        assert call_args.kwargs['selections'] == ['OPTION_B']

    @patch('textual_searchable_selectionlist.select.select')
    def test_select_enum_with_empty_exclude(self, mock_select: MagicMock):
        """Test that select_enum works with empty exclude list."""
        mock_select.return_value = []

        select_enum(
            enum_type=self.SampleEnum,
            selection_strategy=SelectionStrategy.ONE,
            select_by='name',
            exclude=[],
        )

        call_args = mock_select.call_args
        assert set(call_args.kwargs['selections']) == {'OPTION_A', 'OPTION_B', 'OPTION_C'}

    @patch('textual_searchable_selectionlist.select.select')
    def test_select_enum_with_none_exclude(self, mock_select: MagicMock):
        """Test that select_enum works when exclude is None."""
        mock_select.return_value = []

        select_enum(
            enum_type=self.SampleEnum,
            selection_strategy=SelectionStrategy.ONE,
            select_by='name',
            exclude=None,
        )

        call_args = mock_select.call_args
        assert set(call_args.kwargs['selections']) == {'OPTION_A', 'OPTION_B', 'OPTION_C'}

    @patch('textual_searchable_selectionlist.select.select')
    def test_select_enum_uses_custom_title(self, mock_select: MagicMock):
        """Test that select_enum uses custom title when provided."""
        custom_title = 'Pick your option'
        mock_select.return_value = []

        select_enum(
            enum_type=self.SampleEnum,
            selection_strategy=SelectionStrategy.ONE,
            select_by='name',
            title=custom_title,
        )

        call_args = mock_select.call_args
        assert call_args.kwargs['search_title'] == custom_title

    @patch('textual_searchable_selectionlist.select.select')
    def test_select_enum_generates_default_title(self, mock_select: MagicMock):
        """Test that select_enum generates default title from enum name."""
        mock_select.return_value = []

        select_enum(
            enum_type=self.SampleEnum,
            selection_strategy=SelectionStrategy.ONE,
            select_by='name',
        )

        call_args = mock_select.call_args
        assert call_args.kwargs['search_title'] == 'Select from SampleEnum'

    @patch('textual_searchable_selectionlist.select.select')
    def test_select_enum_with_empty_title_generates_default(self, mock_select: MagicMock):
        """Test that empty title string triggers default title generation."""
        mock_select.return_value = []

        select_enum(
            enum_type=self.SampleEnum,
            selection_strategy=SelectionStrategy.ONE,
            select_by='name',
            title='',
        )

        call_args = mock_select.call_args
        assert call_args.kwargs['search_title'] == 'Select from SampleEnum'

    @patch('textual_searchable_selectionlist.select.select')
    def test_select_enum_passes_selection_strategy(self, mock_select: MagicMock):
        """Test that select_enum passes selection strategy correctly."""
        mock_select.return_value = []

        select_enum(
            enum_type=self.SampleEnum,
            selection_strategy=SelectionStrategy.MULTIPLE,
            select_by='name',
        )

        call_args = mock_select.call_args
        assert call_args.kwargs['selection_strategy'] == SelectionStrategy.MULTIPLE

    @patch('textual_searchable_selectionlist.select.select')
    def test_select_enum_with_default_selection_strategy(self, mock_select: MagicMock):
        """Test that select_enum uses ONE as default selection strategy."""
        mock_select.return_value = []

        select_enum(enum_type=self.SampleEnum, select_by='name')

        call_args = mock_select.call_args
        assert call_args.kwargs['selection_strategy'] == SelectionStrategy.ONE

    @patch('textual_searchable_selectionlist.select.select')
    def test_select_enum_handles_option_objects_by_name(self, mock_select: MagicMock):
        """Test that select_enum handles Option objects returned from select by name."""
        option1 = MagicMock(spec=Option)
        option1.value = 'OPTION_A'
        option2 = MagicMock(spec=Option)
        option2.value = 'OPTION_C'
        mock_select.return_value = [option1, option2]

        result = select_enum(
            enum_type=self.SampleEnum,
            selection_strategy=SelectionStrategy.MULTIPLE,
            select_by='name',
        )

        assert result == [self.SampleEnum.OPTION_A, self.SampleEnum.OPTION_C]

    @patch('textual_searchable_selectionlist.select.select')
    def test_select_enum_handles_option_objects_by_value(self, mock_select: MagicMock):
        """Test that select_enum handles Option objects returned from select by value."""
        option1 = MagicMock(spec=Option)
        option1.value = 'value_b'
        mock_select.return_value = [option1]

        result = select_enum(
            enum_type=self.SampleEnum,
            selection_strategy=SelectionStrategy.ONE,
            select_by='value',
        )

        assert result == [self.SampleEnum.OPTION_B]

    @patch('textual_searchable_selectionlist.select.select')
    def test_select_enum_returns_empty_list_when_no_selection(self, mock_select: MagicMock):
        """Test that select_enum returns empty list when no items selected."""
        mock_select.return_value = []

        result = select_enum(
            enum_type=self.SampleEnum,
            selection_strategy=SelectionStrategy.ONE,
            select_by='name',
        )

        assert result == []

    @patch('textual_searchable_selectionlist.select.select')
    def test_select_enum_with_number_enum_by_value(self, mock_select: MagicMock):
        """Test that select_enum works with numeric enum values."""
        mock_select.return_value = [1, 3]

        result = select_enum(
            enum_type=self.NumberEnum,
            selection_strategy=SelectionStrategy.MULTIPLE,
            select_by='value',
        )

        assert result == [self.NumberEnum.ONE, self.NumberEnum.THREE]

    @patch('textual_searchable_selectionlist.select.select')
    def test_select_enum_with_number_enum_by_name(self, mock_select: MagicMock):
        """Test that select_enum works with numeric enum selected by name."""
        mock_select.return_value = ['TWO']

        result = select_enum(
            enum_type=self.NumberEnum,
            selection_strategy=SelectionStrategy.ONE,
            select_by='name',
        )

        assert result == [self.NumberEnum.TWO]
