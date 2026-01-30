# ///////////////////////////////////////////////////////////////
# PASSWORD_INPUT - Password Input Widget
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Password input widget module.

Provides an enhanced password input widget with integrated strength bar
and right-side icon for PySide6 applications.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import re

# Third-party imports
import requests
from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QMouseEvent, QPainter, QPaintEvent, QPixmap
from PySide6.QtWidgets import QLineEdit, QProgressBar, QVBoxLayout, QWidget

# ///////////////////////////////////////////////////////////////
# UTILITY FUNCTIONS
# ///////////////////////////////////////////////////////////////


def password_strength(password: str) -> int:
    """Calculate password strength score.

    Returns a strength score from 0 (weak) to 100 (strong) based on
    various criteria like length, character variety, etc.

    Args:
        password: The password to evaluate.

    Returns:
        Strength score from 0 to 100.
    """
    score = 0
    if len(password) >= 8:
        score += 25
    if re.search(r"[A-Z]", password):
        score += 15
    if re.search(r"[a-z]", password):
        score += 15
    if re.search(r"\d", password):
        score += 20
    if re.search(r"[^A-Za-z0-9]", password):
        score += 25
    return min(score, 100)


def get_strength_color(score: int) -> str:
    """Get color based on password strength score.

    Args:
        score: The password strength score (0-100).

    Returns:
        Hex color code for the strength level.
    """
    if score < 30:
        return "#ff4444"  # Red
    elif score < 60:
        return "#ffaa00"  # Orange
    elif score < 80:
        return "#44aa44"  # Green
    else:
        return "#00aa00"  # Dark green


