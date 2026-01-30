# ///////////////////////////////////////////////////////////////
# CIRCULAR_TIMER - Circular Timer Widget
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Circular timer widget module.

Provides an animated circular timer widget for indicating progress or
elapsed time in PySide6 applications.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import re
from typing import Literal

# Third-party imports
from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

# ///////////////////////////////////////////////////////////////
# UTILITY FUNCTIONS
# ///////////////////////////////////////////////////////////////


def parse_css_color(color_str: QColor | str) -> QColor:
    """Parse CSS color strings to QColor.

    Supports rgb, rgba, hex, and named colors.

    Args:
        color_str: CSS color string or QColor object.

    Returns:
        QColor object.
    """
    if isinstance(color_str, QColor):
        return color_str

    color_str = str(color_str).strip()

    # Parse rgb(r, g, b)
    rgb_match = re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", color_str)
    if rgb_match:
        r, g, b = map(int, rgb_match.groups())
        return QColor(r, g, b)

    # Parse rgba(r, g, b, a)
    rgba_match = re.match(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)", color_str)
    if rgba_match:
        r_str, g_str, b_str, a_str = rgba_match.groups()
        r, g, b = int(r_str), int(g_str), int(b_str)
        a = float(a_str) * 255  # Convert 0-1 to 0-255
        return QColor(r, g, b, int(a))

    # Fallback to QColor constructor (hex, named colors, etc.)
    return QColor(color_str)


# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class CircularTimer(QWidget):
    """Animated circular timer for indicating progress or elapsed time.

    Features:
        - Animated circular progress indicator
        - Customizable colors for ring and center
        - Configurable duration and loop mode
        - Click events for interaction
        - Smooth animation with configurable frame rate

    Args:
        parent: Parent widget (default: None).
        duration: Total animation duration in milliseconds (default: 5000).
        ring_color: Color of the progress arc (default: "#0078d4").
            Supports: hex (#ff0000), rgb(255,0,0), rgba(255,0,0,0.5), names (red).
        node_color: Color of the center (default: "#2d2d2d").
            Supports: hex (#ffffff), rgb(255,255,255), rgba(255,255,255,0.8), names (white).
        ring_width_mode: "small", "medium" (default), or "large".
            Controls the dynamic thickness of the arc.
        pen_width: Thickness of the arc (takes priority over ring_width_mode if set).
        loop: If True, the timer loops automatically at each cycle (default: False).
        *args: Additional arguments passed to QWidget.
        **kwargs: Additional keyword arguments passed to QWidget.

    Signals:
        timerReset(): Emitted when the timer is reset.
        clicked(): Emitted when the widget is clicked.
        cycleCompleted(): Emitted at each end of cycle (even if loop=False).
    """

    timerReset = Signal()
    clicked = Signal()
    cycleCompleted = Signal()

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        parent=None,
        duration: int = 5000,
        ring_color: QColor | str = "#0078d4",
        node_color: QColor | str = "#2d2d2d",
        ring_width_mode: Literal["small", "medium", "large"] = "medium",
        pen_width: int | float | None = None,
        loop: bool = False,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the circular timer."""
        super().__init__(parent, *args, **kwargs)
        self.setProperty("type", "CircularTimer")

        # Initialize properties
        self._duration: int = duration
        self._elapsed: int = 0
        self._running: bool = False
        self._ring_color: QColor = parse_css_color(ring_color)
        self._node_color: QColor = parse_css_color(node_color)
        self._ring_width_mode: str = ring_width_mode
        self._pen_width: float | None = pen_width
        self._loop: bool = bool(loop)
        self._last_update: float | None = None
        self._interval: int = 16  # ~60 FPS

        # Setup timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer)

    # ///////////////////////////////////////////////////////////////
    # PROPERTIES
    # ///////////////////////////////////////////////////////////////

    @property
    def duration(self) -> int:
        """Get the total duration.

        Returns:
            The total duration in milliseconds.
        """
        return self._duration

    @duration.setter
    def duration(self, value: int) -> None:
        """Set the total duration.

        Args:
            value: The new duration in milliseconds.
        """
        self._duration = int(value)
        self.update()

    @property
    def elapsed(self) -> int:
        """Get the elapsed time.

        Returns:
            The elapsed time in milliseconds.
        """
        return self._elapsed

    @elapsed.setter
    def elapsed(self, value: int) -> None:
        """Set the elapsed time.

        Args:
            value: The new elapsed time in milliseconds.
        """
        self._elapsed = int(value)
        self.update()

    @property
    def running(self) -> bool:
        """Get whether the timer is running.

        Returns:
            True if running, False otherwise.
        """
        return self._running

    @property
    def ring_color(self) -> QColor:
        """Get the ring color.

        Returns:
            The current ring color.
        """
        return self._ring_color

    @ring_color.setter
    def ring_color(self, value: QColor | str) -> None:
        """Set the ring color.

        Args:
            value: The new ring color (QColor or CSS string).
        """
        self._ring_color = parse_css_color(value)
        self.update()

    @property
    def node_color(self) -> QColor:
        """Get the node color.

        Returns:
            The current node color.
        """
        return self._node_color

    @node_color.setter
    def node_color(self, value: QColor | str) -> None:
        """Set the node color.

        Args:
            value: The new node color (QColor or CSS string).
        """
        self._node_color = parse_css_color(value)
        self.update()

    @property
    def ring_width_mode(self) -> str:
        """Get the ring width mode.

        Returns:
            The current ring width mode ("small", "medium", or "large").
        """
        return self._ring_width_mode

    @ring_width_mode.setter
    def ring_width_mode(self, value: str) -> None:
        """Set the ring width mode.

        Args:
            value: The new ring width mode ("small", "medium", or "large").
        """
        if value not in ("small", "medium", "large"):
            value = "medium"
        self._ring_width_mode = value
        self.update()

    @property
    def pen_width(self) -> float | None:
        """Get the pen width.

        Returns:
            The pen width, or None if using ring_width_mode.
        """
        return self._pen_width

    @pen_width.setter
    def pen_width(self, value: int | float | None) -> None:
        """Set the pen width.

        Args:
            value: The new pen width, or None to use ring_width_mode.
        """
        self._pen_width = float(value) if value is not None else None
        self.update()

    @property
    def loop(self) -> bool:
        """Get whether the timer loops.

        Returns:
            True if looping, False otherwise.
        """
        return self._loop

    @loop.setter
    def loop(self, value: bool) -> None:
        """Set whether the timer loops.

        Args:
            value: Whether to loop the timer.
        """
        self._loop = bool(value)

    # ///////////////////////////////////////////////////////////////
    # EVENT HANDLERS
    # ///////////////////////////////////////////////////////////////

    def mousePressEvent(self, _event: QMouseEvent) -> None:
        """Handle mouse press events.

        Args:
            _event: The mouse event (unused but required by signature).
        """
        self.clicked.emit()

    # ///////////////////////////////////////////////////////////////
    # PUBLIC METHODS
    # ///////////////////////////////////////////////////////////////

    def startTimer(self) -> None:  # type: ignore[override]
        """Start the circular timer."""
        self.stopTimer()  # Always stop before starting
        self._running = True
        self._last_update = None
        self.timer.start(self._interval)

    def stopTimer(self) -> None:
        """Stop the circular timer."""
        self.resetTimer()  # Always reset to zero
        self._running = False
        self.timer.stop()

    def resetTimer(self) -> None:
        """Reset the circular timer."""
        self._elapsed = 0
        self._last_update = None
        self.timerReset.emit()
        self.update()

    # ------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------

    def _on_timer(self) -> None:
        """Internal callback for smooth animation."""
        import time

        now = time.monotonic() * 1000  # ms
        if self._last_update is None:
            self._last_update = now
            return
        delta = now - self._last_update
        self._last_update = now
        self._elapsed += int(delta)
        if self._elapsed > self._duration:
            self.cycleCompleted.emit()
            if self._loop:
                self.resetTimer()
                self._running = True
                self._last_update = now
                # Timer continues (no stop)
            else:
                self.resetTimer()
                self.stopTimer()
        self.update()

    # ///////////////////////////////////////////////////////////////
    # OVERRIDE METHODS
    # ///////////////////////////////////////////////////////////////

    def minimumSizeHint(self) -> QSize:
        """Get the recommended minimum size for the widget.

        Returns:
            The minimum size hint.
        """
        return QSize(24, 24)

    def paintEvent(self, _event: QPaintEvent) -> None:
        """Draw the animated circular timer.

        Args:
            _event: The paint event (unused but required by signature).
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = min(self.width(), self.height())

        # Pen width (dynamic mode or fixed value)
        if self._pen_width is not None:
            penWidth = int(self._pen_width)
        else:
            if self._ring_width_mode == "small":
                penWidth = int(max(size * 0.12, 3))
            elif self._ring_width_mode == "large":
                penWidth = int(max(size * 0.28, 3))
            else:  # medium
                penWidth = int(max(size * 0.18, 3))

        # Node circle (precise centering)
        center = size / 2
        node_radius = (size - 2 * penWidth) / 2 - penWidth / 2
        if node_radius > 0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self._node_color)
            painter.drawEllipse(
                int(center - node_radius),
                int(center - node_radius),
                int(2 * node_radius),
                int(2 * node_radius),
            )

        # Ring arc (clockwise, starting at 12 o'clock)
        painter.setPen(
            QPen(
                self._ring_color,
                penWidth,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        angle = int((self._elapsed / self._duration) * 360 * 16)
        painter.drawArc(
            penWidth,
            penWidth,
            int(size - 2 * penWidth),
            int(size - 2 * penWidth),
            90 * 16,
            -angle,  # clockwise
        )

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
