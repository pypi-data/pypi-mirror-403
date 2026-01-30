# ///////////////////////////////////////////////////////////////
# TEST_TOGGLE_ICON - ToggleIcon Widget Tests
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Unit tests for ToggleIcon widget.

Tests for the label widget with toggleable icons.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
import pytest
from PySide6.QtGui import QColor

# Local imports
from ezqt_widgets.misc.toggle_icon import ToggleIcon

pytestmark = pytest.mark.unit

# ///////////////////////////////////////////////////////////////
# TEST CLASSES
# ///////////////////////////////////////////////////////////////


class TestToggleIcon:
    """Test cases for ToggleIcon widget."""

    def test_toggle_icon_creation_default(self, qt_application) -> None:
        """Test ToggleIcon creation with default parameters."""
        icon = ToggleIcon()

        assert icon.state == "closed"  # Default state
        assert icon.icon_size == 16
        assert icon.icon_color == QColor(255, 255, 255, 128)  # White with 0.5 opacity
        assert icon.min_width is None
        assert icon.min_height is None

    def test_toggle_icon_creation_custom(self, qt_application) -> None:
        """Test ToggleIcon creation with custom parameters."""
        icon = ToggleIcon(
            opened_icon="path/to/opened.png",
            closed_icon="path/to/closed.png",
            icon_size=24,
            icon_color="#ff0000",
            initial_state="opened",
            min_width=50,
            min_height=30,
        )

        assert icon.state == "opened"
        assert icon.icon_size == 24
        assert icon.icon_color == QColor("#ff0000")
        assert icon.min_width == 50
        assert icon.min_height == 30

    def test_toggle_icon_set_icons(self, qt_application) -> None:
        """Test setting icons."""
        icon = ToggleIcon()

        # Set opened icon
        icon.opened_icon = "path/to/new_opened.png"
        assert icon.opened_icon is not None

        # Set closed icon
        icon.closed_icon = "path/to/new_closed.png"
        assert icon.closed_icon is not None

    def test_toggle_icon_toggle(self, qt_application) -> None:
        """Test toggling the icon state."""
        icon = ToggleIcon(initial_state="closed")

        # Toggle from closed to opened
        icon.toggle_state()
        assert icon.state == "opened"

        # Toggle from opened to closed
        icon.toggle_state()
        assert icon.state == "closed"

    def test_toggle_icon_set_state(self, qt_application) -> None:
        """Test setting state directly."""
        icon = ToggleIcon()

        # Set to opened
        icon.state = "opened"
        assert icon.state == "opened"
        assert icon.is_opened()

        # Set to closed
        icon.state = "closed"
        assert icon.state == "closed"
        assert icon.is_closed()

    def test_toggle_icon_state_methods(self, qt_application) -> None:
        """Test state checking methods."""
        icon = ToggleIcon(initial_state="closed")

        assert icon.is_closed()
        assert not icon.is_opened()

        icon.state = "opened"
        assert icon.is_opened()
        assert not icon.is_closed()

    def test_toggle_icon_signals(self, qt_application) -> None:
        """Test toggle icon signals."""
        icon = ToggleIcon()

        state_changed_called = False
        clicked_called = False

        def on_state_changed(_state: str) -> None:
            nonlocal state_changed_called
            state_changed_called = True

        def on_clicked() -> None:
            nonlocal clicked_called
            clicked_called = True

        icon.stateChanged.connect(on_state_changed)
        icon.clicked.connect(on_clicked)

        # Change state
        icon.state = "opened"
        assert state_changed_called

    def test_toggle_icon_set_icon_size(self, qt_application) -> None:
        """Test setting icon size."""
        icon = ToggleIcon()

        icon.icon_size = 32
        assert icon.icon_size == 32

    def test_toggle_icon_set_icon_color(self, qt_application) -> None:
        """Test setting icon color."""
        icon = ToggleIcon()

        icon.icon_color = "#00ff00"
        assert icon.icon_color == QColor("#00ff00")

    def test_toggle_icon_set_min_size(self, qt_application) -> None:
        """Test setting minimum size."""
        icon = ToggleIcon()

        icon.min_width = 100
        icon.min_height = 50

        assert icon.min_width == 100
        assert icon.min_height == 50

    def test_toggle_icon_size_hints(self, qt_application) -> None:
        """Test size hint methods."""
        icon = ToggleIcon()

        min_size_hint = icon.minimumSizeHint()
        assert min_size_hint.width() > 0
        assert min_size_hint.height() > 0

    def test_toggle_icon_set_state_methods(self, qt_application) -> None:
        """Test set state methods."""
        icon = ToggleIcon(initial_state="closed")

        # Set to opened
        icon.set_state_opened()
        assert icon.state == "opened"

        # Set to closed
        icon.set_state_closed()
        assert icon.state == "closed"