def colorize_pixmap(
    pixmap: QPixmap, color: str = "#FFFFFF", opacity: float = 0.5
) -> QPixmap:
    """Recolor a QPixmap with the given color and opacity.

    Args:
        pixmap: The pixmap to recolor.
        color: Hex color code (default: "#FFFFFF").
        opacity: Opacity value from 0.0 to 1.0 (default: 0.5).

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
                    pixmap.loadFromData(image_data)
                    return QIcon(pixmap)

            except Exception as e:
                print(f"Failed to load icon from URL {source}: {e}")
                return None

        # Handle local SVG
        elif source.lower().endswith(".svg"):
            from PySide6.QtSvg import QSvgRenderer

            renderer = QSvgRenderer(source)
            if renderer.isValid():
                pixmap = QPixmap(QSize(16, 16))
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                return QIcon(pixmap)
            else:
                print(f"Invalid SVG file: {source}")
                return None

        # Handle local image
        else:
            pixmap = QPixmap(source)
            if not pixmap.isNull():
                return QIcon(pixmap)
            else:
                print(f"Failed to load image: {source}")
                return None


# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class PasswordInput(QWidget):
    """Enhanced password input widget with integrated strength bar.

    Features:
        - QLineEdit in password mode with integrated strength bar
        - Right-side icon with click functionality
        - Icon management system (QIcon, path, URL, SVG)
        - Animated strength bar that fills the bottom border
        - Signal strengthChanged(int) emitted on password change
        - Color-coded strength indicator
        - External QSS styling support with CSS variables

    Args:
        parent: The parent widget (default: None).
        show_strength: Whether to show the password strength bar
            (default: True).
        strength_bar_height: Height of the strength bar in pixels
            (default: 3).
        show_icon: Icon for show password (QIcon, str, or None,
            default: URL to icons8.com).
        hide_icon: Icon for hide password (QIcon, str, or None,
            default: URL to icons8.com).
        icon_size: Size of the icon (QSize or tuple, default: QSize(16, 16)).
        *args: Additional arguments passed to QWidget.
        **kwargs: Additional keyword arguments passed to QWidget.

    Properties:
        password: Get or set the password text.
        show_strength: Get or set whether to show the strength bar.
        strength_bar_height: Get or set the strength bar height.
        show_icon: Get or set the show password icon.
        hide_icon: Get or set the hide password icon.
        icon_size: Get or set the icon size.

    Signals:
        strengthChanged(int): Emitted when password strength changes.
        iconClicked(): Emitted when the icon is clicked.
    """

    strengthChanged = Signal(int)
    iconClicked = Signal()

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        parent=None,
        show_strength: bool = True,
        strength_bar_height: int = 3,
        show_icon: (
            QIcon | str | None
        ) = "https://img.icons8.com/?size=100&id=85130&format=png&color=000000",
        hide_icon: (
            QIcon | str | None
        ) = "https://img.icons8.com/?size=100&id=85137&format=png&color=000000",
        icon_size: QSize | tuple[int, int] = QSize(16, 16),
        *args,
        **kwargs,
    ) -> None:
        """Initialize the password input widget."""
        super().__init__(parent, *args, **kwargs)

        # Set widget type for QSS selection
        self.setProperty("type", "PasswordInput")
        self.setObjectName("PasswordInput")

        # Initialize properties
        self._show_strength: bool = show_strength
        self._strength_bar_height: int = strength_bar_height
        self._show_icon: QIcon | None = None
        self._hide_icon: QIcon | None = None
        self._show_icon_source: QIcon | str | None = show_icon
        self._hide_icon_source: QIcon | str | None = hide_icon
        self._icon_size: QSize = (
            QSize(*icon_size) if isinstance(icon_size, (tuple, list)) else icon_size
        )
        self._current_strength: int = 0
        self._password_visible: bool = False

        # Setup UI
        self._setup_ui()

        # Set icons
        if show_icon:
            self.show_icon = show_icon  # type: ignore[assignment]
        if hide_icon:
            self.hide_icon = hide_icon  # type: ignore[assignment]

        # Initialize icon display
        self._update_icon()

    # ------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------

    def _setup_ui(self) -> None:
        """Setup the user interface components."""
        # Create layout
        self._layout = QVBoxLayout(self)

        # Set content margins to show borders
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._layout.setSpacing(0)

        # Create password input
        self._password_input = PasswordLineEdit()
        self._password_input.textChanged.connect(self.update_strength)

        # Connect icon click signal
        self._password_input.iconClicked.connect(self.toggle_password)

        # Create strength bar
        self._strength_bar = QProgressBar()
        self._strength_bar.setProperty("type", "PasswordStrengthBar")
        self._strength_bar.setFixedHeight(self._strength_bar_height)
        self._strength_bar.setRange(0, 100)
        self._strength_bar.setValue(0)
        self._strength_bar.setTextVisible(False)
        self._strength_bar.setVisible(self._show_strength)

        # Add widgets to layout
        self._layout.addWidget(self._password_input)
        self._layout.addWidget(self._strength_bar)

    def _update_icon(self) -> None:
        """Update the icon based on password visibility."""
        if self._password_visible and self._hide_icon:
            self._password_input.set_right_icon(self._hide_icon, self._icon_size)
        elif not self._password_visible and self._show_icon:
            self._password_input.set_right_icon(self._show_icon, self._icon_size)
        # Handle case where icons are not yet loaded
        elif not self._password_visible and self._show_icon_source:
            # Try to load icon from source if not already loaded
            icon = load_icon_from_source(self._show_icon_source)
            if icon:
                self._show_icon = icon
                self._password_input.set_right_icon(icon, self._icon_size)

    def _update_strength_color(self, score: int) -> None:
        """Update strength bar color based on score.

        Args:
            score: The password strength score (0-100).
        """
        color = get_strength_color(score)
        self._strength_bar.setStyleSheet(
            f"""
            QProgressBar {{
                border: none;
                background-color: #2d2d2d;
            }}
            QProgressBar::chunk {{
                background-color: {color};
            }}
            """
        )

    # ///////////////////////////////////////////////////////////////
    # PUBLIC METHODS
    # ///////////////////////////////////////////////////////////////

    def toggle_password(self) -> None:
        """Toggle password visibility."""
        self._password_visible = not self._password_visible
        if self._password_visible:
            self._password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._update_icon()

    def update_strength(self, text: str) -> None:
        """Update password strength.

        Args:
            text: The password text to evaluate.
        """
        score = password_strength(text)
        self._current_strength = score
        self._strength_bar.setValue(score)
        self._update_strength_color(score)
        self.strengthChanged.emit(score)

    # ///////////////////////////////////////////////////////////////
    # PROPERTIES
    # ///////////////////////////////////////////////////////////////

    @property
    def password(self) -> str:
        """Get the password text.

        Returns:
            The current password text.
        """
        return self._password_input.text()

    @password.setter
    def password(self, value: str) -> None:
        """Set the password text.

        Args:
            value: The new password text.
        """
        self._password_input.setText(str(value))

    @property
    def show_strength(self) -> bool:
        """Get whether the strength bar is shown.

        Returns:
            True if strength bar is shown, False otherwise.
        """
        return self._show_strength

    @show_strength.setter
    def show_strength(self, value: bool) -> None:
        """Set whether the strength bar is shown.

        Args:
            value: Whether to show the strength bar.
        """
        self._show_strength = bool(value)
        self._strength_bar.setVisible(self._show_strength)

    @property
    def strength_bar_height(self) -> int:
        """Get the strength bar height.

        Returns:
            The current strength bar height in pixels.
        """
        return self._strength_bar_height

    @strength_bar_height.setter
    def strength_bar_height(self, value: int) -> None:
        """Set the strength bar height.

        Args:
            value: The new strength bar height in pixels.
        """
        self._strength_bar_height = max(1, int(value))
        self._strength_bar.setFixedHeight(self._strength_bar_height)

    @property
    def show_icon(self) -> QIcon | None:
        """Get the show password icon.

        Returns:
            The current show password icon, or None if not set.
        """
        return self._show_icon

    @show_icon.setter
    def show_icon(self, value: QIcon | str | None) -> None:
        """Set the show password icon.

        Args:
            value: The icon source (QIcon, path string, URL, or None).
        """
        self._show_icon_source = value
        self._show_icon = load_icon_from_source(value)
        if not self._password_visible:
            self._update_icon()

    @property
    def hide_icon(self) -> QIcon | None:
        """Get the hide password icon.

        Returns:
            The current hide password icon, or None if not set.
        """
        return self._hide_icon

    @hide_icon.setter
    def hide_icon(self, value: QIcon | str | None) -> None:
        """Set the hide password icon.

        Args:
            value: The icon source (QIcon, path string, URL, or None).
        """
        self._hide_icon_source = value
        self._hide_icon = load_icon_from_source(value)
        if self._password_visible:
            self._update_icon()

    @property
    def icon_size(self) -> QSize:
        """Get the icon size.

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
        self._icon_size = QSize(*value) if isinstance(value, (tuple, list)) else value
        self._update_icon()

    # ///////////////////////////////////////////////////////////////
    # STYLE METHODS
    # ///////////////////////////////////////////////////////////////

    def refresh_style(self) -> None:
        """Refresh the widget style.

        Deprecated - use external QSS for styling.
        """
        self.update()


