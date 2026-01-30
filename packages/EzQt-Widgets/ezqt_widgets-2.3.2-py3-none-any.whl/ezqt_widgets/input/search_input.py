# ///////////////////////////////////////////////////////////////
# SEARCH_INPUT - Search Input Widget
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Search input widget module.

Provides a QLineEdit subclass for search input with integrated history
and optional search icon for PySide6 applications.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QKeyEvent
from PySide6.QtWidgets import QLineEdit

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class SearchInput(QLineEdit):
    """QLineEdit subclass for search input with integrated history.

    Features:
        - Maintains a history of submitted searches
        - Navigate history with up/down arrows
        - Emits a searchSubmitted(str) signal on validation (Enter)
        - Optional search icon (left or right)
        - Optional clear button

    Args:
        parent: The parent widget (default: None).
        max_history: Maximum number of history entries to keep
            (default: 20).
        search_icon: Icon to display as search icon
            (QIcon, str, or None, default: None).
        icon_position: Icon position, 'left' or 'right' (default: 'left').
        clear_button: Whether to show a clear button (default: True).
        *args: Additional arguments passed to QLineEdit.
        **kwargs: Additional keyword arguments passed to QLineEdit.

    Properties:
        search_icon: Get or set the search icon.
        icon_position: Get or set the icon position ('left' or 'right').
        clear_button: Get or set whether the clear button is shown.
        max_history: Get or set the maximum history size.

    Signals:
        searchSubmitted(str): Emitted when a search is submitted (Enter key).
    """

    searchSubmitted = Signal(str)

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        parent=None,
        max_history: int = 20,
        search_icon: QIcon | str | None = None,
        icon_position: str = "left",
        clear_button: bool = True,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the search input."""
        super().__init__(parent, *args, **kwargs)

        # Initialize properties
        self._search_icon: QIcon | None = None
        self._icon_position: str = icon_position
        self._clear_button: bool = clear_button
        self._history: list[str] = []
        self._history_index: int = -1
        self._max_history: int = max_history
        self._current_text: str = ""

        # Setup UI
        self._setup_ui()

        # Set icon if provided
        if search_icon:
            # Setter accepts QIcon | str | None, but mypy sees property return type
            self.search_icon = search_icon

    # ------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------

    def _setup_ui(self) -> None:
        """Setup the user interface components."""
        self.setPlaceholderText("Search...")
        self.setClearButtonEnabled(self._clear_button)

    # ///////////////////////////////////////////////////////////////
    # PROPERTIES
    # ///////////////////////////////////////////////////////////////

    @property
    def search_icon(self) -> QIcon | None:
        """Get the search icon.

        Returns:
            The current search icon, or None if not set.
        """
        return self._search_icon

    @search_icon.setter
    def search_icon(self, value: QIcon | str | None) -> None:
        """Set the search icon.

        Args:
            value: The icon source (QIcon, path string, or None).
        """
        if isinstance(value, str):
            # Load icon from path
            self._search_icon = QIcon(value)
        else:
            self._search_icon = value

        # Update display
        if self._search_icon:
            self.setStyleSheet(f"""
                QLineEdit {{
                    padding-{self._icon_position}: 20px;
                }}
            """)
        else:
            self.setStyleSheet("")

    @property
    def icon_position(self) -> str:
        """Get the icon position.

        Returns:
            The current icon position ('left' or 'right').
        """
        return self._icon_position

    @icon_position.setter
    def icon_position(self, value: str) -> None:
        """Set the icon position.

        Args:
            value: The icon position ('left' or 'right').
        """
        if value in ["left", "right"]:
            self._icon_position = value
            # Update icon display
            if self._search_icon:
                self.search_icon = self._search_icon

    @property
    def clear_button(self) -> bool:
        """Get whether the clear button is shown.

        Returns:
            True if clear button is shown, False otherwise.
        """
        return self._clear_button

    @clear_button.setter
    def clear_button(self, value: bool) -> None:
        """Set whether the clear button is shown.

        Args:
            value: Whether to show the clear button.
        """
        self._clear_button = bool(value)
        self.setClearButtonEnabled(self._clear_button)

    @property
    def max_history(self) -> int:
        """Get the maximum history size.

        Returns:
            The maximum number of history entries.
        """
        return self._max_history

    @max_history.setter
    def max_history(self, value: int) -> None:
        """Set the maximum history size.

        Args:
            value: The maximum number of history entries.
        """
        self._max_history = max(1, int(value))
        self._trim_history()

    # ///////////////////////////////////////////////////////////////
    # PUBLIC METHODS
    # ///////////////////////////////////////////////////////////////

    def add_to_history(self, text: str) -> None:
        """Add a search term to history.

        Args:
            text: The search term to add.
        """
        if not text.strip():
            return

        # Remove if already exists
        if text in self._history:
            self._history.remove(text)

        # Add to beginning
        self._history.insert(0, text)
        self._trim_history()
        self._history_index = -1

    def get_history(self) -> list[str]:
        """Get the search history.

        Returns:
            A copy of the search history list.
        """
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear the search history."""
        self._history.clear()
        self._history_index = -1

    def set_history(self, history_list: list[str]) -> None:
        """Set the search history.

        Args:
            history_list: List of history entries to set.
        """
        self._history = [
            str(item).strip() for item in history_list if str(item).strip()
        ]
        self._trim_history()
        self._history_index = -1

    # ------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------

    def _trim_history(self) -> None:
        """Trim history to maximum size."""
        while len(self._history) > self._max_history:
            self._history.pop()

    # ///////////////////////////////////////////////////////////////
    # EVENT HANDLERS
    # ///////////////////////////////////////////////////////////////

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events.

        Args:
            event: The key event.
        """
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Submit search
            text = self.text().strip()
            if text:
                self.add_to_history(text)
                self.searchSubmitted.emit(text)
        elif event.key() == Qt.Key.Key_Up:
            # Navigate history up
            if self._history:
                if self._history_index < len(self._history) - 1:
                    self._history_index += 1
                    self.setText(self._history[self._history_index])
                event.accept()
                return
        elif event.key() == Qt.Key.Key_Down:
            # Navigate history down
            if self._history_index > 0:
                self._history_index -= 1
                self.setText(self._history[self._history_index])
                event.accept()
                return
            elif self._history_index == 0:
                self._history_index = -1
                self.setText(self._current_text)
                event.accept()
                return

        # Store current text for history navigation
        if event.key() not in [Qt.Key.Key_Up, Qt.Key.Key_Down]:
            self._current_text = self.text()

        super().keyPressEvent(event)

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
