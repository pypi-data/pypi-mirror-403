# ///////////////////////////////////////////////////////////////
# EZQT_WIDGETS - Main Module
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
ezqt_widgets - Custom Qt widgets collection for PySide6.

ezqt_widgets is a collection of custom and reusable Qt widgets for PySide6.
It provides advanced, reusable, and styled graphical components to facilitate
the development of modern and ergonomic interfaces.

**Main Features:**
    - Enhanced button widgets (date picker, icon buttons, loading buttons)
    - Advanced input widgets (auto-complete, search, tab replacement)
    - Enhanced label widgets (clickable tags, framed labels, hover labels, indicators)
    - Utility widgets (circular timers, draggable lists, option selectors, toggles)
    - Modern and ergonomic UI components
    - Fully typed API with type hints
    - PySide6 compatible

**Quick Start:**
    >>> from ezqt_widgets import DateButton, IconButton, AutoCompleteInput
    >>> from PySide6.QtWidgets import QApplication
    >>>
    >>> app = QApplication([])
    >>>
    >>> # Create a date button
    >>> date_btn = DateButton()
    >>> date_btn.show()
    >>>
    >>> # Create an icon button
    >>> icon_btn = IconButton(icon="path/to/icon.png", text="Click me")
    >>> icon_btn.show()
    >>>
    >>> # Create an auto-complete input
    >>> input_widget = AutoCompleteInput(completions=["option1", "option2"])
    >>> input_widget.show()
    >>>
    >>> app.exec()
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import sys

# Local imports
from .button import (
    DateButton,
    DatePickerDialog,
    IconButton,
    LoaderButton,
)
from .input import (
    AutoCompleteInput,
    SearchInput,
    TabReplaceTextEdit,
)
from .label import (
    ClickableTagLabel,
    FramedLabel,
    HoverLabel,
    IndicatorLabel,
)
from .misc import (
    CircularTimer,
    DraggableItem,
    DraggableList,
    OptionSelector,
    ToggleIcon,
    ToggleSwitch,
)

# ///////////////////////////////////////////////////////////////
# META INFORMATIONS
# ///////////////////////////////////////////////////////////////

__version__ = "2.3.2"
__author__ = "Neuraaak"
__maintainer__ = "Neuraaak"
__description__ = (
    "A collection of custom and reusable Qt widgets for PySide6. "
    "Provides advanced, reusable, and styled graphical components "
    "to facilitate the development of modern and ergonomic interfaces."
)
__python_requires__ = ">=3.10"
__keywords__ = [
    "qt",
    "pyside6",
    "widgets",
    "gui",
    "interface",
    "components",
    "ui",
    "desktop",
]
__url__ = "https://github.com/neuraaak/ezqt_widgets"
__repository__ = "https://github.com/neuraaak/ezqt_widgets"
__license__ = "MIT"

# ///////////////////////////////////////////////////////////////
# PYTHON VERSION CHECK
# ///////////////////////////////////////////////////////////////

if sys.version_info < (3, 10):  # noqa: UP036
    raise RuntimeError(
        f"ezqt_widgets {__version__} requires Python 3.10 or higher. "
        f"Current version: {sys.version}"
    )

# ///////////////////////////////////////////////////////////////
# PUBLIC API
# ///////////////////////////////////////////////////////////////

__all__ = [
    # Button widgets
    "DateButton",
    "DatePickerDialog",
    "IconButton",
    "LoaderButton",
    # Input widgets
    "AutoCompleteInput",
    "SearchInput",
    "TabReplaceTextEdit",
    # Label widgets
    "ClickableTagLabel",
    "FramedLabel",
    "HoverLabel",
    "IndicatorLabel",
    # Miscellaneous widgets
    "CircularTimer",
    "DraggableItem",
    "DraggableList",
    "OptionSelector",
    "ToggleIcon",
    "ToggleSwitch",
    # Metadata
    "__version__",
    "__author__",
    "__maintainer__",
    "__description__",
    "__python_requires__",
    "__keywords__",
    "__url__",
    "__repository__",
    "__license__",
]
