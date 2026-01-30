# ///////////////////////////////////////////////////////////////
# INPUT - Input Widgets Module
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Input widgets module.

This module provides various input widgets for PySide6 applications,
including auto-complete inputs, search inputs, and text editors with
tab replacement functionality.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Local imports
from .auto_complete_input import AutoCompleteInput
from .search_input import SearchInput
from .tab_replace_textedit import TabReplaceTextEdit

# ///////////////////////////////////////////////////////////////
# PUBLIC API
# ///////////////////////////////////////////////////////////////

__all__ = [
    "AutoCompleteInput",
    "SearchInput",
    "TabReplaceTextEdit",
]
