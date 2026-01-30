# Examples Documentation – ezqt_widgets

## Overview

This document provides comprehensive examples and usage demonstrations for the **ezqt_widgets** library. These examples showcase all features including button widgets, input widgets, label widgets, and miscellaneous utility widgets.

## Table of Contents

- [Examples Documentation – ezqt_widgets](#examples-documentation--ezqt_widgets)
  - [Overview](#overview)
  - [Table of Contents](#table-of-contents)
  - [📋 Available Example Scripts](#-available-example-scripts)
  - [🧪 Usage Examples](#-usage-examples)
    - [Button Widgets](#button-widgets)
    - [Input Widgets](#input-widgets)
    - [Label Widgets](#label-widgets)
    - [Miscellaneous Widgets](#miscellaneous-widgets)
  - [🚀 Advanced Integration](#-advanced-integration)
  - [🎯 Best Practices](#-best-practices)
  - [▶️ Running Examples](#️-running-examples)

---

## 📋 Available Example Scripts

### 1. `run_all_examples.py` – Main Launcher

A comprehensive launcher script with a graphical interface to run all examples.

**Location:** `examples/run_all_examples.py`

**Usage:**

```bash
python examples/run_all_examples.py
```

**Features:**

- Graphical interface for easy example selection
- Individual launch for specific examples
- Batch execution for all examples
- Error handling with informative messages

---

### 2. `button_example.py` – Button Widgets

Demonstrates all button widgets.

**Location:** `examples/button_example.py`

**Widgets Covered:**

- **DateButton** – Date selection with calendar popup
- **IconButton** – Button with icon support
- **LoaderButton** – Button with loading animation

---

### 3. `input_example.py` – Input Widgets

Demonstrates all input widgets.

**Location:** `examples/input_example.py`

**Widgets Covered:**

- **AutoCompleteInput** – Text field with autocompletion
- **SearchInput** – Search field with history
- **TabReplaceTextEdit** – Text editor with tab replacement

---

### 4. `label_example.py` – Label Widgets

Demonstrates all label widgets.

**Location:** `examples/label_example.py`

**Widgets Covered:**

- **ClickableTagLabel** – Clickable tag with toggle state
- **FramedLabel** – Framed label for styling
- **HoverLabel** – Label with hover icon
- **IndicatorLabel** – Status indicator with LED

---

### 5. `misc_example.py` – Miscellaneous Widgets

Demonstrates utility widgets.

**Location:** `examples/misc_example.py`

**Widgets Covered:**

- **CircularTimer** – Animated circular timer
- **DraggableList** – Drag & drop list
- **OptionSelector** – Option selector with animation
- **ToggleIcon** – Toggleable icon
- **ToggleSwitch** – Modern toggle switch

---

## 🧪 Usage Examples

### Button Widgets

```python
from ezqt_widgets import DateButton, IconButton, LoaderButton
from PySide6.QtWidgets import QApplication

app = QApplication([])

# Date button
date_btn = DateButton(placeholder="Select a date")
date_btn.dateChanged.connect(lambda date: print(f"Date: {date}"))
date_btn.show()

# Icon button
icon_btn = IconButton(icon="path/to/icon.png", text="Click me")
icon_btn.clicked.connect(lambda: print("Clicked"))
icon_btn.show()

# Loader button
loader_btn = LoaderButton(text="Load", loading_text="Loading...")
loader_btn.loadingStarted.connect(lambda: print("Loading..."))
loader_btn.show()

app.exec()
```

---

### Input Widgets

```python
from ezqt_widgets import AutoCompleteInput, SearchInput, TabReplaceTextEdit
from PySide6.QtWidgets import QApplication

app = QApplication([])

# Auto-complete input
auto_input = AutoCompleteInput(completions=["Apple", "Banana", "Cherry"])
auto_input.textChanged.connect(lambda text: print(f"Text: {text}"))
auto_input.show()

# Search input
search_input = SearchInput()
search_input.searchSubmitted.connect(lambda query: print(f"Search: {query}"))
search_input.show()

# Tab replace text edit
text_edit = TabReplaceTextEdit()
text_edit.setPlainText("Type here...")
text_edit.show()

app.exec()
```

---

### Label Widgets

```python
from ezqt_widgets import ClickableTagLabel, FramedLabel, HoverLabel, IndicatorLabel
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

app = QApplication([])

# Clickable tag
tag = ClickableTagLabel(name="Python", enabled=True)
tag.clicked.connect(lambda: print("Tag clicked"))
tag.show()

# Framed label
framed = FramedLabel(text="Framed Label", alignment=Qt.AlignmentFlag.AlignCenter)
framed.show()

# Hover label
hover = HoverLabel(text="Hover me", hover_icon="path/to/icon.png")
hover.hoverIconClicked.connect(lambda: print("Icon clicked"))
hover.show()

# Indicator label
indicator = IndicatorLabel(
    status_map={
        "online": {"text": "Online", "state": "ok", "color": "#28a745"},
        "offline": {"text": "Offline", "state": "error", "color": "#dc3545"},
    },
    initial_status="online",
)
indicator.statusChanged.connect(lambda status: print(f"Status: {status}"))
indicator.show()

app.exec()
```

---

### Miscellaneous Widgets

```python
from ezqt_widgets import (
    CircularTimer,
    DraggableList,
    OptionSelector,
    ToggleIcon,
    ToggleSwitch,
)
from PySide6.QtWidgets import QApplication

app = QApplication([])

# Circular timer
timer = CircularTimer(duration=5000, loop=True)
timer.cycleCompleted.connect(lambda: print("Timer completed"))
timer.startTimer()
timer.show()

# Draggable list
draggable = DraggableList(items=["Item 1", "Item 2", "Item 3"])
draggable.itemMoved.connect(
    lambda item_id, old_pos, new_pos: print(f"Moved: {item_id}")
)
draggable.show()

# Option selector
selector = OptionSelector(options=["A", "B", "C"])
selector.valueChanged.connect(lambda value: print(f"Selected: {value}"))
selector.show()

# Toggle icon
toggle_icon = ToggleIcon(
    opened_icon="path/to/opened.png",
    closed_icon="path/to/closed.png"
)
toggle_icon.stateChanged.connect(lambda state: print(f"State: {state}"))
toggle_icon.show()

# Toggle switch
switch = ToggleSwitch(checked=True)
switch.toggled.connect(lambda checked: print(f"Switch: {checked}"))
switch.show()

app.exec()
```

---

## 🚀 Advanced Integration

### Complete Dashboard

```python
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel
)
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

        # Toggle switches
        self.auto_save = ToggleSwitch(checked=True)
        control_layout.addWidget(QLabel("Auto save:"))
        control_layout.addWidget(self.auto_save)

        self.notifications = ToggleSwitch(checked=False)
        control_layout.addWidget(QLabel("Notifications:"))
        control_layout.addWidget(self.notifications)

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

        # Connect signals
        self.task_list.itemMoved.connect(self._on_task_moved)
        self.task_list.itemRemoved.connect(self._on_task_removed)
        self.task_list.orderChanged.connect(self._on_order_changed)

        task_layout.addWidget(QLabel("Tasks:"))
        task_layout.addWidget(self.task_list)

        layout.addWidget(task_panel)

        # Start timer
        self.session_timer.startTimer()

    def _on_task_moved(self, item_id: str, old_pos: int, new_pos: int) -> None:
        print(f"Task moved: '{item_id}' from {old_pos} to {new_pos}")

    def _on_task_removed(self, item_id: str, position: int) -> None:
        print(f"Task removed: '{item_id}' at position {position}")

    def _on_order_changed(self, new_order: list[str]) -> None:
        print(f"New order: {new_order}")


if __name__ == "__main__":
    app = QApplication([])
    dashboard = Dashboard()
    dashboard.show()
    app.exec()
```

---

## 🎯 Best Practices

### 1. Widget Initialization

Configure widgets during initialization for best performance:

```python
# Good: Configure during initialization
button = DateButton(
    date_format="dd/MM/yyyy",
    placeholder="Select date",
    show_calendar_icon=True
)

# Then use properties for runtime updates
button.date = QDate.currentDate()
```

### 2. Signal Connections

Connect signals for all interactive widgets:

```python
# Connect signals
date_button.dateChanged.connect(handle_date_change)
icon_button.clicked.connect(handle_click)
loader_button.loadingStarted.connect(handle_loading)
auto_input.textChanged.connect(handle_text_change)
search_input.searchSubmitted.connect(handle_search)
tag_label.clicked.connect(handle_tag_click)
hover_label.hoverIconClicked.connect(handle_icon_click)
indicator_label.statusChanged.connect(handle_status_change)
timer.cycleCompleted.connect(handle_timer)
selector.valueChanged.connect(handle_selection)
toggle_icon.stateChanged.connect(handle_toggle)
switch.toggled.connect(handle_switch)
draggable_list.itemMoved.connect(handle_move)
```

### 3. Error Handling

All widgets handle errors gracefully:

```python
try:
    button = DateButton(date="invalid")
except Exception as e:
    print(f"Error: {e}")
```

---

## ▶️ Running Examples

### Using Python

```bash
# Complete demonstration (with GUI launcher)
python examples/run_all_examples.py

# Or run specific examples
python examples/button_example.py
python examples/input_example.py
python examples/label_example.py
python examples/misc_example.py
```

### Using CLI

```bash
# Run all examples with GUI
ezqt run --all

# Run specific categories
ezqt run --buttons
ezqt run --inputs
ezqt run --labels
ezqt run --misc

# List available examples
ezqt list
```

### Prerequisites

```bash
# Install in development mode
pip install -e ".[dev]"

# Or install dependencies
pip install PySide6 ezqt_widgets
```

---

## Additional Resources

- **[API Documentation](../api/API_DOCUMENTATION.md)** – Complete API reference
- **[CLI Documentation](../cli/CLI_DOCUMENTATION.md)** – Command-line interface
- **[Style Guide](../api/STYLE_GUIDE.md)** – QSS customization

---

**ezqt_widgets** – Modern, typed, and beautiful Qt widgets for Python.
