# API Summary

**ezqt_widgets** – Custom Qt widgets collection for PySide6.

## 📖 Complete Documentation

For detailed API documentation, see **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)**.

---

## Quick Overview

### Main Components

- **Button Widgets**: DateButton, IconButton, LoaderButton
- **Input Widgets**: AutoCompleteInput, SearchInput, TabReplaceTextEdit
- **Label Widgets**: ClickableTagLabel, FramedLabel, HoverLabel, IndicatorLabel
- **Misc Widgets**: CircularTimer, DraggableList, OptionSelector, ToggleIcon, ToggleSwitch

### Quick Start

```python
from ezqt_widgets import DateButton, IconButton, AutoCompleteInput
from PySide6.QtWidgets import QApplication

app = QApplication([])

# Create widgets
date_btn = DateButton()
icon_btn = IconButton(icon="path/to/icon.png", text="Click me")
input_widget = AutoCompleteInput(completions=["option1", "option2"])

# Connect signals
date_btn.dateChanged.connect(lambda date: print(f"Date: {date}"))
icon_btn.clicked.connect(lambda: print("Clicked"))

# Show widgets
date_btn.show()
icon_btn.show()
input_widget.show()

app.exec()
```

### Key Features

**Button Widgets:**

- DateButton: Date selection with calendar popup
- IconButton: Button with icon support (QIcon, file, SVG, URL)
- LoaderButton: Loading states with animations

**Input Widgets:**

- AutoCompleteInput: Text field with autocompletion
- SearchInput: Search field with history management
- TabReplaceTextEdit: Text editor with tab replacement

**Label Widgets:**

- ClickableTagLabel: Clickable tag with toggle state
- FramedLabel: Framed label for advanced styling
- HoverLabel: Label with hover icon display
- IndicatorLabel: Status indicator with colored LED

**Misc Widgets:**

- CircularTimer: Animated circular timer
- DraggableList: List with drag & drop reordering
- OptionSelector: Option selector with animation
- ToggleIcon: Toggleable icon (open/closed states)
- ToggleSwitch: Modern toggle switch with animation

### Common Signals

| Widget            | Signal                     | Description           |
| ----------------- | -------------------------- | --------------------- |
| DateButton        | `dateChanged(QDate)`       | Date changed          |
| IconButton        | `clicked()`                | Button clicked        |
| LoaderButton      | `loadingStarted()`         | Loading started       |
| AutoCompleteInput | `textChanged(str)`         | Text changed          |
| SearchInput       | `searchSubmitted(str)`     | Search submitted      |
| ClickableTagLabel | `clicked()`                | Tag clicked           |
| HoverLabel        | `hoverIconClicked()`       | Hover icon clicked    |
| IndicatorLabel    | `statusChanged(str)`       | Status changed        |
| CircularTimer     | `cycleCompleted()`         | Timer cycle completed |
| OptionSelector    | `valueChanged(str)`        | Selection changed     |
| ToggleIcon        | `stateChanged(str)`        | State changed         |
| ToggleSwitch      | `toggled(bool)`            | Toggle state changed  |
| DraggableList     | `itemMoved(str, int, int)` | Item moved            |

### Type Safety

All widgets are fully typed with type hints for IDE autocompletion:

```python
from ezqt_widgets import DateButton, IconButton

# Full autocompletion support
button: DateButton = DateButton()
icon_btn: IconButton = IconButton(icon="path/to/icon.png")
```

---

**For complete API documentation with examples, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).**
