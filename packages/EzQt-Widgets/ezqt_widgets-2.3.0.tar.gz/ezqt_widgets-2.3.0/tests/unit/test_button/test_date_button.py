# ///////////////////////////////////////////////////////////////
# TEST_DATE_BUTTON - DateButton Widget Tests
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Unit tests for DateButton widget.

Tests for the date selection button widget with integrated calendar dialog.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
from unittest.mock import MagicMock, patch

# Third-party imports
import pytest
from PySide6.QtCore import QDate, QPoint, QSize, Qt
from PySide6.QtGui import QIcon, QMouseEvent
from PySide6.QtWidgets import QDialog

# Local imports
from ezqt_widgets.button.date_button import (
    DateButton,
    DatePickerDialog,
    format_date,
    get_calendar_icon,
    parse_date,
)

pytestmark = pytest.mark.unit

# ///////////////////////////////////////////////////////////////
# TEST CLASSES
# ///////////////////////////////////////////////////////////////


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_format_date_valid(self, qt_widget_cleanup) -> None:
        """Test format_date with a valid date."""
        date = QDate(2024, 1, 15)
        result = format_date(date, "dd/MM/yyyy")
        assert result == "15/01/2024"

    def test_format_date_invalid(self, qt_widget_cleanup) -> None:
        """Test format_date with an invalid date."""
        date = QDate()
        result = format_date(date, "dd/MM/yyyy")
        assert result == ""

    def test_format_date_custom_format(self, qt_widget_cleanup) -> None:
        """Test format_date with a custom format."""
        date = QDate(2024, 1, 15)
        result = format_date(date, "yyyy-MM-dd")
        assert result == "2024-01-15"

    def test_parse_date_valid(self, qt_widget_cleanup) -> None:
        """Test parse_date with a valid string."""
        result = parse_date("15/01/2024", "dd/MM/yyyy")
        assert result.isValid()
        assert result.year() == 2024
        assert result.month() == 1
        assert result.day() == 15

    def test_parse_date_invalid(self, qt_widget_cleanup) -> None:
        """Test parse_date with an invalid string."""
        result = parse_date("invalid", "dd/MM/yyyy")
        assert not result.isValid()

    def test_get_calendar_icon(self, qt_widget_cleanup) -> None:
        """Test get_calendar_icon."""
        icon = get_calendar_icon()
        assert icon is not None
        assert isinstance(icon, QIcon)
        assert not icon.isNull()


class TestDatePickerDialog:
    """Tests for DatePickerDialog class."""

    def test_date_picker_dialog_creation(self, qt_widget_cleanup) -> None:
        """Test dialog creation."""
        dialog = DatePickerDialog()
        assert dialog is not None
        assert isinstance(dialog, DatePickerDialog)

    def test_date_picker_dialog_with_date(self, qt_widget_cleanup) -> None:
        """Test creation with a date."""
        date = QDate(2024, 1, 15)
        dialog = DatePickerDialog(current_date=date)
        assert dialog.selected_date() == date

    def test_date_picker_dialog_selected_date(self, qt_widget_cleanup) -> None:
        """Test selected_date property."""
        dialog = DatePickerDialog()
        assert dialog.selected_date() is None


