# ///////////////////////////////////////////////////////////////
# TEST_TOGGLE_SWITCH - ToggleSwitch Widget Tests
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Unit tests for ToggleSwitch widget.

Tests for the modern toggle switch widget.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent

# Local imports
from ezqt_widgets.misc.toggle_switch import ToggleSwitch

pytestmark = pytest.mark.unit

# ///////////////////////////////////////////////////////////////
# TEST CLASSES
# ///////////////////////////////////////////////////////////////


class TestToggleSwitch:
    """Test cases for ToggleSwitch widget."""

    def test_toggle_switch_creation_default(self, qt_application) -> None:
        """Test ToggleSwitch creation with default parameters."""
        switch = ToggleSwitch()

        assert not switch.checked  # Default state
        assert switch.width == 50
        assert switch.height == 24
        assert switch.animation  # Animation enabled by default

    def test_toggle_switch_creation_custom(self, qt_application) -> None:
        """Test ToggleSwitch creation with custom parameters."""
        switch = ToggleSwitch(checked=True, width=80, height=30, animation=False)

        assert switch.checked
        assert switch.width == 80
        assert switch.height == 30
        assert not switch.animation

    def test_toggle_switch_set_checked(self, qt_application) -> None:
        """Test setting checked state."""
        switch = ToggleSwitch()

        switch.checked = True
        assert switch.checked

        switch.checked = False
        assert not switch.checked

    def test_toggle_switch_toggle(self, qt_application) -> None:
        """Test toggling the switch."""
        switch = ToggleSwitch(checked=False)

        # Toggle from False to True
        switch.toggle()
        assert switch.checked

        # Toggle from True to False
        switch.toggle()
        assert not switch.checked

    def test_toggle_switch_set_width(self, qt_application) -> None:
        """Test setting width."""
        switch = ToggleSwitch()

        switch.width = 100
        assert switch.width == 100

    def test_toggle_switch_set_height(self, qt_application) -> None:
        """Test setting height."""
        switch = ToggleSwitch()

        switch.height = 40
        assert switch.height == 40

    def test_toggle_switch_set_animation(self, qt_application) -> None:
        """Test setting animation."""
        switch = ToggleSwitch()

        switch.animation = False
        assert not switch.animation

        switch.animation = True
        assert switch.animation

    def test_toggle_switch_signals(self, qt_application) -> None:
        """Test toggle switch signals."""
        switch = ToggleSwitch()

        toggled_called = False

        def on_toggled(_state: bool) -> None:
            nonlocal toggled_called
            toggled_called = True

        switch.toggled.connect(on_toggled)

        # Toggle the switch
        switch.toggle()
        assert toggled_called

    def test_toggle_switch_size_hints(self, qt_widget_cleanup) -> None:
        """Test size hint methods."""
        switch = ToggleSwitch()

        # Force widget initialization
        switch.show()
        switch.resize(100, 100)

        size_hint = switch.sizeHint()
        assert size_hint.width() == 50  # Default width
        assert size_hint.height() == 24  # Default height

        min_size_hint = switch.minimumSizeHint()
        assert min_size_hint.width() == 50
        assert min_size_hint.height() == 24

    def test_toggle_switch_mouse_press(self, qt_widget_cleanup) -> None:
        """Test mouse press event."""
        switch = ToggleSwitch(checked=False)
        initial_state = switch.checked

        # Simulate mouse press with real Qt event
        mouse_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(10, 10),
            QPoint(10, 10),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        switch.mousePressEvent(mouse_event)

        # State should have changed
        assert switch.checked != initial_state
