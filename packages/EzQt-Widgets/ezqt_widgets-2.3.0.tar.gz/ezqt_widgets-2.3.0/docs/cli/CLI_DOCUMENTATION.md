# CLI Documentation – ezqt_widgets

## Overview

This document provides complete documentation for the **ezqt_widgets** command-line interface (CLI). The CLI provides tools for running examples, managing tests, and exploring widget functionality.

## Table of Contents

- [CLI Documentation – ezqt\_widgets](#cli-documentation--ezqt_widgets)
  - [Overview](#overview)
  - [Table of Contents](#table-of-contents)
  - [🚀 Quick Start](#-quick-start)
    - [Installation](#installation)
    - [Basic Usage](#basic-usage)
  - [📋 Commands Reference](#-commands-reference)
    - [`ezqt run` – Run Examples](#ezqt-run--run-examples)
    - [`ezqt list` – List Examples](#ezqt-list--list-examples)
    - [`ezqt test` – Run Tests](#ezqt-test--run-tests)
    - [`ezqt info` – Package Information](#ezqt-info--package-information)
  - [🎯 Use Cases](#-use-cases)
    - [For Developers](#for-developers)
    - [For Users](#for-users)
  - [🔧 Configuration](#-configuration)
    - [Environment Variables](#environment-variables)
    - [Example Detection](#example-detection)
  - [🐛 Troubleshooting](#-troubleshooting)
    - [Common Issues](#common-issues)
    - [Debug Mode](#debug-mode)
  - [Additional Resources](#additional-resources)

---

## 🚀 Quick Start

### Installation

```bash
# Install in development mode
pip install -e ".[dev]"

# Verify installation
ezqt --version
```

### Basic Usage

```bash
# Run all examples with GUI launcher
ezqt run --all

# Run specific example categories
ezqt run --buttons
ezqt run --inputs
ezqt run --labels
ezqt run --misc

# List available examples
ezqt list

# Show package information
ezqt info
```

---

## 📋 Commands Reference

### `ezqt run` – Run Examples

Launch interactive examples to explore widget functionality.

**Syntax:**

```bash
ezqt run [OPTIONS]
```

**Options:**

| Option      | Short | Description                                                                                |
| ----------- | ----- | ------------------------------------------------------------------------------------------ |
| `--all`     | `-a`  | Run all examples with GUI launcher                                                         |
| `--buttons` | `-b`  | Run button examples (DateButton, IconButton, LoaderButton)                                 |
| `--inputs`  | `-i`  | Run input examples (AutoComplete, Search, TabReplace)                                      |
| `--labels`  | `-l`  | Run label examples (ClickableTag, Framed, Hover, Indicator)                                |
| `--misc`    | `-m`  | Run misc examples (CircularTimer, DraggableList, OptionSelector, ToggleIcon, ToggleSwitch) |
| `--no-gui`  |       | Run examples sequentially without GUI launcher                                             |
| `--verbose` | `-v`  | Verbose output with detailed information                                                   |

**Examples:**

```bash
# Run all examples with GUI
ezqt run --all

# Run only button examples
ezqt run --buttons

# Run input examples with verbose output
ezqt run --inputs --verbose

# Run all examples sequentially (no GUI)
ezqt run --all --no-gui

# Run misc examples with detailed output
ezqt run --misc -v
```

---

### `ezqt list` – List Examples

Show all available example files and their status.

**Syntax:**

```bash
ezqt list
```

**Output:**

```
📋 Available examples:
========================================
✅ button_example
✅ input_example
✅ label_example
✅ misc_example
✅ run_all_examples

Total: 5 examples found
```

---

### `ezqt test` – Run Tests

Execute the test suite for ezqt_widgets.

**Syntax:**

```bash
ezqt test [OPTIONS]
```

**Options:**

| Option       | Short | Description             |
| ------------ | ----- | ----------------------- |
| `--unit`     | `-u`  | Run unit tests          |
| `--coverage` | `-c`  | Run tests with coverage |
| `--verbose`  | `-v`  | Verbose output          |

**Examples:**

```bash
# Run unit tests
ezqt test --unit

# Run tests with coverage
ezqt test --coverage

# Run both with verbose output
ezqt test --unit --coverage --verbose
```

---

### `ezqt info` – Package Information

Display information about ezqt_widgets installation.

**Syntax:**

```bash
ezqt info
```

**Output:**

```
🎨 EzQt Widgets Information
========================================
Version: 2.3.0
Location: /path/to/ezqt_widgets/__init__.py
PySide6: 6.9.1
Examples: 5 found
========================================
```

---

## 🎯 Use Cases

### For Developers

```bash
# Quick testing during development
ezqt run --buttons --verbose

# Run tests before commit
ezqt test --coverage

# Check package status
ezqt info
```

### For Users

```bash
# Explore all widgets
ezqt run --all

# Focus on specific widget type
ezqt run --inputs

# See what's available
ezqt list
```

---

## 🔧 Configuration

### Environment Variables

| Variable            | Description                    |
| ------------------- | ------------------------------ |
| `EZQT_VERBOSE`      | Enable verbose mode by default |
| `EZQT_EXAMPLES_DIR` | Custom examples directory path |

### Example Detection

The CLI automatically detects examples in the following locations (in order):

1. Project root `/examples/` directory
2. Current working directory `/examples/`
3. Package directory `/ezqt_widgets/examples/`

---

## 🐛 Troubleshooting

### Common Issues

| Issue                  | Solution                                                    |
| ---------------------- | ----------------------------------------------------------- |
| **Command not found**  | Install in dev mode: `pip install -e ".[dev]"`              |
| **Examples not found** | Check if examples directory exists in project root          |
| **Import errors**      | Verify PySide6 installation: `pip install PySide6`          |
| **Permission errors**  | Run with appropriate permissions or use virtual environment |

### Debug Mode

```bash
# Enable verbose output
ezqt run --buttons --verbose

# Check package installation
ezqt info
```

---

## Additional Resources

- **[API Documentation](../api/API_DOCUMENTATION.md)** – Complete widget reference
- **[Examples](../examples/EXAMPLES.md)** – Usage examples
- **[Test Documentation](../tests/TEST_DOCUMENTATION.md)** – Testing patterns
- **[Style Guide](../api/STYLE_GUIDE.md)** – QSS customization

---

**ezqt_widgets CLI** – Command-line tools for development and exploration.
