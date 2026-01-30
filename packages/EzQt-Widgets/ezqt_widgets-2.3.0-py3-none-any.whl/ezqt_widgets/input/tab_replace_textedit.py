# ///////////////////////////////////////////////////////////////
# TAB_REPLACE_TEXTEDIT - Tab Replace Text Edit Widget
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Tab replace text edit widget module.

Provides a QPlainTextEdit subclass that sanitizes pasted text by replacing
tab characters according to the chosen mode and removing empty lines for
PySide6 applications.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QKeySequence
from PySide6.QtWidgets import QApplication, QPlainTextEdit

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class TabReplaceTextEdit(QPlainTextEdit):
    """QPlainTextEdit subclass with tab replacement and text sanitization.

    Sanitizes pasted text by replacing tab characters according to the
    chosen mode and removing empty lines. Useful for pasting tabular data
    or ensuring clean input.

    Args:
        parent: The parent widget (default: None).
        tab_replacement: The string to replace tab characters with
            (default: "\\n").
        sanitize_on_paste: Whether to sanitize pasted text (default: True).
        remove_empty_lines: Whether to remove empty lines during sanitization
            (default: True).
        preserve_whitespace: Whether to preserve leading/trailing whitespace
            (default: False).
        *args: Additional arguments passed to QPlainTextEdit.
        **kwargs: Additional keyword arguments passed to QPlainTextEdit.

    Properties:
        tab_replacement: Get or set the string used to replace tab characters.
        sanitize_on_paste: Enable or disable sanitizing pasted text.
        remove_empty_lines: Get or set whether to remove empty lines.
        preserve_whitespace: Get or set whether to preserve whitespace.
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        parent=None,
        tab_replacement: str = "\n",
        sanitize_on_paste: bool = True,
        remove_empty_lines: bool = True,
        preserve_whitespace: bool = False,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the tab replace text edit."""
        super().__init__(parent, *args, **kwargs)

        # Set widget type property
        self.setProperty("type", "TabReplaceTextEdit")

        # Initialize properties
        self._tab_replacement: str = tab_replacement
        self._sanitize_on_paste: bool = sanitize_on_paste
        self._remove_empty_lines: bool = remove_empty_lines
        self._preserve_whitespace: bool = preserve_whitespace

    # ///////////////////////////////////////////////////////////////
    # PROPERTIES
    # ///////////////////////////////////////////////////////////////

    @property
    def tab_replacement(self) -> str:
        """Get the string used to replace tab characters.

        Returns:
            The current tab replacement string.
        """
        return self._tab_replacement

    @tab_replacement.setter
    def tab_replacement(self, value: str) -> None:
        """Set the string used to replace tab characters.

        Args:
            value: The new tab replacement string.
        """
        self._tab_replacement = str(value)

    @property
    def sanitize_on_paste(self) -> bool:
        """Get whether sanitizing pasted text is enabled.

        Returns:
            True if sanitization is enabled, False otherwise.
        """
        return self._sanitize_on_paste

    @sanitize_on_paste.setter
    def sanitize_on_paste(self, value: bool) -> None:
        """Set whether sanitizing pasted text is enabled.

        Args:
            value: Whether to enable sanitization.
        """
        self._sanitize_on_paste = bool(value)

    @property
    def remove_empty_lines(self) -> bool:
        """Get whether empty lines are removed.

        Returns:
            True if empty lines are removed, False otherwise.
        """
        return self._remove_empty_lines

    @remove_empty_lines.setter
    def remove_empty_lines(self, value: bool) -> None:
        """Set whether empty lines are removed.

        Args:
            value: Whether to remove empty lines.
        """
        self._remove_empty_lines = bool(value)

    @property
    def preserve_whitespace(self) -> bool:
        """Get whether whitespace is preserved.

        Returns:
            True if whitespace is preserved, False otherwise.
        """
        return self._preserve_whitespace

    @preserve_whitespace.setter
    def preserve_whitespace(self, value: bool) -> None:
        """Set whether whitespace is preserved.

        Args:
            value: Whether to preserve whitespace.
        """
        self._preserve_whitespace = bool(value)

    # ///////////////////////////////////////////////////////////////
    # PUBLIC METHODS
    # ///////////////////////////////////////////////////////////////

    def sanitize_text(self, text: str) -> str:
        """Sanitize text by replacing tabs and optionally removing empty lines.

        Args:
            text: The text to sanitize.

        Returns:
            The sanitized text.
        """
        # Replace tabs
        sanitized = text.replace("\t", self._tab_replacement)

        if self._remove_empty_lines:
            # Split into lines
            lines = sanitized.split("\n")

            # Filter empty lines
            if self._preserve_whitespace:
                # Keep lines with whitespace
                lines = [line for line in lines if line.strip() or line]
            else:
                # Remove all empty lines but preserve whitespace
                lines = [line for line in lines if line.strip()]

            # Rejoin lines
            sanitized = "\n".join(lines)

        return sanitized

    # ///////////////////////////////////////////////////////////////
    # EVENT HANDLERS
    # ///////////////////////////////////////////////////////////////

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events.

        Overridden method from QPlainTextEdit. Modifies the behavior of
        the paste operation and tab key handling.

        Args:
            event: The key event.
        """
        # Handle tab key
        if event.key() == Qt.Key.Key_Tab:
            # Insert tab replacement
            cursor = self.textCursor()
            cursor.insertText(self._tab_replacement)
            event.accept()
            return

        # Handle paste
        if self._sanitize_on_paste and event.matches(QKeySequence.StandardKey.Paste):
            # Get clipboard text
            clipboard = QApplication.clipboard()
            text = clipboard.text()

            # Sanitize text
            text = self.sanitize_text(text)

            # Insert sanitized text
            self.insertPlainText(text)
            event.accept()
            return

        # Default behavior
        super().keyPressEvent(event)

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
