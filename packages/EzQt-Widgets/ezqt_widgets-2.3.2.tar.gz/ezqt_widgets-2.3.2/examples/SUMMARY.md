# EzQt Widgets Examples Summary

**ezqt_widgets** – Complete widget demonstration examples.

## 📖 Overview

This folder contains interactive examples for all widgets in the EzQt Widgets library. Each example demonstrates the main features and usage patterns for its respective widget category.

---

## 📁 Files

### 🚀 Main Examples

| File                  | Description                         |
| --------------------- | ----------------------------------- |
| `button_example.py`   | Button widget demonstrations        |
| `input_example.py`    | Input widget demonstrations         |
| `label_example.py`    | Label widget demonstrations         |
| `misc_example.py`     | Miscellaneous widget demonstrations |
| `run_all_examples.py` | Unified launcher for all examples   |

---

## 🎯 Widgets Covered

### 🎛️ Button Widgets (`button_example.py`)

| Widget           | Description                                 |
| ---------------- | ------------------------------------------- |
| **DateButton**   | Date picker button with integrated calendar |
| **IconButton**   | Button with icon support and optional text  |
| **LoaderButton** | Button with integrated loading animation    |

### ⌨️ Input Widgets (`input_example.py`)

| Widget                 | Description                          |
| ---------------------- | ------------------------------------ |
| **TabReplaceTextEdit** | Text editor with tab replacement     |
| **AutoCompleteInput**  | Text field with autocompletion       |
| **SearchInput**        | Search field with history management |

### 🏷️ Label Widgets (`label_example.py`)

| Widget                | Description                       |
| --------------------- | --------------------------------- |
| **FramedLabel**       | Framed label for advanced styling |
| **IndicatorLabel**    | Status indicator with colored LED |
| **HoverLabel**        | Label with hover icon display     |
| **ClickableTagLabel** | Clickable tag with toggle state   |

### 🔧 Miscellaneous Widgets (`misc_example.py`)

| Widget             | Description                               |
| ------------------ | ----------------------------------------- |
| **OptionSelector** | Option selector with animated selector    |
| **CircularTimer**  | Animated circular timer                   |
| **ToggleIcon**     | Toggleable icon (open/closed states)      |
| **ToggleSwitch**   | Modern toggle switch with animation       |
| **DraggableList**  | List with draggable and reorderable items |

---

## 🚀 Running Examples

### Using the Launcher (Recommended)

```bash
# Run the unified launcher
python examples/run_all_examples.py
```

### Running Individual Examples

```bash
# Button examples
python examples/button_example.py

# Input examples
python examples/input_example.py

# Label examples
python examples/label_example.py

# Misc examples
python examples/misc_example.py
```

### Using the CLI

```bash
# Run all examples
ezqt run --all

# Run a specific example
ezqt run --example button

# List available examples
ezqt list
```

---

## ✨ Features Demonstrated

### 🎨 User Interface

- **Modern design** with custom CSS styles
- **Organized layouts** by widget category
- **Reactive interactions** with visual feedback
- **Integrated documentation** in each example

### 🔧 Widget Functionality

- **Configuration** with various parameters
- **Event handling** and callbacks
- **Animations** and transitions
- **Multiple states** for each widget
- **Integration** between different widgets

### 📝 Code Quality

- **Detailed comments** in English
- **Modular structure** and reusability
- **Robust error handling**
- **PySide6 best practices**

---

## 📊 Statistics

- **5 example files** demonstrating widget usage
- **15 widgets** fully covered
- **100%** widget coverage

---

## 💡 Usage Tips

1. **Explore interactively**: Use the test buttons to see widget behavior
2. **Read the code**: Each example contains detailed comments
3. **Reuse patterns**: Copy widget configurations for your projects
4. **Test before integration**: Verify functionality before adding to production

---

## 📚 Related Documentation

- **[API Documentation](../docs/api/API_DOCUMENTATION.md)** – Complete widget reference
- **[Style Guide](../docs/api/STYLE_GUIDE.md)** – QSS customization
- **[Examples Guide](../docs/examples/EXAMPLES.md)** – Detailed examples documentation

---

**EzQt Widgets v2.3.0** – Modern, typed, and beautiful Qt widgets for Python. 🎨