class PasswordLineEdit(QLineEdit):
    """QLineEdit subclass with right-side icon support.

    Features:
        - Right-side icon with click functionality
        - Icon management system
        - Signal iconClicked emitted when icon is clicked

    Args:
        parent: The parent widget (default: None).
    """

    iconClicked = Signal()

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(self, parent=None) -> None:
        """Initialize the password line edit."""
        super().__init__(parent)

        # Set widget type for QSS selection
        self.setProperty("type", "PasswordInputField")
        self.setEchoMode(QLineEdit.EchoMode.Password)
        self._right_icon: QIcon | None = None
        self._icon_rect: QRect | None = None

    # ///////////////////////////////////////////////////////////////
    # PUBLIC METHODS
    # ///////////////////////////////////////////////////////////////

    def set_right_icon(self, icon: QIcon | None, size: QSize | None = None) -> None:
        """Set the right-side icon.

        Args:
            icon: The icon to display (QIcon or None).
            size: The icon size (QSize or None for default).
        """
        self._right_icon = icon
        if size:
            self._icon_size = size
        else:
            self._icon_size = QSize(16, 16)
        self.update()

    # ///////////////////////////////////////////////////////////////
    # EVENT HANDLERS
    # ///////////////////////////////////////////////////////////////

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events for icon clicking.

        Args:
            event: The mouse event.
        """
        if (
            self._right_icon
            and self._icon_rect
            and self._icon_rect.contains(event.pos())
        ):
            self.iconClicked.emit()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move events for cursor changes.

        Args:
            event: The mouse event.
        """
        if (
            self._right_icon
            and self._icon_rect
            and self._icon_rect.contains(event.pos())
        ):
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.IBeamCursor)
            super().mouseMoveEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Custom paint event to draw the right-side icon.

        Args:
            event: The paint event.
        """
        super().paintEvent(event)

        if not self._right_icon:
            return

        # Calculate icon position
        icon_x = self.width() - self._icon_size.width() - 8
        icon_y = (self.height() - self._icon_size.height()) // 2

        self._icon_rect = QRect(
            icon_x, icon_y, self._icon_size.width(), self._icon_size.height()
        )

        # Draw icon
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.drawPixmap(self._icon_rect, self._right_icon.pixmap(self._icon_size))

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
