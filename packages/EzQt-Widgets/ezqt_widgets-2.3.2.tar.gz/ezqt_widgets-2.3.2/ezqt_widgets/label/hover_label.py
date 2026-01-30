# ///////////////////////////////////////////////////////////////
# HOVER_LABEL - Hover Label Widget
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Hover label widget module.

Provides an interactive QLabel that displays a floating icon when hovered
for PySide6 applications.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
import requests
from PySide6.QtCore import QEvent, QRect, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QEnterEvent,
    QIcon,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPixmap,
    QResizeEvent,
)
from PySide6.QtWidgets import QLabel

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class HoverLabel(QLabel):
    """Interactive QLabel that displays a floating icon when hovered.

    This widget is useful for adding contextual actions or visual cues to
    labels in a Qt interface.

    Features:
        - Displays a custom icon on hover with configurable opacity, size,
          color overlay, and padding
        - Emits a hoverIconClicked signal when the icon is clicked
        - Handles mouse events and cursor changes for better UX
        - Text and icon can be set at construction or via properties
        - Icon can be enabled/disabled dynamically
        - Supports PNG/JPG and SVG icons (local, resource, URL)
        - Robust error handling for icon loading

    Use cases:
        - Contextual action button in a label
        - Info or help icon on hover
        - Visual feedback for interactive labels

    Args:
        parent: The parent widget (default: None).
        icon: The icon to display on hover (QIcon, path, resource, URL, or SVG).
        text: The label text (default: "").
        opacity: The opacity of the hover icon (default: 0.5).
        icon_size: The size of the hover icon (default: QSize(16, 16)).
        icon_color: Optional color overlay to apply to the icon (default: None).
        icon_padding: Padding (in px) to the right of the text for the icon
            (default: 8).
        icon_enabled: Whether the icon is shown on hover (default: True).
        min_width: Minimum width of the widget (default: None).
        *args: Additional arguments passed to QLabel.
        **kwargs: Additional keyword arguments passed to QLabel.

    Signals:
        hoverIconClicked(): Emitted when the hover icon is clicked.

    Example:
        >>> label = HoverLabel(
        ...     text="Hover me!",
        ...     icon="/path/to/icon.png",
        ...     icon_color="#00BFFF"
        ... )
        >>> label.icon_enabled = True
        >>> label.icon_padding = 12
        >>> label.clear_icon()
    """

    hoverIconClicked = Signal()

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        parent=None,
        icon: QIcon | str | None = None,
        text: str = "",
        opacity: float = 0.5,
        icon_size: QSize | tuple[int, int] = QSize(16, 16),
        icon_color: QColor | str | None = None,
        icon_padding: int = 8,
        icon_enabled: bool = True,
        min_width: int | None = None,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the hover label."""
        super().__init__(parent, *args, text=text or "", **kwargs)
        self.setProperty("type", "HoverLabel")

        # Initialize properties
        self._opacity: float = opacity
        self._hover_icon: QIcon | None = None
        self._icon_size: QSize = (
            QSize(*icon_size) if isinstance(icon_size, (tuple, list)) else icon_size
        )
        self._icon_color: QColor | str | None = icon_color
        self._icon_padding: int = icon_padding
        self._icon_enabled: bool = icon_enabled
        self._min_width: int | None = min_width

        # State variables
        self._show_hover_icon: bool = False

        # Setup widget
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.ArrowCursor)

        # Set minimum width
        if self._min_width:
            self.setMinimumWidth(self._min_width)

        # Set icon if provided
        if icon:
            self.hover_icon = icon

    # ///////////////////////////////////////////////////////////////
    # PROPERTIES
    # ///////////////////////////////////////////////////////////////

    @property
    def opacity(self) -> float:
        """Get the opacity of the hover icon.

        Returns:
            The current opacity level.
        """
        return self._opacity

    @opacity.setter
    def opacity(self, value: float) -> None:
        """Set the opacity of the hover icon.

        Args:
            value: The new opacity level.
        """
        self._opacity = float(value)
        self.update()

    @property
    def hover_icon(self) -> QIcon | None:
        """Get the hover icon.

        Returns:
            The current hover icon, or None if not set.
        """
        return self._hover_icon

    @hover_icon.setter
    def hover_icon(self, value: QIcon | str | None) -> None:
        """Set the icon displayed on hover.

        Accepts QIcon, str (path, resource, URL, or SVG), or None.

        Args:
            value: The icon source.

        Raises:
            ValueError: If icon loading fails.
            TypeError: If value is not a valid type.
        """
        if value is None:
            self._hover_icon = None
        elif isinstance(value, QIcon):
            self._hover_icon = value
        elif isinstance(value, str):
            # Handle URL
            if value.startswith(("http://", "https://")):
                print(f"Loading icon from URL: {value}")
                try:
                    response = requests.get(value, timeout=5)
                    response.raise_for_status()
                    if "image" not in response.headers.get("Content-Type", ""):
                        raise ValueError("URL does not point to an image file.")
                    image_data = response.content

                    # Handle SVG from URL
                    if value.lower().endswith(".svg"):
                        from PySide6.QtCore import QByteArray
                        from PySide6.QtSvg import QSvgRenderer

                        renderer = QSvgRenderer(QByteArray(image_data))
                        pixmap = QPixmap(self._icon_size)
                        pixmap.fill(Qt.GlobalColor.transparent)
                        painter = QPainter(pixmap)
                        renderer.render(painter)
                        painter.end()
                        self._hover_icon = QIcon(pixmap)
                    # Handle raster image from URL
                    else:
                        pixmap = QPixmap()
                        if not pixmap.loadFromData(image_data):
                            raise ValueError(
                                "Failed to load image data from URL (unsupported format or corrupt image)."
                            )
                        self._hover_icon = QIcon(pixmap)
                except Exception as e:
                    raise ValueError(f"Failed to load icon from URL: {e}") from e

            # Handle local SVG
            elif value.lower().endswith(".svg"):
                try:
                    from PySide6.QtCore import QFile
                    from PySide6.QtSvg import QSvgRenderer

                    file = QFile(value)
                    if not file.open(QFile.OpenModeFlag.ReadOnly):
                        raise ValueError(f"Cannot open SVG file: {value}")
                    svg_data = file.readAll()
                    file.close()
                    renderer = QSvgRenderer(svg_data)
                    pixmap = QPixmap(self._icon_size)
                    pixmap.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(pixmap)
                    renderer.render(painter)
                    painter.end()
                    self._hover_icon = QIcon(pixmap)
                except Exception as e:
                    raise ValueError(f"Failed to load SVG icon: {e}") from e

            # Handle local/resource raster image
            else:
                icon = QIcon(value)
                if icon.isNull():
                    raise ValueError(f"Invalid icon path: {value}")
                self._hover_icon = icon
        else:
            raise TypeError("hover_icon must be a QIcon, a path string, or None.")

        self._update_padding_style()
        self.update()

    @property
    def icon_size(self) -> QSize:
        """Get or set the size of the hover icon.

        Returns:
            The current icon size.
        """
        return self._icon_size

    @icon_size.setter
    def icon_size(self, value: QSize | tuple[int, int]) -> None:
        """Set the size of the hover icon.

        Args:
            value: The new icon size (QSize or tuple).

        Raises:
            TypeError: If value is not a valid type.
        """
        if isinstance(value, QSize):
            self._icon_size = value
        elif isinstance(value, (tuple, list)) and len(value) == 2:
            self._icon_size = QSize(*value)
        else:
            raise TypeError(
                "icon_size must be a QSize or a tuple/list of two integers."
            )
        self._update_padding_style()
        self.update()

    @property
    def icon_color(self) -> QColor | str | None:
        """Get or set the color overlay of the hover icon.

        Returns:
            The current icon color (QColor, str, or None).
        """
        return self._icon_color

    @icon_color.setter
    def icon_color(self, value: QColor | str | None) -> None:
        """Set the color overlay of the hover icon.

        Args:
            value: The new icon color (QColor, str, or None).
        """
        self._icon_color = value
        self.update()

    @property
    def icon_padding(self) -> int:
        """Get or set the right padding for the icon.

        Returns:
            The current icon padding in pixels.
        """
        return self._icon_padding

    @icon_padding.setter
    def icon_padding(self, value: int) -> None:
        """Set the right padding for the icon.

        Args:
            value: The new padding in pixels.
        """
        self._icon_padding = int(value)
        self._update_padding_style()
        self.update()

    @property
    def icon_enabled(self) -> bool:
        """Enable or disable the hover icon.

        Returns:
            True if icon is enabled, False otherwise.
        """
        return self._icon_enabled

    @icon_enabled.setter
    def icon_enabled(self, value: bool) -> None:
        """Set whether the icon is enabled.

        Args:
            value: Whether to enable the icon.
        """
        self._icon_enabled = bool(value)
        self._update_padding_style()
        self.update()

    # ///////////////////////////////////////////////////////////////
    # PUBLIC METHODS
    # ///////////////////////////////////////////////////////////////

    def clear_icon(self) -> None:
        """Remove the hover icon."""
        self._hover_icon = None
        self._update_padding_style()
        self.update()

    # ------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------

    def _update_padding_style(self) -> None:
        """Update the padding style based on icon state."""
        padding = (
            self._icon_size.width() + self._icon_padding
            if self._hover_icon and self._icon_enabled
            else 0
        )
        self.setStyleSheet(f"padding-right: {padding}px;")

    # ///////////////////////////////////////////////////////////////
    # EVENT HANDLERS
    # ///////////////////////////////////////////////////////////////

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse movement events.

        Args:
            event: The mouse event.
        """
        if not self._icon_enabled or not self._hover_icon:
            super().mouseMoveEvent(event)
            return

        icon_x = self.width() - self._icon_size.width() - 4
        icon_y = (self.height() - self._icon_size.height()) // 2
        icon_rect = QRect(
            icon_x, icon_y, self._icon_size.width(), self._icon_size.height()
        )

        if icon_rect.contains(event.pos()):
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events.

        Args:
            event: The mouse event.
        """
        if not self._icon_enabled or not self._hover_icon:
            super().mousePressEvent(event)
            return

        icon_x = self.width() - self._icon_size.width() - 4
        icon_y = (self.height() - self._icon_size.height()) // 2
        icon_rect = QRect(
            icon_x, icon_y, self._icon_size.width(), self._icon_size.height()
        )

        if (
            icon_rect.contains(event.position().toPoint())
            and event.button() == Qt.MouseButton.LeftButton
        ):
            self.hoverIconClicked.emit()
        else:
            super().mousePressEvent(event)

    def enterEvent(self, event: QEnterEvent) -> None:
        """Handle enter events.

        Args:
            event: The enter event.
        """
        self._show_hover_icon = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        """Handle leave events.

        Args:
            event: The leave event.
        """
        self._show_hover_icon = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint the widget.

        Args:
            event: The paint event.
        """
        super().paintEvent(event)

        # Draw hover icon if needed
        if self._show_hover_icon and self._hover_icon and self._icon_enabled:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setOpacity(self._opacity)

            icon_x = self.width() - self._icon_size.width() - 4
            icon_y = (self.height() - self._icon_size.height()) // 2
            icon_rect = QRect(
                icon_x, icon_y, self._icon_size.width(), self._icon_size.height()
            )

            icon_pixmap = self._hover_icon.pixmap(self._icon_size)

            # Apply color overlay if specified
            if self._icon_color and not icon_pixmap.isNull():
                colored_pixmap = QPixmap(icon_pixmap.size())
                colored_pixmap.fill(Qt.GlobalColor.transparent)
                overlay_painter = QPainter(colored_pixmap)
                overlay_painter.setCompositionMode(
                    QPainter.CompositionMode.CompositionMode_SourceOver
                )
                overlay_painter.fillRect(
                    colored_pixmap.rect(), QColor(self._icon_color)
                )
                overlay_painter.setCompositionMode(
                    QPainter.CompositionMode.CompositionMode_DestinationIn
                )
                overlay_painter.drawPixmap(0, 0, icon_pixmap)
                overlay_painter.end()
                painter.drawPixmap(icon_rect, colored_pixmap)
            elif not icon_pixmap.isNull():
                painter.drawPixmap(icon_rect, icon_pixmap)

    # ///////////////////////////////////////////////////////////////
    # OVERRIDE METHODS
    # ///////////////////////////////////////////////////////////////

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle resize events.

        Args:
            event: The resize event.
        """
        super().resizeEvent(event)
        self.update()

    def minimumSizeHint(self) -> QSize:
        """Get the minimum size hint for the widget.

        Returns:
            The minimum size hint.
        """
        base = super().minimumSizeHint()
        min_width = self._min_width if self._min_width is not None else base.width()
        return QSize(min_width, base.height())

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
