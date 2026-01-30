# ///////////////////////////////////////////////////////////////
# TOGGLE_ICON - Toggle Icon Widget
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Toggle icon widget module.

Provides a label with toggleable icons to indicate an open/closed state
for PySide6 applications.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
import requests
from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QIcon,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPixmap,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QLabel

# ///////////////////////////////////////////////////////////////
# UTILITY FUNCTIONS
# ///////////////////////////////////////////////////////////////


def colorize_pixmap(pixmap: QPixmap, color: QColor) -> QPixmap:
    """Apply a color to a QPixmap with opacity.

    Args:
        pixmap: The pixmap to colorize.
        color: The color to apply.

    Returns:
        The colorized pixmap.
    """
    if pixmap.isNull():
        return pixmap

    colored_pixmap = QPixmap(pixmap.size())
    colored_pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(colored_pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
    painter.setOpacity(color.alphaF())
    painter.fillRect(colored_pixmap.rect(), color)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()

    return colored_pixmap


def load_icon_from_source(
    source: str | QIcon | QPixmap, size: QSize | None = None
) -> QPixmap:
    """Load an icon from various sources (path, URL, QIcon, QPixmap).

    Args:
        source: Icon source (file path, URL, QIcon, or QPixmap).
        size: Desired size for the icon (default: None).

    Returns:
        The loaded icon pixmap.
    """
    if isinstance(source, QPixmap):
        pixmap = source
    elif isinstance(source, QIcon):
        pixmap = source.pixmap(size or QSize(16, 16))
    elif isinstance(source, str):
        if source.startswith(("http://", "https://")):
            # Load from URL
            try:
                response = requests.get(source, timeout=5)
                response.raise_for_status()
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
            except Exception:
                # Fallback to default icon
                pixmap = QPixmap(16, 16)
                pixmap.fill(Qt.GlobalColor.transparent)
        elif source.lower().endswith(".svg"):
            # Load SVG
            renderer = QSvgRenderer(source)
            if renderer.isValid():
                pixmap = QPixmap(size or QSize(16, 16))
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
            else:
                pixmap = QPixmap(16, 16)
                pixmap.fill(Qt.GlobalColor.transparent)
        else:
            # Load from file
            pixmap = QPixmap(source)

    if not pixmap.isNull() and size:
        pixmap = pixmap.scaled(
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    return pixmap


# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class ToggleIcon(QLabel):
    """Label with toggleable icons to indicate an open/closed state.

    Features:
        - Toggleable icons for open/closed states
        - Custom icons or default painted icons
        - Configurable icon size and color
        - Click and keyboard events for toggling
        - Property-based state management

    Args:
        parent: Parent widget (default: None).
        opened_icon: Icon to display when state is "opened".
            If None, uses paintEvent (default: None).
        closed_icon: Icon to display when state is "closed".
            If None, uses paintEvent (default: None).
        icon_size: Icon size in pixels (default: 16).
        icon_color: Color to apply to icons
            (default: white with 0.5 opacity).
        initial_state: Initial state ("opened" or "closed", default: "closed").
        min_width: Minimum width of the widget (default: None).
        min_height: Minimum height of the widget (default: None).
        *args: Additional arguments passed to QLabel.
        **kwargs: Additional keyword arguments passed to QLabel.

    Signals:
        stateChanged(str): Emitted when the state changes ("opened" or "closed").
        clicked(): Emitted when the widget is clicked.
    """

    stateChanged = Signal(str)  # "opened" or "closed"
    clicked = Signal()

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        parent=None,
        opened_icon: str | QIcon | QPixmap | None = None,
        closed_icon: str | QIcon | QPixmap | None = None,
        icon_size: int = 16,
        icon_color: QColor | str | None = None,
        initial_state: str = "closed",
        min_width: int | None = None,
        min_height: int | None = None,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the toggle icon."""
        super().__init__(parent, *args, **kwargs)
        self.setProperty("type", "ToggleIcon")

        # Initialize variables
        self._icon_size = icon_size
        self._icon_color = (
            QColor(255, 255, 255, 128) if icon_color is None else QColor(icon_color)
        )
        self._min_width = min_width
        self._min_height = min_height
        self._state = initial_state

        # Setup icons
        self._use_custom_icons = opened_icon is not None or closed_icon is not None

        if self._use_custom_icons:
            # Use provided icons
            self._opened_icon = (
                load_icon_from_source(
                    opened_icon, QSize(self._icon_size, self._icon_size)
                )
                if opened_icon is not None
                else None
            )
            self._closed_icon = (
                load_icon_from_source(
                    closed_icon, QSize(self._icon_size, self._icon_size)
                )
                if closed_icon is not None
                else None
            )
        else:
            # Use paintEvent to draw icons
            self._opened_icon = None
            self._closed_icon = None

        # Setup widget
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._update_icon()
        self._apply_initial_state()

    # ///////////////////////////////////////////////////////////////
    # PROPERTIES
    # ///////////////////////////////////////////////////////////////

    @property
    def state(self) -> str:
        """Get the current state.

        Returns:
            The current state ("opened" or "closed").
        """
        return self._state

    @state.setter
    def state(self, value: str) -> None:
        """Set the current state.

        Args:
            value: The new state ("opened" or "closed").
        """
        if value not in ("opened", "closed"):
            value = "closed"
        if self._state != value:
            self._state = value
            self._update_icon()
            self.stateChanged.emit(self._state)

    @property
    def opened_icon(self) -> QPixmap | None:
        """Get or set the opened state icon.

        Returns:
            The opened icon pixmap, or None if using default.
        """
        return self._opened_icon

    @opened_icon.setter
    def opened_icon(self, value: str | QIcon | QPixmap) -> None:
        """Set the opened state icon.

        Args:
            value: The icon source (str, QIcon, or QPixmap).
        """
        self._opened_icon = load_icon_from_source(
            value, QSize(self._icon_size, self._icon_size)
        )
        if self._state == "opened":
            self._update_icon()

    @property
    def closed_icon(self) -> QPixmap | None:
        """Get or set the closed state icon.

        Returns:
            The closed icon pixmap, or None if using default.
        """
        return self._closed_icon

    @closed_icon.setter
    def closed_icon(self, value: str | QIcon | QPixmap) -> None:
        """Set the closed state icon.

        Args:
            value: The icon source (str, QIcon, or QPixmap).
        """
        self._closed_icon = load_icon_from_source(
            value, QSize(self._icon_size, self._icon_size)
        )
        if self._state == "closed":
            self._update_icon()

    @property
    def icon_size(self) -> int:
        """Get or set the icon size.

        Returns:
            The current icon size in pixels.
        """
        return self._icon_size

    @icon_size.setter
    def icon_size(self, value: int) -> None:
        """Set the icon size.

        Args:
            value: The new icon size in pixels.
        """
        self._icon_size = int(value)
        # Reload icons with new size
        if hasattr(self, "_opened_icon") and self._opened_icon is not None:
            self._opened_icon = load_icon_from_source(
                self._opened_icon, QSize(self._icon_size, self._icon_size)
            )
        if hasattr(self, "_closed_icon") and self._closed_icon is not None:
            self._closed_icon = load_icon_from_source(
                self._closed_icon, QSize(self._icon_size, self._icon_size)
            )
        self._update_icon()

    @property
    def icon_color(self) -> QColor:
        """Get or set the icon color.

        Returns:
            The current icon color.
        """
        return self._icon_color

    @icon_color.setter
    def icon_color(self, value: QColor | str) -> None:
        """Set the icon color.

        Args:
            value: The new icon color (QColor or str).
        """
        self._icon_color = QColor(value)
        self._update_icon()

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
            value: The new minimum width, or None to auto-calculate.
        """
        self._min_width = int(value) if value is not None else None
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
            value: The new minimum height, or None to auto-calculate.
        """
        self._min_height = int(value) if value is not None else None
        self.updateGeometry()

    # ///////////////////////////////////////////////////////////////
    # EVENT HANDLERS
    # ///////////////////////////////////////////////////////////////

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events.

        Args:
            event: The mouse event.
        """
        self.toggle_state()
        self.clicked.emit()
        super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events.

        Args:
            event: The key event.
        """
        if event.key() in [
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
            Qt.Key.Key_Space,
        ]:
            self.toggle_state()
            self.clicked.emit()
        super().keyPressEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Draw the icon if no custom icon is provided, centered in a square.

        Args:
            event: The paint event.
        """
        if not self._use_custom_icons:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            try:
                rect = self.rect()
                # Calculate centered square
                side = min(rect.width(), rect.height())
                x0 = rect.center().x() - side // 2
                y0 = rect.center().y() - side // 2
                square = QRectF(x0, y0, side, side)
                center_x = square.center().x()
                center_y = square.center().y()
                arrow_size = max(2, self._icon_size // 4)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(self._icon_color)
                if self._state == "opened":
                    points = [
                        QPointF(center_x - arrow_size, center_y - arrow_size // 2),
                        QPointF(center_x + arrow_size, center_y - arrow_size // 2),
                        QPointF(center_x, center_y + arrow_size // 2),
                    ]
                else:
                    points = [
                        QPointF(center_x - arrow_size, center_y + arrow_size // 2),
                        QPointF(center_x + arrow_size, center_y + arrow_size // 2),
                        QPointF(center_x, center_y - arrow_size // 2),
                    ]
                painter.drawPolygon(points)
            finally:
                painter.end()
        else:
            super().paintEvent(event)

    def minimumSizeHint(self) -> QSize:
        """Calculate a minimum square size based on icon and margins.

        Returns:
            The minimum size hint.
        """
        icon_size = self._icon_size
        margins = self.contentsMargins()
        base = icon_size + max(
            margins.left() + margins.right(),
            margins.top() + margins.bottom(),
        )
        min_side = base
        if self._min_width is not None:
            min_side = max(min_side, self._min_width)
        if self._min_height is not None:
            min_side = max(min_side, self._min_height)
        return QSize(min_side, min_side)

    # ///////////////////////////////////////////////////////////////
    # PUBLIC METHODS
    # ///////////////////////////////////////////////////////////////

    def toggle_state(self) -> None:
        """Toggle between opened and closed states."""
        self.state = "opened" if self._state == "closed" else "closed"

    def set_state_opened(self) -> None:
        """Force the state to opened."""
        self.state = "opened"

    def set_state_closed(self) -> None:
        """Force the state to closed."""
        self.state = "closed"

    def is_opened(self) -> bool:
        """Check if the state is opened.

        Returns:
            True if opened, False otherwise.
        """
        return self._state == "opened"

    def is_closed(self) -> bool:
        """Check if the state is closed.

        Returns:
            True if closed, False otherwise.
        """
        return self._state == "closed"

    # ------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------

    def _update_icon(self) -> None:
        """Update the displayed icon based on current state and center the QPixmap."""
        if self._state == "opened":
            self.setProperty("class", "drop_down")
        else:
            self.setProperty("class", "drop_up")
        if self._use_custom_icons:
            icon = self._opened_icon if self._state == "opened" else self._closed_icon
            if icon is not None:
                colored_icon = colorize_pixmap(icon, self._icon_color)
                self.setPixmap(colored_icon)
            self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            self.setPixmap(QPixmap())
            self.update()
        self.refresh_style()

    def _apply_initial_state(self) -> None:
        """Apply the initial state and update QSS properties."""
        if self._state == "opened":
            self.setProperty("class", "drop_down")
        else:
            self.setProperty("class", "drop_up")
        self.refresh_style()

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
