# ///////////////////////////////////////////////////////////////
# ICON_BUTTON - Icon Button Widget
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Icon button widget module.

Provides an enhanced button widget with icon and optional text support
for PySide6 applications.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
import requests
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QToolButton
from typing_extensions import override

# ///////////////////////////////////////////////////////////////
# UTILITY FUNCTIONS
# ///////////////////////////////////////////////////////////////


def colorize_pixmap(
    pixmap: QPixmap, color: str = "#FFFFFF", opacity: float = 0.5
) -> QPixmap:
    """Recolor a QPixmap with the given color and opacity.

    Args:
        pixmap: The pixmap to recolor.
        color: The color to apply (default: "#FFFFFF").
        opacity: The opacity level (default: 0.5).

    Returns:
        The recolored pixmap.
    """
    result = QPixmap(pixmap.size())
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.setOpacity(opacity)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(result.rect(), QColor(color))
    painter.end()
    return result


def load_icon_from_source(source: QIcon | str | None) -> QIcon | None:
    """Load icon from various sources (QIcon, path, URL, etc.).

    Supports loading icons from:
        - QIcon objects (returned as-is)
        - Local file paths (PNG, JPG, etc.)
        - Local SVG files
        - Remote URLs (HTTP/HTTPS)
        - Remote SVG URLs

    Args:
        source: Icon source (QIcon, path, resource, URL, or SVG).

    Returns:
        Loaded icon or None if loading failed.
    """
    if source is None:
        return None
    elif isinstance(source, QIcon):
        return source
    elif isinstance(source, str):
        # Handle URL
        if source.startswith(("http://", "https://")):
            print(f"Loading icon from URL: {source}")
            try:
                response = requests.get(source, timeout=5)
                response.raise_for_status()
                if "image" not in response.headers.get("Content-Type", ""):
                    raise ValueError("URL does not point to an image file.")
                image_data = response.content

                # Handle SVG from URL
                if source.lower().endswith(".svg"):
                    from PySide6.QtCore import QByteArray
                    from PySide6.QtSvg import QSvgRenderer

                    renderer = QSvgRenderer(QByteArray(image_data))
                    pixmap = QPixmap(QSize(16, 16))
                    pixmap.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(pixmap)
                    renderer.render(painter)
                    painter.end()
                    return QIcon(pixmap)

                # Handle raster image from URL
                else:
                    pixmap = QPixmap()
                    if not pixmap.loadFromData(image_data):
                        raise ValueError("Failed to load image data from URL.")
                    pixmap = colorize_pixmap(pixmap, "#FFFFFF", 0.5)
                    return QIcon(pixmap)
            except Exception as e:
                print(f"Failed to load icon from URL: {e}")
                return None

        # Handle local SVG
        elif source.lower().endswith(".svg"):
            try:
                from PySide6.QtCore import QFile
                from PySide6.QtSvg import QSvgRenderer

                file = QFile(source)
                if not file.open(QFile.OpenModeFlag.ReadOnly):
                    raise ValueError(f"Cannot open SVG file: {source}")
                svg_data = file.readAll()
                file.close()
                renderer = QSvgRenderer(svg_data)
                pixmap = QPixmap(QSize(16, 16))
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                return QIcon(pixmap)
            except Exception as e:
                print(f"Failed to load SVG icon: {e}")
                return None

        # Handle local/resource raster image
        else:
            icon = QIcon(source)
            if icon.isNull():
                print(f"Invalid icon path: {source}")
                return None
            return icon


# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class IconButton(QToolButton):
    """Enhanced button widget with icon and optional text support.

    Features:
        - Icon support from various sources (QIcon, path, URL, SVG)
        - Optional text display with configurable visibility
        - Customizable icon size and spacing
        - Property-based access to icon and text
        - Signals for icon and text changes
        - Hover and click effects

    Args:
        parent: The parent widget (default: None).
        icon: The icon to display (QIcon, path, resource, URL, or SVG).
        text: The button text (default: "").
        icon_size: Size of the icon (default: QSize(20, 20)).
        text_visible: Whether the text is initially visible (default: True).
        spacing: Spacing between icon and text in pixels (default: 10).
        min_width: Minimum width of the button (default: None, auto-calculated).
        min_height: Minimum height of the button (default: None, auto-calculated).
        *args: Additional arguments passed to QToolButton.
        **kwargs: Additional keyword arguments passed to QToolButton.

    Signals:
        iconChanged(QIcon): Emitted when the icon changes.
        textChanged(str): Emitted when the text changes.
    """

    iconChanged = Signal(QIcon)
    textChanged = Signal(str)

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        parent=None,
        icon: QIcon | str | None = None,
        text: str = "",
        icon_size: QSize | tuple[int, int] = QSize(20, 20),
        text_visible: bool = True,
        spacing: int = 10,
        min_width: int | None = None,
        min_height: int | None = None,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the icon button."""
        super().__init__(parent, *args, **kwargs)
        self.setProperty("type", "IconButton")

        # Initialize properties
        self._icon_size: QSize = (
            QSize(*icon_size)
            if isinstance(icon_size, (tuple, list))
            else QSize(icon_size)
        )
        self._text_visible: bool = text_visible
        self._spacing: int = spacing
        self._current_icon: QIcon | None = None
        self._min_width: int | None = min_width
        self._min_height: int | None = min_height

        # Setup UI components
        self.icon_label = QLabel()
        self.text_label = QLabel()

        # Configure text label
        self.text_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("background-color: transparent;")

        # Setup layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(spacing)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)

        # Configure size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Set initial values
        if icon:
            self.icon = icon
        if text:
            self.text = text
        self.text_visible = text_visible

    # ///////////////////////////////////////////////////////////////
    # PROPERTIES
    # ///////////////////////////////////////////////////////////////

    @property
    @override
    def icon(
        self,
    ) -> QIcon | None:
        """Get or set the button icon.

        Returns:
            The current icon, or None if no icon is set.
        """
        return self._current_icon

    @icon.setter
    def icon(self, value: QIcon | str | None) -> None:
        """Set the button icon from various sources.

        Args:
            value: The icon source (QIcon, path, URL, or SVG).
        """
        icon = load_icon_from_source(value)
        if icon:
            self._current_icon = icon
            self.icon_label.setPixmap(icon.pixmap(self._icon_size))
            self.icon_label.setFixedSize(self._icon_size)
            self.icon_label.setStyleSheet("background-color: transparent;")
            self.iconChanged.emit(icon)

    @property
    @override
    def text(
        self,
    ) -> str:
        """Get or set the button text.

        Returns:
            The current button text.
        """
        return self.text_label.text()

    @text.setter
    def text(self, value: str) -> None:
        """Set the button text.

        Args:
            value: The new button text.
        """
        if value != self.text_label.text():
            self.text_label.setText(str(value))
            self.textChanged.emit(str(value))

    @property
    def icon_size(self) -> QSize:
        """Get or set the icon size.

        Returns:
            The current icon size.
        """
        return self._icon_size

    @icon_size.setter
    def icon_size(self, value: QSize | tuple[int, int]) -> None:
        """Set the icon size.

        Args:
            value: The new icon size (QSize or tuple).
        """
        self._icon_size = (
            QSize(*value) if isinstance(value, (tuple, list)) else QSize(value)
        )
        if self._current_icon:
            self.icon_label.setPixmap(self._current_icon.pixmap(self._icon_size))
            self.icon_label.setFixedSize(self._icon_size)

    @property
    def text_visible(self) -> bool:
        """Get or set text visibility.

        Returns:
            True if text is visible, False otherwise.
        """
        return self._text_visible

    @text_visible.setter
    def text_visible(self, value: bool) -> None:
        """Set text visibility.

        Args:
            value: Whether to show the text.
        """
        self._text_visible = bool(value)
        if self._text_visible:
            self.text_label.show()
        else:
            self.text_label.hide()

    @property
    def spacing(self) -> int:
        """Get or set spacing between icon and text.

        Returns:
            The current spacing in pixels.
        """
        return self._spacing

    @spacing.setter
    def spacing(self, value: int) -> None:
        """Set spacing between icon and text.

        Args:
            value: The new spacing in pixels.
        """
        self._spacing = int(value)
        layout = self.layout()
        if layout:
            layout.setSpacing(self._spacing)

    @property
    def min_width(self) -> int | None:
        """Get or set the minimum width of the button.

        Returns:
            The minimum width, or None if not set.
        """
        return self._min_width

    @min_width.setter
    def min_width(self, value: int | None) -> None:
        """Set the minimum width of the button.

        Args:
            value: The minimum width, or None to auto-calculate.
        """
        self._min_width = value
        self.updateGeometry()

    @property
    def min_height(self) -> int | None:
        """Get or set the minimum height of the button.

        Returns:
            The minimum height, or None if not set.
        """
        return self._min_height

    @min_height.setter
    def min_height(self, value: int | None) -> None:
        """Set the minimum height of the button.

        Args:
            value: The minimum height, or None to auto-calculate.
        """
        self._min_height = value
        self.updateGeometry()

    # ///////////////////////////////////////////////////////////////
    # PUBLIC METHODS
    # ///////////////////////////////////////////////////////////////

    def clear_icon(self) -> None:
        """Remove the current icon."""
        self._current_icon = None
        self.icon_label.clear()
        self.iconChanged.emit(QIcon())

    def clear_text(self) -> None:
        """Clear the button text."""
        self.text = ""

    def toggle_text_visibility(self) -> None:
        """Toggle text visibility."""
        self.text_visible = not self.text_visible

    def set_icon_color(self, color: str = "#FFFFFF", opacity: float = 0.5) -> None:
        """Apply color and opacity to the current icon.

        Args:
            color: The color to apply (default: "#FFFFFF").
            opacity: The opacity level (default: 0.5).
        """
        if self._current_icon:
            pixmap = self._current_icon.pixmap(self._icon_size)
            colored_pixmap = colorize_pixmap(pixmap, color, opacity)
            self.icon_label.setPixmap(colored_pixmap)

    # ///////////////////////////////////////////////////////////////
    # OVERRIDE METHODS
    # ///////////////////////////////////////////////////////////////

    def sizeHint(self) -> QSize:
        """Get the recommended size for the button.

        Returns:
            The recommended size.
        """
        return QSize(100, 40)

    def minimumSizeHint(self) -> QSize:
        """Get the minimum size hint for the button.

        Returns:
            The minimum size hint.
        """
        base_size = super().minimumSizeHint()

        icon_width = self._icon_size.width() if self._current_icon else 0

        text_width = 0
        if self._text_visible and self.text:
            text_width = self.text_label.fontMetrics().horizontalAdvance(self.text)

        total_width = icon_width + text_width + self._spacing + 20  # margins

        min_width = self._min_width if self._min_width is not None else total_width
        min_height = (
            self._min_height
            if self._min_height is not None
            else max(base_size.height(), self._icon_size.height() + 8)
        )

        return QSize(max(min_width, total_width), min_height)

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
