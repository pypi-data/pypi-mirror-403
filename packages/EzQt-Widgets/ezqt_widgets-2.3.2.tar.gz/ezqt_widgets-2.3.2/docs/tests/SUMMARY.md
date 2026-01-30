# Test Summary

**ezqt_widgets** – Test suite for custom Qt widgets collection.

## 📖 Complete Documentation

For detailed test documentation, see **[TEST_DOCUMENTATION.md](TEST_DOCUMENTATION.md)**.

---

## Quick Overview

### Test Structure

- **Unit Tests** – Individual component testing with isolated test cases
- **Comprehensive Coverage** – All widgets, properties, signals, and methods tested
- **Real-time Output** – Tests display output in real-time during execution

### Test Organization

```
tests/
├── conftest.py          # Shared fixtures and pytest configuration
├── run_tests.py         # Test runner script (real-time output)
├── unit/                # Unit tests
│   ├── test_button/    # Button widget tests
│   ├── test_input/     # Input widget tests
│   ├── test_label/     # Label widget tests
│   └── test_misc/      # Misc widget tests
```

### Quick Start

```bash
# Run all unit tests
python tests/run_tests.py --type unit

# Run with coverage
python tests/run_tests.py --coverage

# Run specific test module
pytest tests/unit/test_button/ -v
```

### Test Statistics

**Current Status:**

- **Total Tests**: ~211 tests
- **Coverage**: ~80%
- **Status**: ✅ All passing

### Tests by Module

**Button Widgets (`test_button/`):**

- **DateButton**: 20 tests – Date selection with calendar
- **IconButton**: 17 tests – Button with icon support
- **LoaderButton**: 22 tests – Button with loading states

**Input Widgets (`test_input/`):**

- **AutoCompleteInput**: 17 tests – Field with autocompletion
- **SearchInput**: 20 tests – Search field with history
- **TabReplaceTextEdit**: 25 tests – Editor with tab replacement

**Label Widgets (`test_label/`):**

- **ClickableTagLabel**: Multiple tests – Clickable tag functionality
- **FramedLabel**: Multiple tests – Framed label functionality
- **HoverLabel**: Multiple tests – Label with hover functionality
- **IndicatorLabel**: Multiple tests – Status indicator functionality

**Miscellaneous Widgets (`test_misc/`):**

- **CircularTimer**: Multiple tests – Circular timer functionality
- **DraggableList**: Multiple tests – Draggable list functionality
- **OptionSelector**: Multiple tests – Option selector functionality
- **ToggleIcon**: Multiple tests – Toggle icon functionality
- **ToggleSwitch**: Multiple tests – Toggle switch functionality

### Test Fixtures

| Fixture             | Description                         |
| ------------------- | ----------------------------------- |
| `qt_application`    | QApplication instance for all tests |
| `qt_widget_cleanup` | Widget cleanup after each test      |
| `wait_for_signal`   | Helper to wait for Qt signals       |
| `mock_icon_path`    | Temporary icon file for testing     |
| `mock_svg_path`     | Temporary SVG file for testing      |

### Running Tests

**Using pytest:**

```bash
# All tests
pytest tests/

# Specific directory
pytest tests/unit/test_button/

# With coverage
pytest --cov=ezqt_widgets --cov-report=html tests/
```

**Using run_tests.py:**

```bash
# Unit tests
python tests/run_tests.py --type unit

# With coverage
python tests/run_tests.py --coverage

# Verbose mode
python tests/run_tests.py --verbose
```

---

**For complete test documentation with examples, see [TEST_DOCUMENTATION.md](TEST_DOCUMENTATION.md).**
