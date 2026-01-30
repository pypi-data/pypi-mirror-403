# ///////////////////////////////////////////////////////////////
# DATE_BUTTON - Date Selection Button Widget
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Date button widget module.

Provides a button widget with integrated calendar dialog for date selection
in PySide6 applications.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
from PySide6.QtCore import QDate, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QMouseEvent, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCalendarWidget,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
)

# ///////////////////////////////////////////////////////////////
# UTILITY FUNCTIONS
# ///////////////////////////////////////////////////////////////


def format_date(date: QDate, format_str: str = "dd/MM/yyyy") -> str:
    """Format a QDate object to string.

    Args:
        date: The date to format.
        format_str: Format string (default: "dd/MM/yyyy").

    Returns:
        Formatted date string, or empty string if date is invalid.
    """
    if not date.isValid():
        return ""
    return date.toString(format_str)


def parse_date(date_str: str, format_str: str = "dd/MM/yyyy") -> QDate:
    """Parse a date string to QDate object.

    Args:
        date_str: The date string to parse.
        format_str: Format string (default: "dd/MM/yyyy").

    Returns:
        Parsed QDate object or invalid QDate if parsing fails.
    """
    return QDate.fromString(date_str, format_str)


def get_calendar_icon() -> QIcon:
    """Get a default calendar icon.

    Returns:
        QIcon: Calendar icon pixmap.
    """
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setPen(QColor("#666666"))
    painter.setBrush(QColor("#f0f0f0"))
    painter.drawRect(0, 0, 15, 15)
    painter.setPen(QColor("#333333"))
    painter.drawText(2, 2, 12, 12, Qt.AlignmentFlag.AlignCenter, "📅")
    painter.end()
    return QIcon(pixmap)


# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class DatePickerDialog(QDialog):
    """Dialog for date selection with calendar widget.

    Provides a modal dialog with a calendar widget for selecting dates.
    The dialog emits accepted signal when a date is selected and confirmed.

    Args:
        parent: The parent widget (default: None).
        current_date: The current selected date (default: None).
    """

    def __init__(self, parent=None, current_date: QDate | None = None) -> None:
        """Initialize the date picker dialog."""
        super().__init__(parent)

        # ///////////////////////////////////////////////////////////////
        # INIT
        # ///////////////////////////////////////////////////////////////

        self._selected_date: QDate | None = current_date

        # ///////////////////////////////////////////////////////////////
        # SETUP UI
        # ///////////////////////////////////////////////////////////////

        self._setup_ui()

        # Set current date if provided
        if current_date and current_date.isValid():
            self._calendar.setSelectedDate(current_date)

    # ------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        self.setWindowTitle("Select a date")
        self.setModal(True)
        self.setFixedSize(300, 250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self._calendar = QCalendarWidget(self)
        self._calendar.clicked.connect(self._on_date_selected)
        layout.addWidget(self._calendar)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        ok_button = QPushButton("OK", self)
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)

        self._calendar.activated.connect(self.accept)

    def _on_date_selected(self, date: QDate) -> None:
        """Handle date selection from calendar.

        Args:
            date: The selected date from the calendar.
        """
        self._selected_date = date

    # ------------------------------------------------
    # PUBLIC METHODS
    # ------------------------------------------------

    def selected_date(self) -> QDate | None:
        """Get the selected date.

        Returns:
            The selected date, or None if no date was selected.
        """
        return self._selected_date


