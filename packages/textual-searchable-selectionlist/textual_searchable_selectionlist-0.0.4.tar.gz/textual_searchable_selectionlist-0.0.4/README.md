# Searchable SelectionList
[![image](https://img.shields.io/pypi/v/textual-searchable-selectionlist.svg)](https://pypi.python.org/pypi/textual-searchable-selectionlist)
[![Project License - MIT](https://img.shields.io/pypi/l/textual-searchable-selectionlist.svg)](./LICENSE.txt)

Add search to Textual's [SelectionList](https://textual.textualize.io/widgets/selection_list/).

* Selectable items can be filtered by substring.
* Select one or multiple items.
* Search is case-insensitive.
* Title and description can be customized.

## Installation
```bash
pip install textual-searchable-selectionlist
```

## Usage
```python
from textual_searchable_selectionlist.options import SelectionStrategy
from textual_searchable_selectionlist.select import select, select_enum

selected = select(
    ['John', 'Jane', 'James'],
    selection_strategy=SelectionStrategy.MULTIPLE,
    search_title='Select people',
)

# Enums
# class Color(Enum):
#     RED = 'red'
#     GREEN = 'green'
#
# selected_colors = select_enum(Color, selection_strategy=SelectionStrategy.ONE)
```

## Testing
There are currently no automated tests. Manual testing can be done by running:
```bash
python tests/manual/searchable_selection_list_select.py
```
