# ///////////////////////////////////////////////////////////////
# TOGGLE_SWITCH - Toggle Switch Widget
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Toggle switch widget module.

Provides a modern toggle switch widget with animated sliding circle for
PySide6 applications.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    QRect,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QBrush, QColor, QMouseEvent, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class ToggleSwitch(QWidget):
    """Modern toggle switch widget with animated sliding circle.

    Features:
        - Smooth animation when toggling
        - Customizable colors for on/off states
        - Configurable size and border radius
        - Click to toggle functionality
        - Property-based access to state
        - Signal emitted on state change

    Args:
        parent: The parent widget (default: None).
        checked: Initial state of the toggle (default: False).
        width: Width of the toggle switch (default: 50).
        height: Height of the toggle switch (default: 24).
        animation: Whether to animate the toggle (default: True).
        *args: Additional arguments passed to QWidget.
        **kwargs: Additional keyword arguments passed to QWidget.

    Signals:
        toggled(bool): Emitted when the toggle state changes.
    """

    toggled = Signal(bool)

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        parent=None,
        checked: bool = False,
        width: int = 50,
        height: int = 24,
        animation: bool = True,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the toggle switch."""
        super().__init__(parent, *args, **kwargs)

        # Initialize properties
        self._checked: bool = checked
        self._width: int = width
        self._height: int = height
        self._animation: bool = animation
        self._circle_radius: int = (height - 4) // 2  # Circle radius with 2px margin
        self._animation_duration: int = 200

        # Colors
        self._bg_color_off: QColor = QColor(44, 49, 58)  # Default dark theme
        self._bg_color_on: QColor = QColor(150, 205, 50)  # Default accent color
        self._circle_color: QColor = QColor(255, 255, 255)
        self._border_color: QColor = QColor(52, 59, 72)

        # Initialize position
        self._circle_position: int = self._get_circle_position()

        # Setup animation
        self._setup_animation()

        # Setup widget
        self._setup_widget()

    # ------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------

    def _setup_animation(self) -> None:
        """Setup the animation system."""
        self._animation_obj = QPropertyAnimation(self, b"circle_position")
        self._animation_obj.setDuration(self._animation_duration)
        self._animation_obj.setEasingCurve(QEasingCurve.Type.InOutQuart)

    def _setup_widget(self) -> None:
        """Setup the widget properties."""
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(self._width, self._height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _get_circle_position(self) -> int:
        """Calculate circle position based on state.

        Returns:
            The circle position in pixels.
        """
        if self._checked:
            return self._width - self._height + 2  # Right position
        else:
            return 2  # Left position

    def _get_circle_position_property(self) -> int:
        """Property getter for animation.

        Returns:
            The current circle position.
        """
        return self._circle_position

    def _set_circle_position_property(self, position: int) -> None:
        """Property setter for animation.

        Args:
            position: The new circle position.
        """
        self._circle_position = position
        self.update()

    # Property for animation
    circle_position = Property(
        int, _get_circle_position_property, _set_circle_position_property
    )

    # ///////////////////////////////////////////////////////////////
    # PROPERTIES
    # ///////////////////////////////////////////////////////////////

    @property
    def checked(self) -> bool:
        """Get the toggle state.

        Returns:
            True if checked, False otherwise.
        """
        return self._checked

    @checked.setter
    def checked(self, value: bool) -> None:
        """Set the toggle state.

        Args:
            value: The new toggle state.
        """
        if value != self._checked:
            self._checked = bool(value)
            if self._animation:
                self._animate_circle()
            else:
                self._circle_position = self._get_circle_position()
                self.update()
            self.toggled.emit(self._checked)

    @property
    def width(self) -> int:
        """Get the width of the toggle.

        Returns:
            The current width in pixels.
        """
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        """Set the width of the toggle.

        Args:
            value: The new width in pixels.
        """
        self._width = max(20, int(value))
        self._circle_radius = (self._height - 4) // 2
        self.setFixedSize(self._width, self._height)
        self._circle_position = self._get_circle_position()
        self.update()

    @property
    def height(self) -> int:
        """Get the height of the toggle.

        Returns:
            The current height in pixels.
        """
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        """Set the height of the toggle.

        Args:
            value: The new height in pixels.
        """
        self._height = max(12, int(value))
        self._circle_radius = (self._height - 4) // 2
        self.setFixedSize(self._width, self._height)
        self._circle_position = self._get_circle_position()
        self.update()

    @property
    def animation(self) -> bool:
        """Get whether animation is enabled.

        Returns:
            True if animation is enabled, False otherwise.
        """
        return self._animation

    @animation.setter
    def animation(self, value: bool) -> None:
        """Set whether animation is enabled.

        Args:
            value: Whether to enable animation.
        """
        self._animation = bool(value)

    # ///////////////////////////////////////////////////////////////
    # PUBLIC METHODS
    # ///////////////////////////////////////////////////////////////

    def toggle(self) -> None:
        """Toggle the switch state."""
        self.checked = not self._checked

    # ------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------

    def _animate_circle(self) -> None:
        """Animate the circle movement."""
        target_position = self._get_circle_position()
        self._animation_obj.setStartValue(self._circle_position)
        self._animation_obj.setEndValue(target_position)
        self._animation_obj.start()

    # ///////////////////////////////////////////////////////////////
    # EVENT HANDLERS
    # ///////////////////////////////////////////////////////////////

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events.

        Args:
            event: The mouse event.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()

    def paintEvent(self, _event: QPaintEvent) -> None:
        """Custom paint event to draw the toggle switch.

        Args:
            _event: The paint event (unused but required by signature).
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background
        bg_color = self._bg_color_on if self._checked else self._bg_color_off
        painter.setPen(QPen(self._border_color, 1))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(
            0,
            0,
            self._width,
            self._height,
            self._height // 2,
            self._height // 2,
        )

        # Draw circle
        circle_x = self._circle_position
        circle_y = (self._height - self._circle_radius * 2) // 2
        circle_rect = QRect(
            circle_x, circle_y, self._circle_radius * 2, self._circle_radius * 2
        )

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self._circle_color))
        painter.drawEllipse(
            circle_x, circle_y, circle_rect.width(), circle_rect.height()
        )

    # ///////////////////////////////////////////////////////////////
    # OVERRIDE METHODS
    # ///////////////////////////////////////////////////////////////

    def sizeHint(self) -> QSize:
        """Return the recommended size for the widget.

        Returns:
            The recommended size.
        """
        return QSize(self._width, self._height)

    def minimumSizeHint(self) -> QSize:
        """Return the minimum size for the widget.

        Returns:
            The minimum size hint.
        """
        return QSize(self._width, self._height)

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
