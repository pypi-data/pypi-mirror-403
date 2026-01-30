# ///////////////////////////////////////////////////////////////
# TEST_PASSWORD_INPUT - PasswordInput Widget Tests
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Unit tests for PasswordInput widget.

Tests for the password input widget with strength bar and show/hide icon.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
from unittest.mock import MagicMock, patch

# Third-party imports
import pytest
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap

# Local imports
from ezqt_widgets.input.password_input import (
    PasswordInput,
    PasswordLineEdit,
    colorize_pixmap,
    get_strength_color,
    load_icon_from_source,
    password_strength,
)

pytestmark = pytest.mark.unit

# ///////////////////////////////////////////////////////////////
# TEST CLASSES
# ///////////////////////////////////////////////////////////////


class TestPasswordStrength:
    """Tests for password strength utility functions."""

    def test_password_strength_weak(self) -> None:
        """Test weak password strength."""
        # Very weak password
        assert password_strength("") == 0
        assert password_strength("a") == 15  # 1 char + lowercase
        assert password_strength("123") == 20  # 3 chars + digits

        # Weak password
        assert password_strength("password") == 40  # 8+ chars + lowercase
        assert password_strength("12345678") == 45  # 8+ chars + digits

    def test_password_strength_medium(self) -> None:
        """Test medium password strength."""
        # Medium password
        assert password_strength("Password") == 55  # 8+ chars + lowercase + uppercase
        assert password_strength("pass1234") == 60  # 8+ chars + lowercase + digits
        assert password_strength("PASS1234") == 60  # 8+ chars + uppercase + digits

    def test_password_strength_strong(self) -> None:
        """Test strong password strength."""
        # Strong password
        assert (
            password_strength("Password123") == 75
        )  # 8+ chars + lowercase + uppercase + digits
        assert (
            password_strength("Pass@word") == 80
        )  # 8+ chars + lowercase + uppercase + special
        assert (
            password_strength("Pass@123") == 100
        )  # 8+ chars + lowercase + uppercase + digits + special (max 100)

    def test_password_strength_very_strong(self) -> None:
        """Test very strong password strength."""
        # Very strong password
        assert password_strength("MyP@ssw0rd!") == 100  # All criteria
        assert password_strength("SuperS3cret#") == 100  # All criteria
        assert password_strength("C0mpl3x!P@ss") == 100  # All criteria

    def test_password_strength_edge_cases(self) -> None:
        """Test password strength with edge cases."""
        # Special characters
        assert password_strength("pass@word") == 65  # 8+ chars + lowercase + special
        assert password_strength("PASS@WORD") == 65  # 8+ chars + uppercase + special

        # Extreme length
        assert password_strength("a" * 100) == 40  # Length + lowercase
        assert password_strength("A" * 100) == 40  # Length + uppercase

    def test_get_strength_color_weak(self) -> None:
        """Test colors for weak passwords."""
        assert get_strength_color(0) == "#ff4444"  # Red
        assert get_strength_color(10) == "#ff4444"  # Red
        assert get_strength_color(29) == "#ff4444"  # Red

    def test_get_strength_color_medium(self) -> None:
        """Test colors for medium passwords."""
        assert get_strength_color(30) == "#ffaa00"  # Orange
        assert get_strength_color(50) == "#ffaa00"  # Orange
        assert get_strength_color(59) == "#ffaa00"  # Orange

    def test_get_strength_color_good(self) -> None:
        """Test colors for good passwords."""
        assert get_strength_color(60) == "#44aa44"  # Green
        assert get_strength_color(70) == "#44aa44"  # Green
        assert get_strength_color(79) == "#44aa44"  # Green

    def test_get_strength_color_strong(self) -> None:
        """Test colors for strong passwords."""
        assert get_strength_color(80) == "#00aa00"  # Dark green
        assert get_strength_color(90) == "#00aa00"  # Dark green
        assert get_strength_color(100) == "#00aa00"  # Dark green


