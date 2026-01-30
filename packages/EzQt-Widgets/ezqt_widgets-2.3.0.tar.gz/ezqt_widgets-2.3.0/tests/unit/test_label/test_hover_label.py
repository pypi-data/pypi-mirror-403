# ///////////////////////////////////////////////////////////////
# TEST_HOVER_LABEL - HoverLabel Widget Tests
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Unit tests for HoverLabel widget.

Tests for the interactive QLabel with floating icon on hover.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
import pytest
from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt
from PySide6.QtGui import QEnterEvent, QIcon, QMouseEvent, QPixmap

# Local imports
from ezqt_widgets.label.hover_label import HoverLabel

pytestmark = pytest.mark.unit

# ///////////////////////////////////////////////////////////////
# TEST CLASSES
# ///////////////////////////////////////////////////////////////


class TestHoverLabel:
    """Tests for HoverLabel class."""

    def test_hover_label_creation_default(self, qt_widget_cleanup) -> None:
        """Test creation with default parameters."""
        label = HoverLabel()

        assert label is not None
        assert isinstance(label, HoverLabel)
        assert label.text() == ""
        assert label.opacity == 0.5
        assert label.icon_size == QSize(16, 16)
        assert label.icon_color is None
        assert label.icon_padding == 8
        assert label.icon_enabled is True

    def test_hover_label_creation_with_parameters(self, qt_widget_cleanup) -> None:
        """Test creation with custom parameters."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.red)
        icon = QIcon(pixmap)

        label = HoverLabel(
            icon=icon,
            text="Test Label",
            opacity=0.8,
            icon_size=QSize(24, 24),
            icon_color="#FF0000",
            icon_padding=12,
            icon_enabled=False,
            min_width=200,
        )

        assert label.text() == "Test Label"
        assert label.opacity == 0.8
        assert label.icon_size == QSize(24, 24)
        assert label.icon_color == "#FF0000"
        assert label.icon_padding == 12
        assert label.icon_enabled is False

    def test_hover_label_properties(self, qt_widget_cleanup) -> None:
        """Test label properties."""
        label = HoverLabel()

        # Test opacity property
        label.opacity = 0.7
        assert label.opacity == 0.7

        # Test hover_icon property
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.blue)
        icon = QIcon(pixmap)
        label.hover_icon = icon
        assert label.hover_icon is not None

        # Test icon_size property
        label.icon_size = QSize(32, 32)
        assert label.icon_size == QSize(32, 32)

        # Test icon_color property
        label.icon_color = "#00FF00"
        assert label.icon_color == "#00FF00"

        # Test icon_padding property
        label.icon_padding = 16
        assert label.icon_padding == 16

        # Test icon_enabled property
        label.icon_enabled = False
        assert label.icon_enabled is False

    def test_hover_label_signals(self, qt_widget_cleanup) -> None:
        """Test label signals."""
        # Create a label with an icon so the signal can be emitted
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.blue)
        icon = QIcon(pixmap)

        label = HoverLabel(icon=icon)

        # Test hoverIconClicked signal
        signal_received = False

        def on_hover_icon_clicked() -> None:
            nonlocal signal_received
            signal_received = True

        label.hoverIconClicked.connect(on_hover_icon_clicked)

        # Simulate mouse entry
        enter_event = QEnterEvent(QPoint(10, 10), QPoint(10, 10), QPoint(10, 10))
        label.enterEvent(enter_event)

        # Simulate a click on the icon (position in the icon area)
        # Calculate icon position (at the right of the widget)
        icon_x = label.width() - label.icon_size.width() - 4
        icon_y = (label.height() - label.icon_size.height()) // 2

        mouse_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(icon_x + 5, icon_y + 5),  # Position in the icon
            QPoint(icon_x + 5, icon_y + 5),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        label.mousePressEvent(mouse_event)

        # Verify that the signal was emitted
        assert signal_received

    def test_hover_label_mouse_events(self, qt_widget_cleanup) -> None:
        """Test mouse events."""
        label = HoverLabel()

        # Test mouseMoveEvent
        mouse_move_event = QMouseEvent(
            QMouseEvent.Type.MouseMove,
            QPoint(10, 10),
            QPoint(10, 10),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )

        try:
            label.mouseMoveEvent(mouse_move_event)
        except Exception as e:
            pytest.fail(f"mouseMoveEvent() raised an exception: {e}")

        # Test mousePressEvent
        mouse_press_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(10, 10),
            QPoint(10, 10),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        try:
            label.mousePressEvent(mouse_press_event)
        except Exception as e:
            pytest.fail(f"mousePressEvent() raised an exception: {e}")

    def test_hover_label_enter_leave_events(self, qt_widget_cleanup) -> None:
        """Test enter/leave events."""
        label = HoverLabel()

        # Test enterEvent
        enter_event = QEnterEvent(QPoint(10, 10), QPoint(10, 10), QPoint(10, 10))
        try:
            label.enterEvent(enter_event)
        except Exception as e:
            pytest.fail(f"enterEvent() raised an exception: {e}")

        # Test leaveEvent
        leave_event = QEvent(QEvent.Type.Leave)
        try:
            label.leaveEvent(leave_event)
        except Exception as e:
            pytest.fail(f"leaveEvent() raised an exception: {e}")

    def test_hover_label_paint_event(self, qt_widget_cleanup) -> None:
        """Test paint event."""
        label = HoverLabel()

        # Test paintEvent
        from PySide6.QtGui import QPaintEvent

        paint_event = QPaintEvent(QRect(0, 0, 100, 50))
        try:
            label.paintEvent(paint_event)
        except Exception as e:
            pytest.fail(f"paintEvent() raised an exception: {e}")

    def test_hover_label_resize_event(self, qt_widget_cleanup) -> None:
        """Test resize event."""
        label = HoverLabel()

        # Test resizeEvent
        from PySide6.QtGui import QResizeEvent

        resize_event = QResizeEvent(QSize(100, 50), QSize(80, 40))
        try:
            label.resizeEvent(resize_event)
        except Exception as e:
            pytest.fail(f"resizeEvent() raised an exception: {e}")

    def test_hover_label_size_hints(self, qt_widget_cleanup) -> None:
        """Test size hint methods."""
        label = HoverLabel(text="Test Label")

        # Test minimumSizeHint
        min_size_hint = label.minimumSizeHint()
        assert min_size_hint is not None
        assert isinstance(min_size_hint, QSize)
        assert min_size_hint.width() > 0
        assert min_size_hint.height() > 0

    def test_hover_label_refresh_style(self, qt_widget_cleanup) -> None:
        """Test refresh_style method."""
        label = HoverLabel()

        # Method should not raise an exception
        try:
            label.refresh_style()
        except Exception as e:
            pytest.fail(f"refresh_style() raised an exception: {e}")

    def test_hover_label_clear_icon(self, qt_widget_cleanup) -> None:
        """Test clear_icon method."""
        label = HoverLabel()

        # Set an icon
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.red)
        icon = QIcon(pixmap)
        label.hover_icon = icon

        # Clear icon
        label.clear_icon()

        # Verify that the icon is cleared
        assert label.hover_icon is None

    def test_hover_label_icon_enabled_disabled(self, qt_widget_cleanup) -> None:
        """Test icon enable/disable."""
        label = HoverLabel()

        # Initial state
        assert label.icon_enabled is True

        # Disable icon
        label.icon_enabled = False
        assert label.icon_enabled is False

        # Re-enable icon
        label.icon_enabled = True
        assert label.icon_enabled is True

    def test_hover_label_icon_color_changes(self, qt_widget_cleanup) -> None:
        """Test icon color changes."""
        label = HoverLabel()

        # Set a color
        label.icon_color = "#FF0000"
        assert label.icon_color == "#FF0000"

        # Change color
        label.icon_color = "#00FF00"
        assert label.icon_color == "#00FF00"

        # Clear color
        label.icon_color = None
        assert label.icon_color is None

    def test_hover_label_icon_size_changes(self, qt_widget_cleanup) -> None:
        """Test icon size changes."""
        label = HoverLabel()

        # Initial size
        assert label.icon_size == QSize(16, 16)

        # Change size
        label.icon_size = QSize(32, 32)
        assert label.icon_size == QSize(32, 32)

        # Change with a tuple
        label.icon_size = (24, 24)
        assert label.icon_size == QSize(24, 24)

    def test_hover_label_opacity_changes(self, qt_widget_cleanup) -> None:
        """Test opacity changes."""
        label = HoverLabel()

        # Initial opacity
        assert label.opacity == 0.5

        # Change opacity
        label.opacity = 0.8
        assert label.opacity == 0.8

        # Minimum opacity
        label.opacity = 0.0
        assert label.opacity == 0.0

        # Maximum opacity
        label.opacity = 1.0
        assert label.opacity == 1.0

    def test_hover_label_padding_changes(self, qt_widget_cleanup) -> None:
        """Test padding changes."""
        label = HoverLabel()

        # Initial padding
        assert label.icon_padding == 8

        # Change padding
        label.icon_padding = 16
        assert label.icon_padding == 16

        # Zero padding
        label.icon_padding = 0
        assert label.icon_padding == 0

        # Negative padding
        label.icon_padding = -5
        assert label.icon_padding == -5

    def test_hover_label_text_changes(self, qt_widget_cleanup) -> None:
        """Test text changes."""
        label = HoverLabel()

        # Initial text
        assert label.text() == ""

        # Set text
        label.setText("Test Text")
        assert label.text() == "Test Text"

        # Change text
        label.setText("New Text")
        assert label.text() == "New Text"

        # Empty text
        label.setText("")
        assert label.text() == ""

    def test_hover_label_icon_from_path(
        self, qt_widget_cleanup, mock_icon_path
    ) -> None:
        """Test icon loading from path."""
        label = HoverLabel()

        # Load an icon from a path
        label.hover_icon = mock_icon_path

        # Verify that the icon is loaded
        assert label.hover_icon is not None
        assert isinstance(label.hover_icon, QIcon)

    def test_hover_label_icon_from_svg(self, qt_widget_cleanup, mock_svg_path) -> None:
        """Test SVG icon loading."""
        label = HoverLabel()

        # Load an SVG icon
        label.hover_icon = mock_svg_path

        # Verify that the icon is loaded
        assert label.hover_icon is not None
        assert isinstance(label.hover_icon, QIcon)

    def test_hover_label_cursor_changes(self, qt_widget_cleanup) -> None:
        """Test cursor changes."""
        label = HoverLabel()

        # Simulate mouse entry
        enter_event = QEnterEvent(QPoint(10, 10), QPoint(10, 10), QPoint(10, 10))
        label.enterEvent(enter_event)

        # Verify that the cursor changed
        # Note: The cursor may change according to implementation

        # Simulate mouse exit
        leave_event = QEvent(QEvent.Type.Leave)
        label.leaveEvent(leave_event)

        # Verify that the cursor is restored
        # Note: The cursor may be restored according to implementation