class DateButton(QToolButton):
    """Button widget for date selection with integrated calendar.

    Features:
        - Displays current selected date
        - Opens calendar dialog on click
        - Configurable date format
        - Placeholder text when no date selected
        - Calendar icon with customizable appearance
        - Date validation and parsing

    Args:
        parent: The parent widget (default: None).
        date: Initial date (QDate, date string, or None for current date).
        date_format: Format for displaying the date (default: "dd/MM/yyyy").
        placeholder: Text to display when no date is selected
            (default: "Select a date").
        show_calendar_icon: Whether to show calendar icon (default: True).
        icon_size: Size of the calendar icon (default: QSize(16, 16)).
        min_width: Minimum width of the button (default: None, auto-calculated).
        min_height: Minimum height of the button (default: None, auto-calculated).
        *args: Additional arguments passed to QToolButton.
        **kwargs: Additional keyword arguments passed to QToolButton.

    Signals:
        dateChanged(QDate): Emitted when the date changes.
        dateSelected(QDate): Emitted when a date is selected from calendar.
    """

    dateChanged = Signal(QDate)
    dateSelected = Signal(QDate)

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        parent=None,
        date: QDate | str | None = None,
        date_format: str = "dd/MM/yyyy",
        placeholder: str = "Select a date",
        show_calendar_icon: bool = True,
        icon_size: QSize | tuple[int, int] = QSize(16, 16),
        min_width: int | None = None,
        min_height: int | None = None,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the date button."""
        super().__init__(parent, *args, **kwargs)
        self.setProperty("type", "DateButton")

        # Initialize properties
        self._date_format: str = date_format
        self._placeholder: str = placeholder
        self._show_calendar_icon: bool = show_calendar_icon
        self._icon_size: QSize = (
            QSize(*icon_size)
            if isinstance(icon_size, (tuple, list))
            else QSize(icon_size)
        )
        self._min_width: int | None = min_width
        self._min_height: int | None = min_height
        self._current_date: QDate = QDate()

        # Setup UI components
        self.date_label = QLabel()
        self.icon_label = QLabel()

        # Configure labels
        self.date_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.date_label.setStyleSheet("background-color: transparent;")

        # Setup layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.date_label)
        layout.addStretch()  # Push icon to the right
        layout.addWidget(self.icon_label)

        # Configure size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Set initial values
        if date:
            self.date = date
        else:
            self.date = QDate.currentDate()

        self.show_calendar_icon = show_calendar_icon
        self._update_display()

    # ///////////////////////////////////////////////////////////////
    # PROPERTIES
    # ///////////////////////////////////////////////////////////////

    @property
    def date(self) -> QDate:
        """Get or set the selected date.

        Returns:
            The current selected date.
        """
        return self._current_date

    @date.setter
    def date(self, value: QDate | str | None) -> None:
        """Set the date from QDate, string, or None.

        Args:
            value: The date to set (QDate, string, or None).
        """
        if isinstance(value, str):
            new_date = parse_date(value, self._date_format)
        elif isinstance(value, QDate):
            new_date = value
        elif value is None:
            new_date = QDate()
        else:
            raise TypeError(f"Invalid date value: {value}")

        if new_date != self._current_date:
            self._current_date = new_date
            self._update_display()
            self.dateChanged.emit(self._current_date)

    @property
    def date_string(self) -> str:
        """Get or set the date as formatted string.

        Returns:
            The formatted date string.
        """
        return format_date(self._current_date, self._date_format)

    @date_string.setter
    def date_string(self, value: str) -> None:
        """Set the date from a formatted string.

        Args:
            value: The formatted date string.
        """
        self.date = value

    @property
    def date_format(self) -> str:
        """Get or set the date format.

        Returns:
            The current date format string.
        """
        return self._date_format

    @date_format.setter
    def date_format(self, value: str) -> None:
        """Set the date format.

        Args:
            value: The new date format string.
        """
        self._date_format = str(value)
        self._update_display()

    @property
    def placeholder(self) -> str:
        """Get or set the placeholder text.

        Returns:
            The current placeholder text.
        """
        return self._placeholder

    @placeholder.setter
    def placeholder(self, value: str) -> None:
        """Set the placeholder text.

        Args:
            value: The new placeholder text.
        """
        self._placeholder = str(value)
        self._update_display()

    @property
    def show_calendar_icon(self) -> bool:
        """Get or set calendar icon visibility.

        Returns:
            True if calendar icon is visible, False otherwise.
        """
        return self._show_calendar_icon

    @show_calendar_icon.setter
    def show_calendar_icon(self, value: bool) -> None:
        """Set calendar icon visibility.

        Args:
            value: Whether to show the calendar icon.
        """
        self._show_calendar_icon = bool(value)
        if self._show_calendar_icon:
            self.icon_label.show()
            self.icon_label.setPixmap(get_calendar_icon().pixmap(self._icon_size))
            self.icon_label.setFixedSize(self._icon_size)
        else:
            self.icon_label.hide()

    @property
    def icon_size(self) -> QSize:
        """Get or set the icon size.

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
        self._icon_size = (
            QSize(*value) if isinstance(value, (tuple, list)) else QSize(value)
        )
        if self._show_calendar_icon:
            self.icon_label.setPixmap(get_calendar_icon().pixmap(self._icon_size))
            self.icon_label.setFixedSize(self._icon_size)

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

    def clear_date(self) -> None:
        """Clear the selected date."""
        self.date = None

    def set_today(self) -> None:
        """Set the date to today."""
        self.date = QDate.currentDate()

    def open_calendar(self) -> None:
        """Open the calendar dialog."""
        dialog = DatePickerDialog(self, self._current_date)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_date = dialog.selected_date()
            if selected_date and selected_date.isValid():
                self.date = selected_date
                self.dateSelected.emit(selected_date)

    # ------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------

    def _update_display(self) -> None:
        """Update the display text."""
        if self._current_date.isValid():
            display_text = format_date(self._current_date, self._date_format)
        else:
            display_text = self._placeholder

        self.date_label.setText(display_text)

    # ///////////////////////////////////////////////////////////////
    # EVENT HANDLERS
    # ///////////////////////////////////////////////////////////////

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events.

        Args:
            event: The mouse event.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_calendar()
        super().mousePressEvent(event)

    # ///////////////////////////////////////////////////////////////
    # OVERRIDE METHODS
    # ///////////////////////////////////////////////////////////////

    def sizeHint(self) -> QSize:
        """Get the recommended size for the button.

        Returns:
            The recommended size.
        """
        return QSize(150, 30)

    def minimumSizeHint(self) -> QSize:
        """Get the minimum size hint for the button.

        Returns:
            The minimum size hint.
        """
        base_size = super().minimumSizeHint()

        text_width = self.date_label.fontMetrics().horizontalAdvance(
            self.date_string if self._current_date.isValid() else self._placeholder
        )

        icon_width = self._icon_size.width() if self._show_calendar_icon else 0

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
