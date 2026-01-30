# ///////////////////////////////////////////////////////////////
# FRAMED_LABEL - Framed Label Widget
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Framed label widget module.

Provides a flexible label widget based on QFrame for advanced styling and
layout in PySide6 applications.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class FramedLabel(QFrame):
    """Flexible label widget based on QFrame for advanced styling.

    This widget encapsulates a QLabel inside a QFrame, allowing you to benefit
    from QFrame's styling and layout capabilities while providing a simple
    interface for text display, alignment, and dynamic style updates.

    Features:
        - Property-based access to the label text and alignment
        - Emits a textChanged(str) signal when the text changes
        - Allows custom stylesheet injection for advanced appearance
        - Suitable for use as a header, section label, or any styled context

    Args:
        text: The initial text to display in the label (default: "").
        parent: The parent widget (default: None).
        alignment: The alignment of the label text
            (default: Qt.AlignmentFlag.AlignCenter).
        style_sheet: Custom stylesheet to apply to the QFrame
            (default: None, uses transparent background).
        min_width: Minimum width constraint for the widget (default: None).
        min_height: Minimum height constraint for the widget (default: None).
        *args: Additional arguments passed to QFrame.
        **kwargs: Additional keyword arguments passed to QFrame.

    Signals:
        textChanged(str): Emitted when the label text changes.
    """

    textChanged = Signal(str)

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        text: str = "",
        parent=None,
        alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignCenter,
        style_sheet: str | None = None,
        min_width: int | None = None,
        min_height: int | None = None,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the framed label."""
        super().__init__(parent, *args, **kwargs)
        self.setProperty("type", "FramedLabel")

        # Initialize properties
        self._min_width: int | None = min_width
        self._min_height: int | None = min_height
        self._alignment: Qt.AlignmentFlag = alignment

        # Setup styling
        self.setStyleSheet(style_sheet or "background-color: transparent;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Setup layout
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(alignment)

        # Setup label
        self.label = QLabel(text, self)
        self.label.setAlignment(alignment)
        layout.addWidget(self.label)

    # ///////////////////////////////////////////////////////////////
    # PROPERTIES
    # ///////////////////////////////////////////////////////////////

    @property
    def text(self) -> str:
        """Get or set the label text.

        Returns:
            The current label text.
        """
        return self.label.text()

    @text.setter
    def text(self, value: str) -> None:
        """Set the label text.

        Args:
            value: The new label text.
        """
        str_value = str(value)
        if str_value != self.label.text():
            self.label.setText(str_value)
            self.textChanged.emit(str_value)

    @property
    def alignment(self) -> Qt.AlignmentFlag:
        """Get or set the alignment of the label.

        Returns:
            The current alignment.
        """
        return self._alignment

    @alignment.setter
    def alignment(self, value: Qt.AlignmentFlag) -> None:
        """Set the alignment of the label.

        Args:
            value: The new alignment.
        """
        self._alignment = value
        self.label.setAlignment(value)
        layout = self.layout()
        if layout is not None:
            layout.setAlignment(value)

    @property
    def min_width(self) -> int | None:
        """Get or set the minimum width.

        Returns:
            The minimum width, or None if not set.
        """
        return self._min_width

    @min_width.setter
    def min_width(self, value: int | None) -> None:
        """Set the minimum width.

        Args:
            value: The minimum width, or None to auto-calculate.
        """
        self._min_width = value
        self.updateGeometry()

    @property
    def min_height(self) -> int | None:
        """Get or set the minimum height.

        Returns:
            The minimum height, or None if not set.
        """
        return self._min_height

    @min_height.setter
    def min_height(self, value: int | None) -> None:
        """Set the minimum height.

        Args:
            value: The minimum height, or None to auto-calculate.
        """
        self._min_height = value
        self.updateGeometry()

    # ///////////////////////////////////////////////////////////////
    # OVERRIDE METHODS
    # ///////////////////////////////////////////////////////////////

    def minimumSizeHint(self) -> QSize:
        """Get the minimum size hint for the widget.

        Returns:
            The minimum size hint.
        """
        font_metrics = self.fontMetrics()
        text_width = font_metrics.horizontalAdvance(self.text)
        text_height = font_metrics.height()

        content_width = text_width + 16  # 8px padding on each side
        content_height = text_height + 8  # 4px padding top/bottom

        min_width = self._min_width if self._min_width is not None else content_width
        min_height = (
            self._min_height if self._min_height is not None else content_height
        )

        return QSize(max(min_width, content_width), max(min_height, content_height))

    # ///////////////////////////////////////////////////////////////
    # STYLE METHODS
    # ///////////////////////////////////////////////////////////////

    def refresh_style(self) -> None:
        """Refresh the widget's style.

        Useful after dynamic stylesheet changes.
        """
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
