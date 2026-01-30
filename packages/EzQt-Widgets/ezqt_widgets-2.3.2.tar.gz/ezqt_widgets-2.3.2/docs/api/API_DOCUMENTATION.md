# Complete API Documentation – ezqt_widgets

## Overview

This documentation presents all available widgets in the **ezqt_widgets** library, organized by functional modules. Each widget is designed to provide specialized functionality while maintaining API and design consistency.

## Table of Contents

- [Complete API Documentation – ezqt_widgets](#complete-api-documentation--ezqt_widgets)
  - [Overview](#overview)
  - [Table of Contents](#table-of-contents)
  - [🎛️ Button Module (`ezqt_widgets.button`)](#️-button-module-ezqt_widgetsbutton)
    - [DateButton](#datebutton)
    - [DatePickerDialog](#datepickerdialog)
    - [IconButton](#iconbutton)
    - [LoaderButton](#loaderbutton)
  - [⌨️ Input Module (`ezqt_widgets.input`)](#️-input-module-ezqt_widgetsinput)
    - [AutoCompleteInput](#autocompleteinput)
    - [SearchInput](#searchinput)
    - [TabReplaceTextEdit](#tabreplacetextedit)
  - [🏷️ Label Module (`ezqt_widgets.label`)](#️-label-module-ezqt_widgetslabel)
    - [ClickableTagLabel](#clickabletaglabel)
    - [FramedLabel](#framedlabel)
    - [HoverLabel](#hoverlabel)
    - [IndicatorLabel](#indicatorlabel)
  - [🔧 Misc Module (`ezqt_widgets.misc`)](#️-misc-module-ezqt_widgetsmisc)
    - [CircularTimer](#circulartimer)
    - [DraggableList](#draggablelist)
    - [DraggableItem](#draggableitem)
    - [OptionSelector](#optionselector)
    - [ToggleIcon](#toggleicon)
    - [ToggleSwitch](#toggleswitch)
  - [🧪 Usage Examples](#-usage-examples)
  - [🎯 Best Practices](#-best-practices)

---

## 🎛️ Button Module (`ezqt_widgets.button`)

Specialized button widgets with advanced functionality.

### DateButton

**File:** `button/date_button.py`  
**Style Guide:** [See QSS styles](STYLE_GUIDE.md#datebutton)

Date picker button widget with integrated calendar.

**Features:**

- Date selection via popup calendar
- Customizable date format
- Configurable placeholder and icon
- Date validation
- Date change signals

**Main Parameters:**

| Parameter            | Type   | Default         | Description         |
| -------------------- | ------ | --------------- | ------------------- |
| `date_format`        | `str`  | `"yyyy-MM-dd"`  | Date display format |
| `placeholder`        | `str`  | `"Select date"` | Placeholder text    |
| `show_calendar_icon` | `bool` | `True`          | Show calendar icon  |
| `min_width`          | `int`  | `None`          | Minimum width       |
| `min_height`         | `int`  | `None`          | Minimum height      |

**Signals:**

- `dateChanged(QDate)` – Emitted when date changes
- `dateSelected(QDate)` – Emitted when date is selected

**Methods:**

- `clear_date() -> None` – Clear the current date
- `set_today() -> None` – Set date to today
- `open_calendar() -> None` – Open the calendar dialog

**Example:**

```python
from ezqt_widgets import DateButton
from PySide6.QtCore import QDate

button = DateButton(
    date_format="dd/MM/yyyy",
    placeholder="Choose a date",
    show_calendar_icon=True
)
button.dateChanged.connect(lambda date: print(f"Selected: {date}"))
button.show()
```

---

### DatePickerDialog

**File:** `button/date_button.py`

Calendar dialog for date selection, used internally by DateButton.

**Main Parameters:**

| Parameter      | Type      | Default | Description           |
| -------------- | --------- | ------- | --------------------- |
| `initial_date` | `QDate`   | `None`  | Initial selected date |
| `parent`       | `QWidget` | `None`  | Parent widget         |

**Methods:**

- `selected_date() -> QDate` – Get the selected date

---

### IconButton

**File:** `button/icon_button.py`  
**Style Guide:** [See QSS styles](STYLE_GUIDE.md#iconbutton)

Button with icon support and optional text.

**Features:**

- Icon support from various sources (QIcon, file path, URL, SVG)
- Optional text with configurable visibility
- Customizable size and spacing
- Hover and click effects
- Icon colorization

**Main Parameters:**

| Parameter      | Type              | Default    | Description                  |
| -------------- | ----------------- | ---------- | ---------------------------- |
| `icon`         | `QIcon \| str`    | `None`     | Icon (QIcon, path, URL, SVG) |
| `text`         | `str`             | `""`       | Button text                  |
| `icon_size`    | `tuple[int, int]` | `(24, 24)` | Icon size                    |
| `text_visible` | `bool`            | `True`     | Text visibility              |
| `spacing`      | `int`             | `5`        | Icon-text spacing            |
| `icon_color`   | `str \| QColor`   | `None`     | Icon color                   |

**Signals:**

- `iconChanged(QIcon)` – Emitted when icon changes
- `textChanged(str)` – Emitted when text changes

**Methods:**

- `clear_icon() -> None` – Clear the icon
- `clear_text() -> None` – Clear the text
- `toggle_text_visibility() -> None` – Toggle text visibility

**Example:**

```python
from ezqt_widgets import IconButton

button = IconButton(
    icon="path/to/icon.png",
    text="Click me",
    icon_size=(32, 32),
    icon_color="#007bff"
)
button.clicked.connect(lambda: print("Button clicked"))
button.show()
```

---

### LoaderButton

**File:** `button/loader_button.py`  
**Style Guide:** [See QSS styles](STYLE_GUIDE.md#loaderbutton)

Button with integrated loading animation.

**Features:**

- Loading, success, and error states
- Animated spinner during loading
- Configurable texts and icons by state
- Smooth transitions between states
- Auto-reset configurable

**Main Parameters:**

| Parameter         | Type           | Default        | Description          |
| ----------------- | -------------- | -------------- | -------------------- |
| `text`            | `str`          | `"Submit"`     | Default button text  |
| `loading_text`    | `str`          | `"Loading..."` | Text during loading  |
| `loading_icon`    | `str \| QIcon` | `None`         | Loading icon         |
| `success_icon`    | `str \| QIcon` | `None`         | Success icon         |
| `error_icon`      | `str \| QIcon` | `None`         | Error icon           |
| `animation_speed` | `int`          | `100`          | Animation speed (ms) |

**Signals:**

- `loadingStarted()` – Emitted when loading starts
- `loadingFinished()` – Emitted when loading finishes
- `loadingFailed(str)` – Emitted when loading fails

**Methods:**

- `start_loading() -> None` – Start loading state
- `stop_loading() -> None` – Stop loading state
- `set_success() -> None` – Set success state
- `set_error(message: str) -> None` – Set error state

**Example:**

```python
from ezqt_widgets import LoaderButton

button = LoaderButton(
    text="Save",
    loading_text="Saving...",
    animation_speed=80
)

button.loadingStarted.connect(lambda: print("Loading..."))
button.loadingFinished.connect(lambda: print("Done!"))

# Start loading
button.start_loading()
# ... do async work ...
button.set_success()  # or button.set_error("Failed")
```

---

## ⌨️ Input Module (`ezqt_widgets.input`)

Data input widgets with validation and extended functionality.

### AutoCompleteInput

**File:** `input/auto_complete_input.py`  
**Style Guide:** [See QSS styles](STYLE_GUIDE.md#autocompleteinput)

Text field with autocomplete functionality.

**Features:**

- Autocomplete suggestions
- Case-sensitive configurable
- Filtering and completion modes
- Intuitive user interface

**Main Parameters:**

| Parameter         | Type                        | Default           | Description         |
| ----------------- | --------------------------- | ----------------- | ------------------- |
| `completions`     | `list[str]`                 | `[]`              | List of suggestions |
| `case_sensitive`  | `bool`                      | `False`           | Case sensitivity    |
| `filter_mode`     | `Qt.MatchFlag`              | `MatchContains`   | Filtering mode      |
| `completion_mode` | `QCompleter.CompletionMode` | `PopupCompletion` | Completion mode     |

**Properties:**

- `suggestions: list[str]` – List of suggestions
- `case_sensitive: bool` – Case sensitivity
- `filter_mode: Qt.MatchFlag` – Filtering mode
- `completion_mode: QCompleter.CompletionMode` – Completion mode

**Example:**

```python
from ezqt_widgets import AutoCompleteInput
from PySide6.QtCore import Qt

input_field = AutoCompleteInput(
    completions=["Apple", "Banana", "Cherry", "Date"],
    case_sensitive=False,
    filter_mode=Qt.MatchFlag.MatchContains
)
input_field.textChanged.connect(lambda text: print(f"Text: {text}"))
input_field.show()
```

---

### SearchInput

**File:** `input/search_input.py`  
**Style Guide:** [See QSS styles](STYLE_GUIDE.md#searchinput)

Search field with history management.

**Features:**

- Search history
- Navigation in history
- Optional search icon
- Clear button
- Submission signal

**Main Parameters:**

| Parameter       | Type           | Default  | Description          |
| --------------- | -------------- | -------- | -------------------- |
| `search_icon`   | `str \| QIcon` | `None`   | Search icon          |
| `icon_position` | `str`          | `"left"` | Icon position        |
| `clear_button`  | `bool`         | `True`   | Show clear button    |
| `max_history`   | `int`          | `10`     | Maximum history size |

**Signals:**

- `searchSubmitted(str)` – Emitted when search is submitted

**Example:**

```python
from ezqt_widgets import SearchInput

search = SearchInput(
    clear_button=True,
    max_history=20
)
search.searchSubmitted.connect(lambda query: print(f"Search: {query}"))
search.show()
```

---

### TabReplaceTextEdit

**File:** `input/tab_replace_textedit.py`  
**Style Guide:** [See QSS styles](STYLE_GUIDE.md#tabreplacetextedit)

Text editor with automatic tab replacement.

**Features:**

- Automatic tab replacement
- Text cleaning on paste
- Removal of empty lines
- Preservation of whitespace

**Main Parameters:**

| Parameter             | Type   | Default  | Description            |
| --------------------- | ------ | -------- | ---------------------- |
| `tab_replacement`     | `str`  | `"    "` | Tab replacement string |
| `sanitize_on_paste`   | `bool` | `True`   | Sanitize pasted text   |
| `remove_empty_lines`  | `bool` | `False`  | Remove empty lines     |
| `preserve_whitespace` | `bool` | `True`   | Preserve whitespace    |

**Example:**

```python
from ezqt_widgets import TabReplaceTextEdit

editor = TabReplaceTextEdit(
    tab_replacement="  ",  # 2 spaces
    sanitize_on_paste=True
)
editor.setPlainText("def hello():\n\tprint('Hello')")
editor.show()
```

---

## 🏷️ Label Module (`ezqt_widgets.label`)

Interactive label widgets and visual indicators.

### ClickableTagLabel

**File:** `label/clickable_tag_label.py`  
**Style Guide:** [See QSS styles](STYLE_GUIDE.md#clickabletaglabel)

Clickable tag with toggleable state.

**Features:**

- Clickable tag with enabled/disabled state
- Customizable status color
- Click and state change signals
- QSS-friendly interface

**Main Parameters:**

| Parameter      | Type            | Default | Description    |
| -------------- | --------------- | ------- | -------------- |
| `name`         | `str`           | `""`    | Tag name/text  |
| `enabled`      | `bool`          | `False` | Initial state  |
| `status_color` | `str \| QColor` | `None`  | Status color   |
| `min_width`    | `int`           | `None`  | Minimum width  |
| `min_height`   | `int`           | `None`  | Minimum height |

**Signals:**

- `clicked()` – Emitted when tag is clicked
- `toggle_keyword(str)` – Emitted with tag name on toggle
- `stateChanged(bool)` – Emitted when state changes

**Example:**

```python
from ezqt_widgets import ClickableTagLabel

tag = ClickableTagLabel(
    name="Python",
    enabled=True,
    status_color="#007bff"
)
tag.clicked.connect(lambda: print("Tag clicked"))
tag.stateChanged.connect(lambda state: print(f"State: {state}"))
tag.show()
```

---

### FramedLabel

**File:** `label/framed_label.py`  
**Style Guide:** [See QSS styles](STYLE_GUIDE.md#framedlabel)

Framed label for advanced styling based on QFrame.

**Features:**

- Label based on QFrame for more flexibility
- Property-based text and alignment access
- Text change signal
- Custom stylesheet injection

**Main Parameters:**

| Parameter    | Type               | Default     | Description    |
| ------------ | ------------------ | ----------- | -------------- |
| `text`       | `str`              | `""`        | Label text     |
| `alignment`  | `Qt.AlignmentFlag` | `AlignLeft` | Text alignment |
| `min_width`  | `int`              | `None`      | Minimum width  |
| `min_height` | `int`              | `None`      | Minimum height |

**Signals:**

- `textChanged(str)` – Emitted when text changes

**Example:**

```python
from ezqt_widgets import FramedLabel
from PySide6.QtCore import Qt

label = FramedLabel(
    text="Hello World",
    alignment=Qt.AlignmentFlag.AlignCenter
)
label.show()
```

---

### HoverLabel

**File:** `label/hover_label.py`  
**Style Guide:** [See QSS styles](STYLE_GUIDE.md#hoverlabel)

Label with floating icon on hover.

**Features:**

- Interactive label with floating icon on hover
- Click signal on hover icon
- Cursor changes
- Dynamic icon activation/deactivation
- Multiple icon sources

**Main Parameters:**

| Parameter      | Type              | Default    | Description        |
| -------------- | ----------------- | ---------- | ------------------ |
| `text`         | `str`             | `""`       | Label text         |
| `hover_icon`   | `str \| QIcon`    | `None`     | Hover icon         |
| `icon_size`    | `tuple[int, int]` | `(16, 16)` | Icon size          |
| `icon_color`   | `str \| QColor`   | `None`     | Icon color         |
| `icon_padding` | `int`             | `5`        | Icon padding       |
| `icon_enabled` | `bool`            | `True`     | Enable hover icon  |
| `opacity`      | `float`           | `0.8`      | Hover icon opacity |

**Signals:**

- `hoverIconClicked()` – Emitted when hover icon is clicked

**Example:**

```python
from ezqt_widgets import HoverLabel

label = HoverLabel(
    text="Hover over me",
    hover_icon="path/to/icon.png",
    icon_color="#dc3545"
)
label.hoverIconClicked.connect(lambda: print("Icon clicked"))
label.show()
```

---

### IndicatorLabel

**File:** `label/indicator_label.py`  
**Style Guide:** [See QSS styles](STYLE_GUIDE.md#indicatorlabel)

Status indicator with colored LED.

**Features:**

- Dynamic status indicator
- Customizable status map
- Property-based status access
- Status change signal

**Main Parameters:**

| Parameter        | Type   | Default | Description              |
| ---------------- | ------ | ------- | ------------------------ |
| `status_map`     | `dict` | `{}`    | Status configuration map |
| `initial_status` | `str`  | `None`  | Initial status key       |

**Properties:**

- `status: str` – Current status

**Signals:**

- `statusChanged(str)` – Emitted when status changes

**Example:**

```python
from ezqt_widgets import IndicatorLabel

indicator = IndicatorLabel(
    status_map={
        "online": {"text": "Online", "state": "ok", "color": "#28a745"},
        "offline": {"text": "Offline", "state": "error", "color": "#dc3545"},
        "away": {"text": "Away", "state": "warning", "color": "#ffc107"},
    },
    initial_status="online"
)
indicator.statusChanged.connect(lambda status: print(f"Status: {status}"))
indicator.show()

# Change status
indicator.status = "offline"
```

---

## 🔧 Misc Module (`ezqt_widgets.misc`)

Utility widgets and specialized components.

### CircularTimer

**File:** `misc/circular_timer.py`  
**Style Guide:** [See QSS styles](STYLE_GUIDE.md#circulartimer)

Animated circular timer with complete customization.

**Features:**

- Animated circular timer with visual progress
- Customizable colors for ring and node
- Optional loop mode
- Signals for cycle and click events
- Configurable line width

**Main Parameters:**

| Parameter         | Type            | Default     | Description                             |
| ----------------- | --------------- | ----------- | --------------------------------------- |
| `duration`        | `int`           | `5000`      | Duration in milliseconds                |
| `ring_color`      | `str \| QColor` | `"#007bff"` | Ring color                              |
| `node_color`      | `str \| QColor` | `"#ffffff"` | Node/center color                       |
| `ring_width_mode` | `str`           | `"medium"`  | Width mode ("small", "medium", "large") |
| `pen_width`       | `int`           | `None`      | Custom pen width                        |
| `loop`            | `bool`          | `False`     | Enable loop mode                        |

**Signals:**

- `timerReset()` – Emitted when timer is reset
- `clicked()` – Emitted when widget is clicked
- `cycleCompleted()` – Emitted when cycle completes

**Methods:**

- `startTimer() -> None` – Start the timer
- `stopTimer() -> None` – Stop the timer
- `resetTimer() -> None` – Reset the timer

**Example:**

```python
from ezqt_widgets import CircularTimer

timer = CircularTimer(
    duration=10000,  # 10 seconds
    ring_color="#007bff",
    node_color="#ffffff",
    loop=True
)
timer.cycleCompleted.connect(lambda: print("Cycle completed"))
timer.startTimer()
timer.show()
```

---

### DraggableList

**File:** `misc/draggable_list.py`  
**Style Guide:** [See QSS styles](STYLE_GUIDE.md#draggablelist)

Reorderable list with drag & drop and removal via HoverLabel.

**Features:**

- Reorderable list by drag & drop
- Removal of items via HoverLabel (delete icon on hover)
- Signals for reordering and removal
- Compact mode for vertical space saving
- Adaptive width based on content

**Main Parameters:**

| Parameter         | Type            | Default | Description             |
| ----------------- | --------------- | ------- | ----------------------- |
| `items`           | `list[str]`     | `[]`    | Initial list of items   |
| `allow_drag_drop` | `bool`          | `True`  | Allow drag & drop       |
| `allow_remove`    | `bool`          | `True`  | Allow item removal      |
| `max_height`      | `int`           | `None`  | Maximum widget height   |
| `min_width`       | `int`           | `150`   | Minimum widget width    |
| `compact`         | `bool`          | `False` | Compact mode            |
| `icon_color`      | `str \| QColor` | `None`  | Icon color for deletion |

**Signals:**

- `itemMoved(str, int, int)` – Item moved (item_id, old_pos, new_pos)
- `itemRemoved(str, int)` – Item removed (item_id, position)
- `itemAdded(str, int)` – Item added (item_id, position)
- `itemClicked(str)` – Item clicked (item_id)
- `orderChanged(list[str])` – Order changed

**Methods:**

- `add_item(item_id: str, text: str = None) -> None` – Add an item
- `remove_item(item_id: str) -> None` – Remove an item
- `clear_items() -> None` – Clear the list
- `move_item(item_id: str, new_position: int) -> None` – Move an item
- `get_item_position(item_id: str) -> int` – Get item position
- `refresh_style() -> None` – Refresh widget style

**Properties:**

- `items: list[str]` – List of items in current order
- `compact: bool` – Compact mode
- `min_width: int` – Minimum widget width
- `icon_color: str` – Icon color for deletion

**Example:**

```python
from ezqt_widgets import DraggableList

task_list = DraggableList(
    items=["Task 1", "Task 2", "Task 3"],
    compact=True,
    icon_color="#dc3545",
    max_height=300
)

task_list.itemMoved.connect(
    lambda item_id, old_pos, new_pos: print(f"Moved: {item_id}")
)
task_list.itemRemoved.connect(
    lambda item_id, pos: print(f"Removed: {item_id}")
)
task_list.orderChanged.connect(
    lambda order: print(f"New order: {order}")
)
task_list.show()
```

---

### DraggableItem

**File:** `misc/draggable_list.py`

Individual draggable item component used by DraggableList.

**Main Parameters:**

| Parameter     | Type            | Default  | Description            |
| ------------- | --------------- | -------- | ---------------------- |
| `item_id`     | `str`           | Required | Unique item identifier |
| `text`        | `str`           | `None`   | Item display text      |
| `parent_list` | `DraggableList` | `None`   | Parent list reference  |

---

### OptionSelector

**File:** `misc/option_selector.py`  
**Style Guide:** [See QSS styles](STYLE_GUIDE.md#optionselector)

Modern option selector with animation.

**Features:**

- Smooth option selection
- Single selection mode
- Configurable orientation (horizontal/vertical)
- Customizable animation

**Main Parameters:**

| Parameter            | Type        | Default        | Description             |
| -------------------- | ----------- | -------------- | ----------------------- |
| `options`            | `list[str]` | `[]`           | List of options         |
| `default_id`         | `int`       | `0`            | Default option index    |
| `orientation`        | `str`       | `"horizontal"` | Selector orientation    |
| `animation_duration` | `int`       | `200`          | Animation duration (ms) |

**Signals:**

- `clicked()` – Emitted when selector is clicked
- `valueChanged(str)` – Emitted when value changes
- `valueIdChanged(int)` – Emitted when value index changes

**Properties:**

- `current_value: str` – Current selected value
- `current_value_id: int` – Current selected index
- `selected_option: FramedLabel` – Currently selected option widget

**Example:**

```python
from ezqt_widgets import OptionSelector

selector = OptionSelector(
    options=["Small", "Medium", "Large"],
    default_id=1,  # "Medium"
    orientation="horizontal"
)
selector.valueChanged.connect(lambda value: print(f"Selected: {value}"))
selector.show()
```

---

### ToggleIcon

**File:** `misc/toggle_icon.py`  
**Style Guide:** [See QSS styles](STYLE_GUIDE.md#toggleicon)

Toggleable icon to represent open/closed states.

**Features:**

- Toggleable icon between two states
- Customizable colors
- Multiple icon sources (file, URL, SVG)
- State change signals

**Main Parameters:**

| Parameter     | Type              | Default    | Description           |
| ------------- | ----------------- | ---------- | --------------------- |
| `opened_icon` | `str \| QIcon`    | `None`     | Icon for open state   |
| `closed_icon` | `str \| QIcon`    | `None`     | Icon for closed state |
| `state`       | `str`             | `"closed"` | Initial state         |
| `icon_size`   | `tuple[int, int]` | `(16, 16)` | Icon size             |
| `icon_color`  | `str \| QColor`   | `None`     | Icon color            |

**Signals:**

- `stateChanged(str)` – Emitted when state changes
- `clicked()` – Emitted when icon is clicked

**Methods:**

- `toggle() -> None` – Toggle the state
- `set_state(state: str) -> None` – Set specific state

**Example:**

```python
from ezqt_widgets import ToggleIcon

toggle = ToggleIcon(
    opened_icon="path/to/opened.png",
    closed_icon="path/to/closed.png",
    state="closed"
)
toggle.stateChanged.connect(lambda state: print(f"State: {state}"))
toggle.clicked.connect(lambda: print("Clicked"))
toggle.show()
```

---

### ToggleSwitch

**File:** `misc/toggle_switch.py`  
**Style Guide:** [See QSS styles](STYLE_GUIDE.md#toggleswitch)

Modern toggle switch with sliding animation.

**Features:**

- Modern switch with animation
- Customizable colors
- Configurable size
- Smooth animation

**Main Parameters:**

| Parameter   | Type   | Default | Description      |
| ----------- | ------ | ------- | ---------------- |
| `checked`   | `bool` | `False` | Initial state    |
| `width`     | `int`  | `50`    | Switch width     |
| `height`    | `int`  | `24`    | Switch height    |
| `animation` | `bool` | `True`  | Enable animation |

**Signals:**

- `toggled(bool)` – Emitted when state changes

**Methods:**

- `toggle() -> None` – Toggle the switch
- `setChecked(checked: bool) -> None` – Set checked state
- `isChecked() -> bool` – Get checked state

**Example:**

```python
from ezqt_widgets import ToggleSwitch

switch = ToggleSwitch(
    checked=True,
    width=60,
    height=28
)
switch.toggled.connect(lambda checked: print(f"Switch: {checked}"))
switch.show()
```

---

## 🧪 Usage Examples

### Complete Dashboard

```python
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel
from ezqt_widgets import CircularTimer, DraggableList, ToggleSwitch, IndicatorLabel

class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard - ezqt_widgets")
        self.setGeometry(100, 100, 1000, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # Control panel
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)

        # Session timer
        self.session_timer = CircularTimer(
            duration=3600000,  # 1 hour
            ring_color="#007bff",
            loop=True,
        )
        control_layout.addWidget(QLabel("Session time:"))
        control_layout.addWidget(self.session_timer)

        # Status indicator
        self.service_status = IndicatorLabel(
            status_map={
                "running": {"text": "Active", "state": "ok", "color": "#28a745"},
                "stopped": {"text": "Stopped", "state": "error", "color": "#dc3545"},
            },
            initial_status="running",
        )
        control_layout.addWidget(QLabel("Service status:"))
        control_layout.addWidget(self.service_status)

        # Switches
        self.auto_save = ToggleSwitch(checked=True)
        control_layout.addWidget(QLabel("Auto save:"))
        control_layout.addWidget(self.auto_save)

        layout.addWidget(control_panel)

        # Task panel
        task_panel = QWidget()
        task_layout = QVBoxLayout(task_panel)

        self.task_list = DraggableList(
            items=["Analyze data", "Generate report", "Send notifications"],
            compact=True,
            icon_color="#28a745",
            max_height=300,
        )

        task_layout.addWidget(QLabel("Tasks:"))
        task_layout.addWidget(self.task_list)

        layout.addWidget(task_panel)

        # Start timer
        self.session_timer.startTimer()

if __name__ == "__main__":
    app = QApplication([])
    dashboard = Dashboard()
    dashboard.show()
    app.exec()
```

---

## 🎯 Best Practices

### Type Safety

- **Use type hints**: Import widgets directly for better IDE support
- **Type your variables**: `button: DateButton = DateButton()` enables full autocompletion
- **Import from main module**: `from ezqt_widgets import DateButton, IconButton`

### Widget Configuration

- Configure widgets during initialization for best performance
- Use properties for runtime updates
- Connect signals for event handling

### Error Handling

- All widgets handle errors gracefully
- Invalid inputs are validated and handled
- Signals provide feedback for state changes

### Styling

- Use QSS (Qt Style Sheets) for customization
- Follow the [Style Guide](STYLE_GUIDE.md) for consistent styling
- Test styles across different themes

### Signal Connections

```python
# Connect signals for interactive widgets
date_button.dateChanged.connect(lambda date: print(f"Date: {date}"))
icon_button.clicked.connect(lambda: print("Clicked"))
loader_button.loadingStarted.connect(lambda: print("Loading"))
auto_input.textChanged.connect(lambda text: print(f"Text: {text}"))
search_input.searchSubmitted.connect(lambda query: print(f"Search: {query}"))
```

---

**ezqt_widgets** – Complete API documentation for professional Qt widget integration in your Python projects.
