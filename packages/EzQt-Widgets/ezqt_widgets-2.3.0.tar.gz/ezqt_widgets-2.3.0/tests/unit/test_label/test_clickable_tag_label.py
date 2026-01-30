# ///////////////////////////////////////////////////////////////
# TEST_CLICKABLE_TAG_LABEL - ClickableTagLabel Widget Tests
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Unit tests for ClickableTagLabel widget.

Tests for the clickable tag label widget with toggle functionality.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
from unittest.mock import MagicMock

# Third-party imports
import pytest
from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import QMouseEvent

# Local imports
from ezqt_widgets.label.clickable_tag_label import ClickableTagLabel

pytestmark = pytest.mark.unit

# ///////////////////////////////////////////////////////////////
# TEST CLASSES
# ///////////////////////////////////////////////////////////////


class TestClickableTagLabel:
    """Tests for ClickableTagLabel class."""

    def test_clickable_tag_label_creation_default(self, qt_widget_cleanup) -> None:
        """Test creation with default parameters."""
        tag = ClickableTagLabel()

        assert tag is not None
        assert isinstance(tag, ClickableTagLabel)
        assert tag.name == ""
        assert tag.enabled is False
        assert tag.status_color == "#0078d4"

    def test_clickable_tag_label_creation_with_parameters(
        self, qt_widget_cleanup
    ) -> None:
        """Test creation with custom parameters."""
        tag = ClickableTagLabel(
            name="Test Tag",
            enabled=True,
            status_color="#FF0000",
            min_width=100,
            min_height=30,
        )

        assert tag.name == "Test Tag"
        assert tag.enabled is True
        assert tag.status_color == "#FF0000"
        assert tag.min_width == 100
        assert tag.min_height == 30

    def test_clickable_tag_label_properties(self, qt_widget_cleanup) -> None:
        """Test tag properties."""
        tag = ClickableTagLabel()

        # Test name property
        tag.name = "New Tag Name"
        assert tag.name == "New Tag Name"

        # Test enabled property
        tag.enabled = True
        assert tag.enabled is True

        # Test status_color property
        tag.status_color = "#00FF00"
        assert tag.status_color == "#00FF00"

        # Test min_width property
        tag.min_width = 150
        assert tag.min_width == 150

        # Test min_height property
        tag.min_height = 40
        assert tag.min_height == 40

        # Test with None
        tag.min_width = None
        tag.min_height = None
        assert tag.min_width is None
        assert tag.min_height is None

    def test_clickable_tag_label_signals(self, qt_widget_cleanup) -> None:
        """Test tag signals."""
        tag = ClickableTagLabel(name="Test Tag")

        # Test clicked signal
        clicked_signal_received = False

        def on_clicked() -> None:
            nonlocal clicked_signal_received
            clicked_signal_received = True

        tag.clicked.connect(on_clicked)

        # Simulate a click with real Qt event
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(10, 10),
            QPoint(10, 10),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        tag.mousePressEvent(event)

        # Verify that the signal was emitted
        assert clicked_signal_received

        # Test toggle_keyword signal
        toggle_signal_received = False
        received_keyword = ""

        def on_toggle_keyword(keyword: str) -> None:
            nonlocal toggle_signal_received, received_keyword
            toggle_signal_received = True
            received_keyword = keyword

        tag.toggle_keyword.connect(on_toggle_keyword)

        # Simulate a click for toggle
        tag.mousePressEvent(event)

        # Verify that the signal was emitted
        assert toggle_signal_received
        assert received_keyword == "Test Tag"

        # Test stateChanged signal
        state_signal_received = False
        received_state: bool | None = None

        def on_state_changed(state: bool) -> None:
            nonlocal state_signal_received, received_state
            state_signal_received = True
            received_state = state

        tag.stateChanged.connect(on_state_changed)

        # Change state
        tag.enabled = True

        # Verify that the signal was emitted
        assert state_signal_received
        assert received_state is True

    def test_clickable_tag_label_mouse_press_event(self, qt_widget_cleanup) -> None:
        """Test mousePressEvent."""
        tag = ClickableTagLabel(name="Test Tag")

        # Test left click
        left_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(10, 10),
            QPoint(10, 10),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        # Verify that the event does not raise an exception
        try:
            tag.mousePressEvent(left_event)
        except Exception as e:
            pytest.fail(f"mousePressEvent() raised an exception: {e}")

        # Test right click (should not trigger signals)
        right_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(10, 10),
            QPoint(10, 10),
            Qt.MouseButton.RightButton,
            Qt.MouseButton.RightButton,
            Qt.KeyboardModifier.NoModifier,
        )

        try:
            tag.mousePressEvent(right_event)
        except Exception as e:
            pytest.fail(f"mousePressEvent() raised an exception: {e}")

    def test_clickable_tag_label_key_press_event(self, qt_widget_cleanup) -> None:
        """Test keyPressEvent."""
        tag = ClickableTagLabel(name="Test Tag")

        # Test space key
        mock_event = MagicMock()
        mock_event.key.return_value = Qt.Key.Key_Space

        # Verify that the event does not raise an exception
        try:
            tag.keyPressEvent(mock_event)
        except Exception as e:
            pytest.fail(f"keyPressEvent() raised an exception: {e}")

        # Test other key (should not trigger signals)
        mock_event.key.return_value = Qt.Key.Key_Enter

        try:
            tag.keyPressEvent(mock_event)
        except Exception as e:
            pytest.fail(f"keyPressEvent() raised an exception: {e}")

    def test_clickable_tag_label_toggle_behavior(self, qt_widget_cleanup) -> None:
        """Test toggle behavior."""
        tag = ClickableTagLabel(name="Test Tag")

        # Initial state
        assert tag.enabled is False

        # First click - activate tag
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(10, 10),
            QPoint(10, 10),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        clicked_count = 0

        def on_clicked() -> None:
            nonlocal clicked_count
            clicked_count += 1

        tag.clicked.connect(on_clicked)
        tag.mousePressEvent(event)

        # Verify that the tag is now active
        assert tag.enabled is True
        assert clicked_count == 1

        # Second click - deactivate tag
        tag.mousePressEvent(event)

        # Verify that the tag is now inactive
        assert tag.enabled is False
        assert clicked_count == 2

    def test_clickable_tag_label_toggle_via_property(self, qt_widget_cleanup) -> None:
        """Test toggle via enabled property."""
        tag = ClickableTagLabel(name="Test Tag")

        # Initial state
        assert tag.enabled is False

        # Connect signal
        state_signal_received = False
        received_state: bool | None = None

        def on_state_changed(state: bool) -> None:
            nonlocal state_signal_received, received_state
            state_signal_received = True
            received_state = state

        tag.stateChanged.connect(on_state_changed)

        # Toggle via property
        tag.enabled = True
        assert tag.enabled is True
        assert state_signal_received
        assert received_state is True

        # Toggle again
        tag.enabled = False
        assert tag.enabled is False

    def test_clickable_tag_label_keyboard_toggle(self, qt_widget_cleanup) -> None:
        """Test keyboard toggle."""
        tag = ClickableTagLabel(name="Test Tag")

        # Initial state
        assert tag.enabled is False

        # Space key - activate tag
        mock_event = MagicMock()
        mock_event.key.return_value = Qt.Key.Key_Space

        clicked_count = 0

        def on_clicked() -> None:
            nonlocal clicked_count
            clicked_count += 1

        tag.clicked.connect(on_clicked)
        tag.keyPressEvent(mock_event)

        # Verify that the tag is now active
        assert tag.enabled is True
        assert clicked_count == 1

        # Second space key - deactivate tag
        tag.keyPressEvent(mock_event)

        # Verify that the tag is now inactive
        assert tag.enabled is False
        assert clicked_count == 2

    def test_clickable_tag_label_size_hints(self, qt_widget_cleanup) -> None:
        """Test size hint methods."""
        tag = ClickableTagLabel(name="Test Tag")

        # Test sizeHint
        size_hint = tag.sizeHint()
        assert size_hint is not None
        assert isinstance(size_hint, QSize)
        assert size_hint.width() > 0
        assert size_hint.height() > 0

        # Test minimumSizeHint
        min_size_hint = tag.minimumSizeHint()
        assert min_size_hint is not None
        assert isinstance(min_size_hint, QSize)
        assert min_size_hint.width() > 0
        assert min_size_hint.height() > 0

    def test_clickable_tag_label_refresh_style(self, qt_widget_cleanup) -> None:
        """Test refresh_style method."""
        tag = ClickableTagLabel()

        # Method should not raise an exception
        try:
            tag.refresh_style()
        except Exception as e:
            pytest.fail(f"refresh_style() raised an exception: {e}")

    def test_clickable_tag_label_display_update(self, qt_widget_cleanup) -> None:
        """Test display update."""
        tag = ClickableTagLabel(name="Test Tag")

        # Verify initial display
        assert tag.name == "Test Tag"

        # Change name
        tag.name = "New Tag Name"
        assert tag.name == "New Tag Name"

        # Change color
        tag.status_color = "#FF0000"
        assert tag.status_color == "#FF0000"

    def test_clickable_tag_label_accessibility(self, qt_widget_cleanup) -> None:
        """Test accessibility."""
        tag = ClickableTagLabel(name="Test Tag")

        # Verify that the widget can receive focus
        # Note: focusPolicy may vary according to implementation
        focus_policy = tag.focusPolicy()
        assert focus_policy in [
            Qt.FocusPolicy.StrongFocus,
            Qt.FocusPolicy.ClickFocus,
            Qt.FocusPolicy.TabFocus,
            Qt.FocusPolicy.WheelFocus,
        ]

        # Verify that the widget is focusable
        tag.setFocus()
        # Note: hasFocus() may not work in a test context
        # Let's verify that setFocus() doesn't raise an exception
        try:
            tag.setFocus()
        except Exception as e:
            pytest.fail(f"setFocus() raised an exception: {e}")

    def test_clickable_tag_label_properties_validation(self, qt_widget_cleanup) -> None:
        """Test property validation."""
        tag = ClickableTagLabel()

        # Test empty name
        tag.name = ""
        assert tag.name == ""

        # Test name with spaces
        tag.name = "   Tag with spaces   "
        assert tag.name == "   Tag with spaces   "

        # Test invalid color (should be accepted)
        tag.status_color = "invalid_color"
        assert tag.status_color == "invalid_color"

        # Test negative dimensions (should be accepted)
        tag.min_width = -10
        tag.min_height = -5
        assert tag.min_width == -10
        assert tag.min_height == -5
