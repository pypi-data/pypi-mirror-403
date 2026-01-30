# ///////////////////////////////////////////////////////////////
# AUTO_COMPLETE_INPUT - Auto-Complete Input Widget
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Auto-complete input widget module.

Provides a QLineEdit subclass with autocompletion support for PySide6
applications.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
from PySide6.QtCore import QStringListModel, Qt
from PySide6.QtWidgets import QCompleter, QLineEdit

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class AutoCompleteInput(QLineEdit):
    """QLineEdit subclass with autocompletion support.

    Provides a text input widget with autocompletion functionality.
    You can provide a list of suggestions (strings) to be used for
    autocompletion.

    Args:
        parent: The parent widget (default: None).
        suggestions: List of strings to use for autocompletion
            (default: empty list).
        case_sensitive: Whether the autocompletion is case sensitive
            (default: False).
        filter_mode: Filter mode for completion
            (default: Qt.MatchFlag.MatchContains).
        completion_mode: Completion mode
            (default: QCompleter.CompletionMode.PopupCompletion).
        *args: Additional arguments passed to QLineEdit.
        **kwargs: Additional keyword arguments passed to QLineEdit.

    Properties:
        suggestions: Get or set the list of suggestions for autocompletion.
        case_sensitive: Get or set whether autocompletion is case sensitive.
        filter_mode: Get or set the filter mode for completion.
        completion_mode: Get or set the completion mode.
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        parent=None,
        suggestions: list[str] | None = None,
        case_sensitive: bool = False,
        filter_mode: Qt.MatchFlag = Qt.MatchFlag.MatchContains,
        completion_mode: QCompleter.CompletionMode = QCompleter.CompletionMode.PopupCompletion,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the auto-complete input."""
        super().__init__(parent, *args, **kwargs)

        # Initialize properties
        self._suggestions: list[str] = suggestions or []
        self._case_sensitive: bool = case_sensitive
        self._filter_mode: Qt.MatchFlag = filter_mode
        self._completion_mode: QCompleter.CompletionMode = completion_mode

        # Setup completer
        self._setup_completer()

    # ------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------

    def _setup_completer(self) -> None:
        """Setup the completer with current settings."""
        self._completer = QCompleter(self)
        self._model = QStringListModel(self._suggestions, self)

        # Configure completer
        self._completer.setModel(self._model)
        self._completer.setCaseSensitivity(
            Qt.CaseSensitivity.CaseSensitive
            if self._case_sensitive
            else Qt.CaseSensitivity.CaseInsensitive
        )
        self._completer.setFilterMode(self._filter_mode)
        self._completer.setCompletionMode(self._completion_mode)
        self.setCompleter(self._completer)

    # ///////////////////////////////////////////////////////////////
    # PROPERTIES
    # ///////////////////////////////////////////////////////////////

    @property
    def suggestions(self) -> list[str]:
        """Get the list of suggestions.

        Returns:
            A copy of the current suggestions list.
        """
        return self._suggestions.copy()

    @suggestions.setter
    def suggestions(self, value: list[str]) -> None:
        """Set the list of suggestions.

        Args:
            value: The new list of suggestions.
        """
        self._suggestions = value or []
        self._model.setStringList(self._suggestions)

    @property
    def case_sensitive(self) -> bool:
        """Get whether autocompletion is case sensitive.

        Returns:
            True if case sensitive, False otherwise.
        """
        return self._case_sensitive

    @case_sensitive.setter
    def case_sensitive(self, value: bool) -> None:
        """Set whether autocompletion is case sensitive.

        Args:
            value: Whether to enable case sensitivity.
        """
        self._case_sensitive = bool(value)
        self._completer.setCaseSensitivity(
            Qt.CaseSensitivity.CaseSensitive
            if self._case_sensitive
            else Qt.CaseSensitivity.CaseInsensitive
        )

    @property
    def filter_mode(self) -> Qt.MatchFlag:
        """Get the filter mode for completion.

        Returns:
            The current filter mode.
        """
        return self._filter_mode

    @filter_mode.setter
    def filter_mode(self, value: Qt.MatchFlag) -> None:
        """Set the filter mode for completion.

        Args:
            value: The new filter mode.
        """
        self._filter_mode = value
        self._completer.setFilterMode(self._filter_mode)

    @property
    def completion_mode(self) -> QCompleter.CompletionMode:
        """Get the completion mode.

        Returns:
            The current completion mode.
        """
        return self._completion_mode

    @completion_mode.setter
    def completion_mode(self, value: QCompleter.CompletionMode) -> None:
        """Set the completion mode.

        Args:
            value: The new completion mode.
        """
        self._completion_mode = value
        self._completer.setCompletionMode(self._completion_mode)

    # ///////////////////////////////////////////////////////////////
    # PUBLIC METHODS
    # ///////////////////////////////////////////////////////////////

    def add_suggestion(self, suggestion: str) -> None:
        """Add a suggestion to the list.

        Args:
            suggestion: The suggestion string to add.
        """
        if suggestion and suggestion not in self._suggestions:
            self._suggestions.append(suggestion)
            self._model.setStringList(self._suggestions)

    def remove_suggestion(self, suggestion: str) -> None:
        """Remove a suggestion from the list.

        Args:
            suggestion: The suggestion string to remove.
        """
        if suggestion in self._suggestions:
            self._suggestions.remove(suggestion)
            self._model.setStringList(self._suggestions)

    def clear_suggestions(self) -> None:
        """Clear all suggestions."""
        self._suggestions.clear()
        self._model.setStringList(self._suggestions)

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
