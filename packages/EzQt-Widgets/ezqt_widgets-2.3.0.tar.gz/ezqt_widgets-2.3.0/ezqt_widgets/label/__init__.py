# ///////////////////////////////////////////////////////////////
# LABEL - Label Widgets Module
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Label widgets module.

This module provides enhanced label widgets for PySide6 applications,
including clickable tags, framed labels, hover labels, and indicator labels.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Local imports
from .clickable_tag_label import ClickableTagLabel
from .framed_label import FramedLabel
from .hover_label import HoverLabel
from .indicator_label import IndicatorLabel

# ///////////////////////////////////////////////////////////////
# PUBLIC API
# ///////////////////////////////////////////////////////////////

__all__ = [
    "ClickableTagLabel",
    "FramedLabel",
    "HoverLabel",
    "IndicatorLabel",
]
