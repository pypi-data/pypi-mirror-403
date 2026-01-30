# ///////////////////////////////////////////////////////////////
# LOADER_BUTTON - Loading Button Widget
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Loader button widget module.

Provides a button widget with integrated loading animation for PySide6
applications.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
)
from typing_extensions import override

# ///////////////////////////////////////////////////////////////
# UTILITY FUNCTIONS
# ///////////////////////////////////////////////////////////////


def create_spinner_pixmap(size: int = 16, color: str = "#0078d4") -> QPixmap:
    """Create a spinner pixmap for loading animation.

    Args:
        size: Size of the spinner (default: 16).
        color: Color of the spinner (default: "#0078d4").

    Returns:
        Spinner pixmap.
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = QPen(QColor(color))
    pen.setWidth(2)
    painter.setPen(pen)

    center = size // 2
    radius = (size - 4) // 2

    # Draw 8 segments with different opacities
    for i in range(8):
        angle = i * 45
        painter.setOpacity(0.1 + (i * 0.1))
        painter.drawArc(
            center - radius,
            center - radius,
            radius * 2,
            radius * 2,
            angle * 16,
            30 * 16,
        )

    painter.end()
    return pixmap


def create_loading_icon(size: int = 16, color: str = "#0078d4") -> QIcon:
    """Create a loading icon with spinner.

    Args:
        size: Size of the icon (default: 16).
        color: Color of the icon (default: "#0078d4").

    Returns:
        Loading icon.
    """
    return QIcon(create_spinner_pixmap(size, color))


def create_success_icon(size: int = 16, color: str = "#28a745") -> QIcon:
    """Create a success icon (checkmark).

    Args:
        size: Size of the icon (default: 16).
        color: Color of the icon (default: "#28a745").

    Returns:
        Success icon.
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = QPen(QColor(color))
    pen.setWidth(2)
    painter.setPen(pen)

    margin = size // 4
    painter.drawLine(margin, size // 2, size // 3, size - margin)
    painter.drawLine(size // 3, size - margin, size - margin, margin)

    painter.end()
    return QIcon(pixmap)


def create_error_icon(size: int = 16, color: str = "#dc3545") -> QIcon:
    """Create an error icon (X mark).

    Args:
        size: Size of the icon (default: 16).
        color: Color of the icon (default: "#dc3545").

    Returns:
        Error icon.
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = QPen(QColor(color))
    pen.setWidth(2)
    painter.setPen(pen)

    margin = size // 4
    painter.drawLine(margin, margin, size - margin, size - margin)
    painter.drawLine(size - margin, margin, margin, size - margin)

    painter.end()
    return QIcon(pixmap)


# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class LoaderButton(QToolButton):
    """Button widget with integrated loading animation.

    Features:
        - Loading state with animated spinner
        - Success state with checkmark icon
        - Error state with X icon
        - Configurable loading, success, and error text/icons
        - Smooth transitions between states
        - Disabled state during loading
        - Customizable animation speed
        - Progress indication support
        - Auto-reset after completion with configurable display times

    Args:
        parent: The parent widget (default: None).
        text: Button text (default: "").
        icon: Button icon (default: None).
        loading_text: Text to display during loading (default: "Loading...").
        loading_icon: Icon to display during loading
            (default: None, auto-generated).
        success_icon: Icon to display on success
            (default: None, auto-generated checkmark).
        error_icon: Icon to display on error
            (default: None, auto-generated X mark).
        animation_speed: Animation speed in milliseconds (default: 100).
        auto_reset: Whether to auto-reset after loading (default: True).
        success_display_time: Time to display success state in milliseconds
            (default: 1000).
        error_display_time: Time to display error state in milliseconds
            (default: 2000).
        min_width: Minimum width of the button (default: None, auto-calculated).
        min_height: Minimum height of the button (default: None, auto-calculated).
        *args: Additional arguments passed to QToolButton.
        **kwargs: Additional keyword arguments passed to QToolButton.

    Signals:
        loadingStarted(): Emitted when loading starts.
        loadingFinished(): Emitted when loading finishes successfully.
        loadingFailed(str): Emitted when loading fails with error message.
    """

    loadingStarted = Signal()
    loadingFinished = Signal()
    loadingFailed = Signal(str)

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        parent=None,
        text: str = "",
        icon: QIcon | str | None = None,
        loading_text: str = "Loading...",
        loading_icon: QIcon | str | None = None,
        success_icon: QIcon | str | None = None,
        error_icon: QIcon | str | None = None,
        animation_speed: int = 100,
        auto_reset: bool = True,
        success_display_time: int = 1000,
        error_display_time: int = 2000,
        min_width: int | None = None,
        min_height: int | None = None,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the loader button."""
        super().__init__(parent, *args, **kwargs)
        self.setProperty("type", "LoaderButton")

        # Initialize properties
        self._original_text = text
        self._original_icon: QIcon | None = None
        self._loading_text = loading_text
        self._loading_icon: QIcon | None = None
        self._success_icon: QIcon | None = None
        self._error_icon: QIcon | None = None
        self._is_loading = False
        self._animation_speed = animation_speed
        self._auto_reset = auto_reset
        self._success_display_time = success_display_time
        self._error_display_time = error_display_time
        self._min_width = min_width
        self._min_height = min_height
        self._animation_group = None
        self._spinner_animation = None

        # Setup UI components
        self.text_label = QLabel()
        self.icon_label = QLabel()

        # Configure labels
        self.text_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self.text_label.setStyleSheet("background-color: transparent;")

        # Setup layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(8)
        layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)

        # Configure size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Set initial values
        if icon:
            self.icon = icon
        if text:
            self.text = text

        # Setup icons
        if loading_icon:
            self.loading_icon = loading_icon
        else:
            self.loading_icon = create_loading_icon(16, "#0078d4")

        if success_icon:
            self.success_icon = success_icon
        else:
            self.success_icon = create_success_icon(16, "#28a745")

        if error_icon:
            self.error_icon = error_icon
        else:
            self.error_icon = create_error_icon(16, "#dc3545")

        # Setup animations
        self._setup_animations()

        # Initial display
        self._update_display()

    # ///////////////////////////////////////////////////////////////
    # PROPERTIES
    # ///////////////////////////////////////////////////////////////

    @property
    @override
    def text(
        self,
    ) -> str:
        """Get or set the button text.

        Returns:
            The current button text.
        """
        return self._original_text

    @text.setter
    def text(self, value: str) -> None:
        """Set the button text.

        Args:
            value: The new button text.
        """
        self._original_text = str(value)
        if not self._is_loading:
            self._update_display()

    @property
    @override
    def icon(
        self,
    ) -> QIcon | None:
        """Get or set the button icon.

        Returns:
            The current button icon, or None if no icon is set.
        """
        return self._original_icon

    @icon.setter
    def icon(self, value: QIcon | str | None) -> None:
        """Set the button icon.

        Args:
            value: The icon source (QIcon, path, or URL).
        """
        if isinstance(value, str):
            self._original_icon = QIcon(value)
        else:
            self._original_icon = value
        if not self._is_loading:
            self._update_display()

    @property
    def loading_text(self) -> str:
        """Get or set the loading text.

        Returns:
            The current loading text.
        """
        return self._loading_text

    @loading_text.setter
    def loading_text(self, value: str) -> None:
        """Set the loading text.

        Args:
            value: The new loading text.
        """
        self._loading_text = str(value)
        if self._is_loading:
            self._update_display()

    @property
    def loading_icon(self) -> QIcon | None:
        """Get or set the loading icon.

        Returns:
            The current loading icon, or None if not set.
        """
        return self._loading_icon

    @loading_icon.setter
    def loading_icon(self, value: QIcon | str | None) -> None:
        """Set the loading icon.

        Args:
            value: The icon source (QIcon, path, or URL).
        """
        if isinstance(value, str):
            self._loading_icon = QIcon(value)
        else:
            self._loading_icon = value

    @property
    def success_icon(self) -> QIcon | None:
        """Get or set the success icon.

        Returns:
            The current success icon, or None if not set.
        """
        return self._success_icon

    @success_icon.setter
    def success_icon(self, value: QIcon | str | None) -> None:
        """Set the success icon.

        Args:
            value: The icon source (QIcon, path, or URL).
        """
        if isinstance(value, str):
            self._success_icon = QIcon(value)
        else:
            self._success_icon = value

    @property
    def error_icon(self) -> QIcon | None:
        """Get or set the error icon.

        Returns:
            The current error icon, or None if not set.
        """
        return self._error_icon

    @error_icon.setter
    def error_icon(self, value: QIcon | str | None) -> None:
        """Set the error icon.

        Args:
            value: The icon source (QIcon, path, or URL).
        """
        if isinstance(value, str):
            self._error_icon = QIcon(value)
        else:
            self._error_icon = value

    @property
    def success_display_time(self) -> int:
        """Get or set the success display time.

        Returns:
            The success display time in milliseconds.
        """
        return self._success_display_time

    @success_display_time.setter
    def success_display_time(self, value: int) -> None:
        """Set the success display time.

        Args:
            value: The display time in milliseconds.
        """
        self._success_display_time = int(value)

    @property
    def error_display_time(self) -> int:
        """Get or set the error display time.

        Returns:
            The error display time in milliseconds.
        """
        return self._error_display_time

    @error_display_time.setter
    def error_display_time(self, value: int) -> None:
        """Set the error display time.

        Args:
            value: The display time in milliseconds.
        """
        self._error_display_time = int(value)

    @property
    def is_loading(self) -> bool:
        """Get the current loading state.

        Returns:
            True if loading, False otherwise.
        """
        return self._is_loading

    @property
    def animation_speed(self) -> int:
        """Get or set the animation speed.

        Returns:
            The animation speed in milliseconds.
        """
        return self._animation_speed

    @animation_speed.setter
    def animation_speed(self, value: int) -> None:
        """Set the animation speed.

        Args:
            value: The animation speed in milliseconds.
        """
        self._animation_speed = int(value)
        if self._spinner_animation:
            self._spinner_animation.setDuration(self._animation_speed)

    @property
    def auto_reset(self) -> bool:
        """Get or set auto-reset behavior.

        Returns:
            True if auto-reset is enabled, False otherwise.
        """
        return self._auto_reset

    @auto_reset.setter
    def auto_reset(self, value: bool) -> None:
        """Set auto-reset behavior.

        Args:
            value: Whether to auto-reset after loading completes.
        """
        self._auto_reset = bool(value)

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

    def start_loading(self) -> None:
        """Start the loading animation."""
        if self._is_loading:
            return

        self._is_loading = True
        self.setEnabled(False)
        self._update_display()

        # Start spinner animation using timer
        self._rotation_angle = 0
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._rotate_spinner)
        self._animation_timer.start(self._animation_speed // 10)

        self.loadingStarted.emit()

    def stop_loading(self, success: bool = True, error_message: str = "") -> None:
        """Stop the loading animation.

        Args:
            success: Whether the operation succeeded (default: True).
            error_message: Error message if operation failed (default: "").
        """
        if not self._is_loading:
            return

        self._is_loading = False

        # Stop spinner animation
        if hasattr(self, "_animation_timer"):
            self._animation_timer.stop()
            self._animation_timer.deleteLater()

        # Show result state
        if success:
            self._show_success_state()
        else:
            self._show_error_state(error_message)

        # Enable button
        self.setEnabled(True)

        if success:
            self.loadingFinished.emit()
        else:
            self.loadingFailed.emit(error_message)

        # Auto-reset if enabled
        if self._auto_reset:
            display_time = (
                self._success_display_time if success else self._error_display_time
            )
            QTimer.singleShot(display_time, self._reset_to_original)

    # ------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------

    def _show_success_state(self) -> None:
        """Show success state with success icon."""
        self.text_label.setText("Success!")
        if self._success_icon:
            self.icon_label.setPixmap(self._success_icon.pixmap(16, 16))
            self.icon_label.show()
        else:
            self.icon_label.hide()

    def _show_error_state(self, error_message: str = "") -> None:
        """Show error state with error icon.

        Args:
            error_message: Optional error message to display.
        """
        if error_message:
            self.text_label.setText(f"Error: {error_message}")
        else:
            self.text_label.setText("Error")

        if self._error_icon:
            self.icon_label.setPixmap(self._error_icon.pixmap(16, 16))
            self.icon_label.show()
        else:
            self.icon_label.hide()

    def _reset_to_original(self) -> None:
        """Reset to original state after auto-reset delay."""
        self._update_display()

    def _setup_animations(self) -> None:
        """Setup the spinner rotation animation."""
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)

        self._rotation_angle = 0

    def _rotate_spinner(self) -> None:
        """Rotate the spinner icon."""
        if not self._is_loading:
            return

        self._rotation_angle = (self._rotation_angle + 10) % 360

        if self._loading_icon:
            pixmap = self._loading_icon.pixmap(16, 16)
            if pixmap:
                rotated_pixmap = QPixmap(pixmap.size())
                rotated_pixmap.fill(Qt.GlobalColor.transparent)

                painter = QPainter(rotated_pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)

                painter.translate(pixmap.width() / 2, pixmap.height() / 2)
                painter.rotate(self._rotation_angle)
                painter.translate(-pixmap.width() / 2, -pixmap.height() / 2)

                painter.drawPixmap(0, 0, pixmap)
                painter.end()

                self.icon_label.setPixmap(rotated_pixmap)

    def _update_display(self) -> None:
        """Update the display based on current state."""
        if self._is_loading:
            self.text_label.setText(self._loading_text)
            if self._loading_icon:
                self.icon_label.setPixmap(self._loading_icon.pixmap(16, 16))
                self.icon_label.show()
            else:
                self.icon_label.hide()
        else:
            self.text_label.setText(self._original_text)
            if self._original_icon:
                self.icon_label.setPixmap(self._original_icon.pixmap(16, 16))
                self.icon_label.show()
            else:
                self.icon_label.hide()

    # ///////////////////////////////////////////////////////////////
    # EVENT HANDLERS
    # ///////////////////////////////////////////////////////////////

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events.

        Args:
            event: The mouse event.
        """
        if not self._is_loading and event.button() == Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)

    # ///////////////////////////////////////////////////////////////
    # OVERRIDE METHODS
    # ///////////////////////////////////////////////////////////////

    def sizeHint(self) -> QSize:
        """Get the recommended size for the button.

        Returns:
            The recommended size.
        """
        return QSize(120, 30)

    def minimumSizeHint(self) -> QSize:
        """Get the minimum size hint for the button.

        Returns:
            The minimum size hint.
        """
        base_size = super().minimumSizeHint()

        text_width = self.text_label.fontMetrics().horizontalAdvance(
            self._loading_text if self._is_loading else self._original_text
        )

        icon_width = 16 if (self._loading_icon or self._original_icon) else 0

        total_width = text_width + icon_width + 16 + 8  # margins + spacing

        min_width = self._min_width if self._min_width is not None else total_width
        min_height = (
            self._min_height
            if self._min_height is not None
            else max(base_size.height(), 30)
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