class TestDateButton:
    """Tests for DateButton class."""

    def test_date_button_creation_default(self, qt_widget_cleanup) -> None:
        """Test creation with default parameters."""
        button = DateButton()

        assert button is not None
        assert isinstance(button, DateButton)
        assert button.date_format == "dd/MM/yyyy"
        assert button.placeholder == "Select a date"
        assert button.show_calendar_icon is True
        assert button.icon_size == QSize(16, 16)

    def test_date_button_creation_with_parameters(self, qt_widget_cleanup) -> None:
        """Test creation with custom parameters."""
        date = QDate(2024, 1, 15)
        button = DateButton(
            date=date,
            date_format="yyyy-MM-dd",
            placeholder="Choose date",
            show_calendar_icon=False,
            icon_size=QSize(24, 24),
        )

        assert button.date == date
        assert button.date_format == "yyyy-MM-dd"
        assert button.placeholder == "Choose date"
        assert button.show_calendar_icon is False
        assert button.icon_size == QSize(24, 24)

    def test_date_button_creation_with_string_date(self, qt_widget_cleanup) -> None:
        """Test creation with a string date."""
        button = DateButton(date="15/01/2024")

        assert button.date.isValid()
        assert button.date.year() == 2024
        assert button.date.month() == 1
        assert button.date.day() == 15

    def test_date_button_properties(self, qt_widget_cleanup) -> None:
        """Test button properties."""
        button = DateButton()

        # Test date property
        date = QDate(2024, 1, 15)
        button.date = date
        assert button.date == date

        # Test date_string property
        button.date_string = "20/02/2024"
        assert button.date.year() == 2024
        assert button.date.month() == 2
        assert button.date.day() == 20

        # Test date_format property
        button.date_format = "yyyy-MM-dd"
        assert button.date_format == "yyyy-MM-dd"

        # Test placeholder property
        button.placeholder = "New placeholder"
        assert button.placeholder == "New placeholder"

        # Test show_calendar_icon property
        button.show_calendar_icon = False
        assert button.show_calendar_icon is False

        # Test icon_size property
        button.icon_size = QSize(32, 32)
        assert button.icon_size == QSize(32, 32)

    def test_date_button_signals(self, qt_widget_cleanup) -> None:
        """Test button signals."""
        button = DateButton()

        # Test dateChanged signal
        date = QDate(2024, 1, 15)

        signal_received = False

        def on_date_changed(new_date: QDate) -> None:
            nonlocal signal_received
            signal_received = True
            assert new_date == date

        button.dateChanged.connect(on_date_changed)
        button.date = date

        # Verify that the signal was emitted
        assert signal_received

    def test_date_button_methods(self, qt_widget_cleanup) -> None:
        """Test button methods."""
        button = DateButton()

        # Test clear_date
        button.date = QDate(2024, 1, 15)
        button.clear_date()
        assert not button.date.isValid()

        # Test set_today
        button.set_today()
        assert button.date.isValid()
        assert button.date == QDate.currentDate()

    @patch("ezqt_widgets.button.date_button.DatePickerDialog")
    def test_date_button_open_calendar(
        self, mock_dialog_class, qt_widget_cleanup
    ) -> None:
        """Test open_calendar method."""
        button = DateButton()

        # Mock the dialog
        mock_dialog = MagicMock()
        mock_dialog.selected_date.return_value = QDate(2024, 1, 15)
        mock_dialog_class.return_value = mock_dialog

        # Test calendar opening
        button.open_calendar()

        # Verify that the dialog was created and executed
        mock_dialog_class.assert_called_once()
        mock_dialog.exec.assert_called_once()

    def test_date_button_size_hints(self, qt_widget_cleanup) -> None:
        """Test size hint methods."""
        button = DateButton(text="Test Button")

        # Test sizeHint
        size_hint = button.sizeHint()
        assert size_hint is not None
        assert isinstance(size_hint, QSize)
        assert size_hint.width() > 0
        assert size_hint.height() > 0

        # Test minimumSizeHint
        min_size_hint = button.minimumSizeHint()
        assert min_size_hint is not None
        assert isinstance(min_size_hint, QSize)
        assert min_size_hint.width() > 0
        assert min_size_hint.height() > 0

    def test_date_button_refresh_style(self, qt_widget_cleanup) -> None:
        """Test refresh_style method."""
        button = DateButton()

        # Method should not raise an exception
        try:
            button.refresh_style()
        except Exception as e:
            pytest.fail(f"refresh_style() raised an exception: {e}")

    def test_date_button_minimum_dimensions(self, qt_widget_cleanup) -> None:
        """Test minimum dimensions."""
        button = DateButton(min_width=150, min_height=50)

        assert button.min_width == 150
        assert button.min_height == 50

        # Modify dimensions
        button.min_width = 200
        button.min_height = 75

        assert button.min_width == 200
        assert button.min_height == 75

        # Test with None
        button.min_width = None
        button.min_height = None

        assert button.min_width is None
        assert button.min_height is None

    @patch("ezqt_widgets.button.date_button.DatePickerDialog")
    def test_date_button_mouse_press_event(
        self, mock_dialog_class, qt_widget_cleanup
    ) -> None:
        """Test mousePressEvent."""
        button = DateButton()

        # Mock the dialog to avoid blocking
        mock_dialog = MagicMock()
        mock_dialog.selected_date.return_value = QDate(2024, 1, 15)
        mock_dialog.exec.return_value = QDialog.DialogCode.Accepted
        mock_dialog_class.return_value = mock_dialog

        # Create a real Qt mouse event
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(10, 10),
            QPoint(10, 10),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        # Test that the event does not raise an exception
        try:
            button.mousePressEvent(event)
        except Exception as e:
            pytest.fail(f"mousePressEvent() raised an exception: {e}")

        # Verify that the dialog was created and executed
        mock_dialog_class.assert_called_once()
        mock_dialog.exec.assert_called_once()

    def test_date_button_display_with_date(self, qt_widget_cleanup) -> None:
        """Test display with a date."""
        date = QDate(2024, 1, 15)
        button = DateButton(date=date)

        # Verify that the date is displayed
        assert button.date_string == "15/01/2024"

    def test_date_button_display_without_date(self, qt_widget_cleanup) -> None:
        """Test display without a date."""
        button = DateButton()

        # Verify that the widget displays a date
        # Note: DateButton initializes with current date by default
        assert button.date_string != ""
        assert button.date.isValid()

        # Clear the date
        button.clear_date()

        # Verify that the date is cleared
        # Note: clear_date() sets an invalid QDate, so date_string returns ""
        assert button.date_string == ""
        assert not button.date.isValid()

        # Verify that the label displays the placeholder
        # The internal label should display the placeholder
        assert button.date_label.text() == button.placeholder

    def test_date_button_custom_format(self, qt_widget_cleanup) -> None:
        """Test with a custom format."""
        date = QDate(2024, 1, 15)
        button = DateButton(date=date, date_format="yyyy-MM-dd")

        # Verify that the format is applied
        assert button.date_string == "2024-01-15"
