# Development Guide – ezqt_widgets

## Overview

This guide provides comprehensive instructions for setting up the development environment, using development tools, and contributing to the **ezqt_widgets** project.

---

## 🚀 Environment Setup

### Quick Installation

```bash
# Install package in development mode
pip install -e ".[dev]"

# Or with make (Linux/Mac)
make install-dev
```

### Prerequisites

- **Python**: 3.10 or higher
- **PySide6**: 6.x
- **Git**: For version control

---

## 🛠️ Development Tools

### Code Formatting

#### VSCode (Recommended)

The project includes a complete VSCode configuration in `.vscode/settings.json` that enables:

- **Automatic formatting on save** with Ruff
- **Automatic import organization** with Ruff
- **Real-time linting** with Ruff
- **Test detection** with pytest

#### Recommended VSCode Extensions

Extensions are listed in `.vscode/extensions.json`:

- `ms-python.python` – Complete Python support
- `charliermarsh.ruff` – Ruff formatter and linter
- `ms-python.mypy-type-checker` – Type checking

### Development Commands

#### With Make (Linux/Mac/WSL)

```bash
make help           # Show help
make format         # Format code (ruff)
make lint           # Check code quality
make fix            # Auto-fix issues
make test           # Run tests
make test-cov       # Tests with coverage
make clean          # Clean temporary files
```

#### Native Python Scripts

```bash
# Linting and formatting
python .scripts/dev/lint.py              # Check code quality
python .scripts/dev/lint.py --fix        # Auto-fix issues

# Tests
python tests/run_tests.py --type unit    # Unit tests
python tests/run_tests.py --coverage     # With coverage
python tests/run_tests.py --fast         # Fast tests
```

---

## 📏 Code Standards

### Ruff Configuration

- **Line length**: 88 characters
- **Python versions**: 3.10, 3.11, 3.12
- **Auto-format on save**: Enabled

### Type Hints

- **Required**: All public functions and methods
- **Style**: Use native types (`list`, `dict`) with `from __future__ import annotations`

### Docstrings

- **Format**: Google-style
- **Language**: English
- **Required**: All public classes, methods, and functions

### Section Markers

Use consistent section markers in Python files:

```python
# ///////////////////////////////////////////////////////////////
# SECTION NAME
# ///////////////////////////////////////////////////////////////
```

---

## 🔒 Pre-commit Hooks

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

### Automatic Checks

Hooks run before each commit:

- Formatting with Ruff
- Import organization with Ruff
- Linting with Ruff
- Type checking with mypy
- General checks (trailing whitespace, etc.)

---

## 🧪 Testing

### Test Structure

```
tests/
├── conftest.py                 # Pytest configuration
├── run_tests.py               # Test runner script
└── unit/                      # Unit tests
    ├── test_button/
    ├── test_input/
    ├── test_label/
    └── test_misc/
```

### Running Tests

```bash
# Fast tests
python tests/run_tests.py --type unit --fast

# Complete tests with coverage
python tests/run_tests.py --coverage

# Specific tests
pytest tests/unit/test_button/ -v
```

### Current Metrics

- **305+ tests** total
- **~79% coverage** overall
- **Real-time output** during test execution

---

## 📦 CLI Integration

The project includes a complete CLI accessible via `ezqt`:

```bash
# Package information
ezqt info

# Run examples
ezqt run --all
ezqt run --buttons
ezqt run --inputs

# Tests from CLI
ezqt test --unit
ezqt test --coverage
```

---

## 🔧 Recommended Development Workflow

### 1. Before Starting

```bash
# Update dependencies
pip install -e ".[dev]"

# Install hooks
pre-commit install
```

### 2. During Development

- **VSCode** will auto-format on save
- **Or manually**: `make format`
- **Quick tests**: `make test`

### 3. Before Committing

```bash
# Complete verification
make check        # format + lint + test

# Or step by step
make format       # Format
make lint         # Check
make test         # Test
```

### 4. Pre-commit hooks run automatically

---

## 🐛 Debugging

### Common Issues

#### Ruff not formatting

- Check installation: `ruff --version`
- Check VSCode config in `.vscode/settings.json`

#### Tests failing

- Check PySide6: `python -c "import PySide6; print(PySide6.__version__)"`
- Clean: `make clean`

#### Pre-commit hooks

- Reinstall: `pre-commit clean && pre-commit install`
- Skip temporarily: `git commit --no-verify`

---

## 📁 Project Structure

```
ezqt_widgets/
├── .vscode/              # VSCode configuration
├── docs/                 # Documentation
├── ezqt_widgets/         # Source code
│   ├── button/          # Button widgets
│   ├── input/           # Input widgets
│   ├── label/           # Label widgets
│   ├── misc/            # Misc widgets
│   └── cli/             # CLI interface
├── examples/            # Usage examples
├── tests/               # Test suite
├── pyproject.toml       # Project configuration
├── .pre-commit-config.yaml  # Pre-commit hooks
└── Makefile            # Make commands
```

---

## 📝 Conventions

### Commits

- **Format**: Clear and concise description
- **Language**: English preferred

### Code

- **Type hints**: Required
- **Docstrings**: Google-style format
- **Section markers**: `# //////` for major sections
- **Tests**: Required for each widget

### Documentation

- **API**: English
- **Comments**: English
- **README**: English

---

## 🔗 Additional Resources

- **[API Documentation](api/API_DOCUMENTATION.md)** – Complete API reference
- **[Test Documentation](tests/TEST_DOCUMENTATION.md)** – Testing guide
- **[CLI Documentation](cli/CLI_DOCUMENTATION.md)** – CLI reference

---

**ezqt_widgets Development Guide** – Your reference for contributing to the project.
