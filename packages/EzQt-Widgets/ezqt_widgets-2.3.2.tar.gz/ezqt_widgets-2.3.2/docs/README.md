# Documentation – ezqt_widgets

## Overview

This directory contains the complete documentation for the **ezqt_widgets** library – a collection of custom and reusable Qt widgets for PySide6.

## 📖 Documentation Structure

### API Reference

- **[API Summary](api/SUMMARY.md)** – Quick API overview and main components
- **[API Documentation](api/API_DOCUMENTATION.md)** – Complete widget reference with parameters, signals, and methods
- **[Style Guide](api/STYLE_GUIDE.md)** – QSS customization examples and best practices

### CLI Reference

- **[CLI Documentation](cli/CLI_DOCUMENTATION.md)** – Command-line interface guide and available commands

### Examples

- **[Examples](examples/EXAMPLES.md)** – Usage examples and code snippets for all widgets

### Tests

- **[Test Summary](tests/SUMMARY.md)** – Quick test overview
- **[Test Documentation](tests/TEST_DOCUMENTATION.md)** – Complete test reference and coverage information

### Development

- **[Development Guide](DEVELOPMENT.md)** – Environment setup, tools, and contribution guidelines

---

## Quick Start

### Installation

```bash
pip install ezqt_widgets
```

### Basic Usage

```python
from ezqt_widgets import DateButton, IconButton, AutoCompleteInput
from PySide6.QtWidgets import QApplication

app = QApplication([])

# Create widgets
date_btn = DateButton()
icon_btn = IconButton(icon="path/to/icon.png", text="Click me")
input_widget = AutoCompleteInput(completions=["option1", "option2"])

# Show widgets
date_btn.show()
app.exec()
```

---

## Widgets Overview

### 🎛️ Button Widgets (`ezqt_widgets.button`)

| Widget               | Description                                 |
| -------------------- | ------------------------------------------- |
| **DateButton**       | Date picker button with integrated calendar |
| **DatePickerDialog** | Calendar dialog for date selection          |
| **IconButton**       | Button with icon support and optional text  |
| **LoaderButton**     | Button with integrated loading animation    |

### ⌨️ Input Widgets (`ezqt_widgets.input`)

| Widget                 | Description                          |
| ---------------------- | ------------------------------------ |
| **AutoCompleteInput**  | Text field with autocompletion       |
| **SearchInput**        | Search field with history management |
| **TabReplaceTextEdit** | Text editor with tab replacement     |

### 🏷️ Label Widgets (`ezqt_widgets.label`)

| Widget                | Description                       |
| --------------------- | --------------------------------- |
| **ClickableTagLabel** | Clickable tag with toggle state   |
| **FramedLabel**       | Framed label for advanced styling |
| **HoverLabel**        | Label with hover icon display     |
| **IndicatorLabel**    | Status indicator with colored LED |

### 🔧 Miscellaneous Widgets (`ezqt_widgets.misc`)

| Widget             | Description                               |
| ------------------ | ----------------------------------------- |
| **CircularTimer**  | Animated circular timer                   |
| **DraggableItem**  | Draggable list item component             |
| **DraggableList**  | List with draggable and reorderable items |
| **OptionSelector** | Option selector with animated selector    |
| **ToggleIcon**     | Toggleable icon (open/closed states)      |
| **ToggleSwitch**   | Modern toggle switch with animation       |

---

## Recommended Reading Order

### For Beginners

1. **[API Summary](api/SUMMARY.md)** – Quick overview
2. **[Examples](examples/EXAMPLES.md)** – See widgets in action
3. **[Style Guide](api/STYLE_GUIDE.md)** – Customization

### For Developers

1. **[Development Guide](DEVELOPMENT.md)** – Setup and tools
2. **[Test Documentation](tests/TEST_DOCUMENTATION.md)** – Testing patterns
3. **[CLI Documentation](cli/CLI_DOCUMENTATION.md)** – Development tools

---

## Additional Resources

- **[Main README](../README.md)** – Project overview
- **[Changelog](../CHANGELOG.md)** – Version history
- **[License](../LICENSE)** – MIT License

---

**ezqt_widgets** – Custom Qt widgets for modern Python applications.
