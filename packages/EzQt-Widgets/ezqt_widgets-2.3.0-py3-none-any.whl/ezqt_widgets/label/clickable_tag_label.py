# ///////////////////////////////////////////////////////////////
# CLICKABLE_TAG_LABEL - Clickable Tag Label Widget
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Clickable tag label widget module.

Provides a tag-like clickable label with toggleable state for PySide6
applications.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QFont, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class ClickableTagLabel(QFrame):
    """Tag-like clickable label with toggleable state.

    Features:
        - Clickable tag with enabled/disabled state
        - Emits signals on click and state change
        - Customizable text, font, min width/height
        - Customizable status color (traditional name or hex)
        - QSS-friendly (type/class/status properties)
        - Automatic minimum size calculation
        - Keyboard focus and accessibility

    Args:
        name: Text to display in the tag (default: "").
        enabled: Initial state (default: False).
        status_color: Color when selected (default: "#0078d4").
        min_width: Minimum width (default: None, auto-calculated).
        min_height: Minimum height (default: None, auto-calculated).
        parent: Parent widget (default: None).
        *args: Additional arguments passed to QFrame.
        **kwargs: Additional keyword arguments passed to QFrame.

    Signals:
        clicked(): Emitted when the tag is clicked.
        toggle_keyword(str): Emitted with the tag name when toggled.
        stateChanged(bool): Emitted when the enabled state changes.
    """

    clicked = Signal()
    toggle_keyword = Signal(str)
    stateChanged = Signal(bool)

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        name: str = "",
        enabled: bool = False,
        status_color: str = "#0078d4",
        min_width: int | None = None,
        min_height: int | None = None,
        parent=None,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the clickable tag label."""
        super().__init__(parent, *args, **kwargs)

        self.setProperty("type", "ClickableTagLabel")

        # Initialize properties
        self._name: str = name
        self._enabled: bool = enabled
        self._status_color: str = status_color
        self._min_width: int | None = min_width
        self._min_height: int | None = min_height

        # Setup UI
        self._setup_ui()
        self._update_display()

    # ------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------

    def _setup_ui(self) -> None:
        """Setup the user interface components."""
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContentsMargins(4, 0, 4, 0)
        self.setFixedHeight(20)

        self._layout = QHBoxLayout(self)
        self._layout.setObjectName("status_HLayout")
        self._layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(12)

        self._label = QLabel()
        self._label.setObjectName("tag")
        self._label.setFont(QFont("Segoe UI", 8))
        self._label.setLineWidth(0)
        self._label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self._label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._layout.addWidget(self._label, 0, Qt.AlignmentFlag.AlignTop)

        if self._min_width:
            self.setMinimumWidth(self._min_width)
        if self._min_height:
            self.setMinimumHeight(self._min_height)

    def _update_display(self) -> None:
        """Update the display based on current state."""
        self._label.setText(self._name)
        self.setObjectName(self._name)

        if self._enabled:
            self.setProperty("status", "selected")
            self._label.setStyleSheet(
                f"color: {self._status_color}; background-color: transparent; border: none;"
            )
        else:
            self.setProperty("status", "unselected")
            self._label.setStyleSheet(
                "color: rgb(86, 86, 86); background-color: transparent; border: none;"
            )

        self.refresh_style()
        self.adjustSize()

    # ///////////////////////////////////////////////////////////////
    # PROPERTIES
    # ///////////////////////////////////////////////////////////////

    @property
    def name(self) -> str:
        """Get the tag text.

        Returns:
            The current tag text.
        """
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the tag text.

        Args:
            value: The new tag text.
        """
        self._name = str(value)
        self._update_display()
        self.updateGeometry()

    @property
    def enabled(self) -> bool:
        """Get the enabled state.

        Returns:
            True if enabled, False otherwise.
        """
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set the enabled state.

        Args:
            value: The new enabled state.
        """
        if value != self._enabled:
            self._enabled = bool(value)
            self._update_display()
            self.stateChanged.emit(self._enabled)

    @property
    def status_color(self) -> str:
        """Get the status color.

        Returns:
            The current status color.
        """
        return self._status_color

    @status_color.setter
    def status_color(self, value: str) -> None:
        """Set the status color.

        Args:
            value: The new status color.
        """
        self._status_color = str(value)
        if self._enabled:
            self._label.setStyleSheet(
                f"color: {value}; background-color: transparent; border: none;"
            )
            self.refresh_style()

    @property
    def min_width(self) -> int | None:
        """Get the minimum width.

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
        if value:
            self.setMinimumWidth(value)
        self.updateGeometry()

    @property
    def min_height(self) -> int | None:
        """Get the minimum height.

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
        if value:
            self.setMinimumHeight(value)
        self.updateGeometry()

    # ///////////////////////////////////////////////////////////////
    # EVENT HANDLERS
    # ///////////////////////////////////////////////////////////////

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events.

        Args:
            event: The mouse event.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.enabled = not self.enabled
            self.clicked.emit()
            self.toggle_keyword.emit(self._name)
        super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events.

        Args:
            event: The key event.
        """
        if event.key() in [Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            self.enabled = not self.enabled
            self.clicked.emit()
            self.toggle_keyword.emit(self._name)
        else:
            super().keyPressEvent(event)

    # ///////////////////////////////////////////////////////////////
    # OVERRIDE METHODS
    # ///////////////////////////////////////////////////////////////

    def sizeHint(self) -> QSize:
        """Return the recommended size for the widget.

        Returns:
            The recommended size.
        """
        return QSize(80, 24)

    def minimumSizeHint(self) -> QSize:
        """Return the minimum size for the widget.

        Returns:
            The minimum size hint.
        """
        font_metrics = self._label.fontMetrics()
        text_width = font_metrics.horizontalAdvance(self._name)
        min_width = self._min_width if self._min_width is not None else text_width + 16
        min_height = (
            self._min_height
            if self._min_height is not None
            else max(font_metrics.height() + 8, 20)
        )

        return QSize(min_width, min_height)

    # ///////////////////////////////////////////////////////////////
    # STYLE METHODS
    # ///////////////////////////////////////////////////////////////

    def refresh_style(self) -> None:
        """Refresh the widget style.

        Useful after dynamic stylesheet changes.
        """
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
