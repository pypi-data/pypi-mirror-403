"""
Playground to test the widget.

python tests/manual/searchable_selection_list_select.py

# Install package if needed
pip install -e .
"""

from enum import Enum

from faker import Faker
from rich.text import Text

from textual_searchable_selectionlist.options import FilteredItems, SelectionStrategy
from textual_searchable_selectionlist.select import select, select_enum


class SampleEnum(Enum):
    A = 'a'
    B = 'b'
    C = 'c'


fake = Faker()


def print_selected(selected: list):
    print('\n----- Selections:\n' + '\n'.join(map(str, selected)))


def test_select_items_str_1():
    selected = select(['John', 'Jane', 'James'], SelectionStrategy.ONE, 'This is the title')
    print_selected(selected)


def test_select_items_str_2():
    selected = select(
        [fake.sentence() for _ in range(10)],
        SelectionStrategy.MULTIPLE,
        'This is the search title',
        app_title='This is the app title',
        description=Text.from_markup(
            'A longer\n[b]description[/b] for things to be more [cyan]readable[/cyan].'
        ),
    )
    print_selected(selected)


def test_select_items_tuple():
    selected = select(
        [('a', 'Abc'), ('b', 'Bcd'), ('c', 'Cde')], SelectionStrategy.ONE, 'This is the title'
    )
    print_selected(selected)


def test_select_enum():
    selected = select_enum(
        SampleEnum,
        SelectionStrategy.ONE,
        title='This is the title',
        filtered_items=FilteredItems.HIDE,
    )
    print_selected(selected)


def test_select_enum_exclude():
    selected = select_enum(
        SampleEnum, SelectionStrategy.ONE, exclude=[SampleEnum.B], title='This is the title'
    )
    print_selected(selected)


if __name__ == '__main__':
    test_select_items_str_2()