class TestColorizePixmap:
    """Tests for colorize_pixmap function."""

    def test_colorize_pixmap_basic(self, qt_widget_cleanup) -> None:
        """Basic test for colorize_pixmap."""
        # Create a test pixmap
        original_pixmap = QPixmap(16, 16)
        original_pixmap.fill(Qt.GlobalColor.white)

        # Colorize the pixmap
        colored_pixmap = colorize_pixmap(original_pixmap, "#ff0000", 0.5)

        # Verify that the result is a pixmap
        assert isinstance(colored_pixmap, QPixmap)
        assert colored_pixmap.size() == original_pixmap.size()

    def test_colorize_pixmap_different_colors(self, qt_widget_cleanup) -> None:
        """Test colorize_pixmap with different colors."""
        original_pixmap = QPixmap(16, 16)
        original_pixmap.fill(Qt.GlobalColor.white)

        # Test different colors
        colors = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff"]
        for color in colors:
            colored_pixmap = colorize_pixmap(original_pixmap, color, 0.5)
            assert isinstance(colored_pixmap, QPixmap)

    def test_colorize_pixmap_different_opacities(self, qt_widget_cleanup) -> None:
        """Test colorize_pixmap with different opacities."""
        original_pixmap = QPixmap(16, 16)
        original_pixmap.fill(Qt.GlobalColor.white)

        # Test different opacities
        opacities = [0.0, 0.25, 0.5, 0.75, 1.0]
        for opacity in opacities:
            colored_pixmap = colorize_pixmap(original_pixmap, "#ff0000", opacity)
            assert isinstance(colored_pixmap, QPixmap)


