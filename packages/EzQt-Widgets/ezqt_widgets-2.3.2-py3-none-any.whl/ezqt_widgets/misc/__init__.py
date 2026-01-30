# ///////////////////////////////////////////////////////////////
# MISC - Miscellaneous Widgets Module
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Miscellaneous widgets module.

This module provides various utility widgets for PySide6 applications,
including circular timers, draggable lists, option selectors, toggle icons,
and toggle switches.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Local imports
from .circular_timer import CircularTimer
from .draggable_list import DraggableItem, DraggableList
from .option_selector import OptionSelector
from .toggle_icon import ToggleIcon
from .toggle_switch import ToggleSwitch

# ///////////////////////////////////////////////////////////////
# PUBLIC API
# ///////////////////////////////////////////////////////////////

__all__ = [
    "CircularTimer",
    "DraggableItem",
    "DraggableList",
    "OptionSelector",
    "ToggleIcon",
    "ToggleSwitch",
]