class TestLoadIconFromSource:
    """Tests for load_icon_from_source function."""

    def test_load_icon_from_source_none(self) -> None:
        """Test load_icon_from_source with None."""
        icon = load_icon_from_source(None)
        assert icon is None

    def test_load_icon_from_source_qicon(self, qt_widget_cleanup) -> None:
        """Test load_icon_from_source with QIcon."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.red)
        original_icon = QIcon(pixmap)

        icon = load_icon_from_source(original_icon)
        assert isinstance(icon, QIcon)

    @patch("requests.get")
    def test_load_icon_from_source_url(self, mock_get, qt_widget_cleanup) -> None:
        """Test load_icon_from_source with URL."""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf5\x01\x00\x00\x00\x00IEND\xaeB`\x82"
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "image/png"}
        mock_get.return_value = mock_response

        # Test icon loading from URL
        icon = load_icon_from_source("https://example.com/icon.png")
        assert isinstance(icon, QIcon)

    @patch("requests.get")
    def test_load_icon_from_source_url_failure(self, mock_get) -> None:
        """Test load_icon_from_source with URL failure."""
        # Mock HTTP failure
        mock_get.side_effect = Exception("Network error")

        # Test loading failure
        icon = load_icon_from_source("https://example.com/icon.png")
        assert icon is None


class TestPasswordLineEdit:
    """Tests for PasswordLineEdit class."""

    def test_password_line_edit_creation(self, qt_widget_cleanup) -> None:
        """Test PasswordLineEdit creation."""
        line_edit = PasswordLineEdit()

        assert line_edit is not None
        assert isinstance(line_edit, PasswordLineEdit)
        assert line_edit.echoMode() == line_edit.EchoMode.Password

    def test_password_line_edit_set_right_icon(self, qt_widget_cleanup) -> None:
        """Test set_right_icon."""
        line_edit = PasswordLineEdit()

        # Create an icon
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.red)
        icon = QIcon(pixmap)

        # Set the icon
        line_edit.set_right_icon(icon, QSize(20, 20))

        # Verify that the icon is set
        # Note: We can't easily verify the internal icon
        # but we can verify that the method doesn't raise an exception
        assert line_edit is not None

    def test_password_line_edit_refresh_style(self, qt_widget_cleanup) -> None:
        """Test refresh_style."""
        line_edit = PasswordLineEdit()

        # Method should not raise an exception
        try:
            line_edit.refresh_style()
        except Exception as e:
            pytest.fail(f"refresh_style() raised an exception: {e}")


class TestPasswordInput:
    """Tests for PasswordInput class."""

    def test_password_input_creation_default(self, qt_widget_cleanup) -> None:
        """Test creation with default parameters."""
        password_widget = PasswordInput()

        assert password_widget is not None
        assert isinstance(password_widget, PasswordInput)
        assert password_widget.show_strength is True
        assert password_widget.strength_bar_height == 3
        assert password_widget.show_icon is not None
        assert password_widget.hide_icon is not None
        assert password_widget.icon_size == QSize(16, 16)

    def test_password_input_creation_with_parameters(self, qt_widget_cleanup) -> None:
        """Test creation with custom parameters."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.red)
        icon = QIcon(pixmap)

        password_widget = PasswordInput(
            show_strength=False,
            strength_bar_height=5,
            show_icon=icon,
            hide_icon=icon,
            icon_size=QSize(24, 24),
        )

        assert password_widget.show_strength is False
        assert password_widget.strength_bar_height == 5
        assert password_widget.show_icon is not None
        assert password_widget.hide_icon is not None
        assert password_widget.icon_size == QSize(24, 24)

    def test_password_input_properties(self, qt_widget_cleanup) -> None:
        """Test widget properties."""
        password_widget = PasswordInput()

        # Test password property
        password_widget.password = "test123"
        assert password_widget.password == "test123"

        # Test show_strength property
        password_widget.show_strength = False
        assert password_widget.show_strength is False

        # Test strength_bar_height property
        password_widget.strength_bar_height = 10
        assert password_widget.strength_bar_height == 10

        # Test show_icon property
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.blue)
        icon = QIcon(pixmap)
        password_widget.show_icon = icon
        assert password_widget.show_icon is not None

        # Test hide_icon property
        password_widget.hide_icon = icon
        assert password_widget.hide_icon is not None

        # Test icon_size property
        password_widget.icon_size = QSize(32, 32)
        assert password_widget.icon_size == QSize(32, 32)

    def test_password_input_toggle_password(self, qt_widget_cleanup) -> None:
        """Test toggle_password."""
        password_widget = PasswordInput()

        # Initial state (password hidden)
        initial_mode = password_widget._password_input.echoMode()

        # Toggle display
        password_widget.toggle_password()

        # Verify that the mode changed
        new_mode = password_widget._password_input.echoMode()
        assert new_mode != initial_mode

        # Toggle again
        password_widget.toggle_password()
        final_mode = password_widget._password_input.echoMode()
        assert final_mode == initial_mode

    def test_password_input_update_strength(self, qt_widget_cleanup) -> None:
        """Test update_strength."""
        password_widget = PasswordInput()

        # Test weak password
        password_widget.update_strength("weak")
        # Note: We can't easily verify the internal state
        # but we can verify that the method doesn't raise an exception

        # Test strong password
        password_widget.update_strength("StrongP@ss123!")
        # Method should not raise an exception

    def test_password_input_signals(self, qt_widget_cleanup) -> None:
        """Test widget signals."""
        password_widget = PasswordInput()

        # Test strengthChanged signal
        signal_received = False
        received_strength = 0

        def on_strength_changed(strength: int) -> None:
            nonlocal signal_received, received_strength
            signal_received = True
            received_strength = strength

        password_widget.strengthChanged.connect(on_strength_changed)

        # Simulate a strength change
        password_widget.update_strength("test123")

        # Verify that the signal is connected
        assert password_widget.strengthChanged is not None

        # Test iconClicked signal
        icon_signal_received = False

        def on_icon_clicked() -> None:
            nonlocal icon_signal_received
            icon_signal_received = True

        password_widget.iconClicked.connect(on_icon_clicked)

        # Verify that the signal is connected
        assert password_widget.iconClicked is not None

    def test_password_input_refresh_style(self, qt_widget_cleanup) -> None:
        """Test refresh_style."""
        password_widget = PasswordInput()

        # Method should not raise an exception
        try:
            password_widget.refresh_style()
        except Exception as e:
            pytest.fail(f"refresh_style() raised an exception: {e}")

    def test_password_input_password_validation(self, qt_widget_cleanup) -> None:
        """Test password validation."""
        password_widget = PasswordInput()

        # Test valid passwords
        valid_passwords = [
            "password",
            "Password123",
            "MyP@ssw0rd!",
            "12345678",
            "a" * 100,
        ]

        for password in valid_passwords:
            password_widget.password = password
            assert password_widget.password == password

        # Test empty password
        password_widget.password = ""
        assert password_widget.password == ""

    def test_password_input_icon_size_validation(self, qt_widget_cleanup) -> None:
        """Test icon size validation."""
        password_widget = PasswordInput()

        # Test valid sizes
        valid_sizes = [QSize(16, 16), QSize(24, 24), QSize(32, 32)]

        for size in valid_sizes:
            password_widget.icon_size = size
            assert password_widget.icon_size == size

    def test_password_input_strength_bar_height_validation(
        self, qt_widget_cleanup
    ) -> None:
        """Test strength bar height validation."""
        password_widget = PasswordInput()

        # Test valid heights
        valid_heights = [1, 3, 5, 10, 20]
        for height in valid_heights:
            password_widget.strength_bar_height = height
            assert password_widget.strength_bar_height == height

        # Test zero height (becomes 1)
        password_widget.strength_bar_height = 0
        assert password_widget.strength_bar_height == 1

        # Test negative height (becomes 1)
        password_widget.strength_bar_height = -5
        assert password_widget.strength_bar_height == 1

    def test_password_input_multiple_instances(self, qt_widget_cleanup) -> None:
        """Test with multiple instances."""
        password_widget1 = PasswordInput(show_strength=True)
        password_widget2 = PasswordInput(show_strength=False)

        # Test instance independence
        password_widget1.password = "password1"
        password_widget2.password = "password2"

        assert password_widget1.password == "password1"
        assert password_widget2.password == "password2"
        assert password_widget1.password != password_widget2.password

    def test_password_input_dynamic_property_changes(self, qt_widget_cleanup) -> None:
        """Test dynamic property changes."""
        password_widget = PasswordInput()

        # Test dynamic show_strength change
        password_widget.show_strength = False
        assert password_widget.show_strength is False

        password_widget.show_strength = True
        assert password_widget.show_strength is True

        # Test dynamic strength_bar_height change
        password_widget.strength_bar_height = 10
        assert password_widget.strength_bar_height == 10

        password_widget.strength_bar_height = 5
        assert password_widget.strength_bar_height == 5

    def test_password_input_special_characters(self, qt_widget_cleanup) -> None:
        """Test with special characters in password."""
        password_widget = PasswordInput()

        special_passwords = [
            "pass@word",
            "user-name_123",
            "file/path/pass",
            "pass with spaces",
            "pass\nwith\nnewlines",
            "pass\twith\ttabs",
            "pass with émojis 🚀",
            "pass with unicode: 你好世界",
        ]

        for password in special_passwords:
            password_widget.password = password
            assert password_widget.password == password

    def test_password_input_large_password(self, qt_widget_cleanup) -> None:
        """Test with very long password."""
        password_widget = PasswordInput()

        # Create a very long password
        long_password = "a" * 1000

        # Set the password
        password_widget.password = long_password

        # Verify that the password is correctly set
        assert password_widget.password == long_password

        # Verify that strength is calculated
        password_widget.update_strength(long_password)
        # Method should not raise an exception
