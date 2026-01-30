#!/usr/bin/env python3
# ///////////////////////////////////////////////////////////////
# INPUT EXAMPLE - EzQt Widgets
# Demonstration of input widgets
# ///////////////////////////////////////////////////////////////

"""
Input widgets usage examples for EzQt Widgets.

This script demonstrates the usage of all available input widget types:
    - TabReplaceTextEdit: Text editor with tab replacement
    - AutoCompleteInput: Text field with autocompletion
    - SearchInput: Search field with history management

Example:
    Run this script directly to see the input widgets in action::

        $ python input_example.py
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import os
import re
import sys

# Third-party imports
import yaml
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

# Local imports
from ezqt_widgets.input import (
    AutoCompleteInput,
    SearchInput,
    TabReplaceTextEdit,
)

# ///////////////////////////////////////////////////////////////
# UTILITY FUNCTIONS
# ///////////////////////////////////////////////////////////////


def load_and_apply_qss(
    app: QApplication,
    qss_path: str,
    yaml_path: str,
    theme_name: str = "dark",
) -> None:
    """
    Load and apply QSS stylesheet with theme variables.

    Args:
        app: The QApplication instance.
        qss_path: Path to the QSS stylesheet file.
        yaml_path: Path to the YAML theme configuration file.
        theme_name: Name of the theme to apply. Defaults to "dark".
    """
    try:
        # Load theme variables from YAML
        with open(yaml_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        theme_vars = config["theme_palette"][theme_name]

        # Load QSS stylesheet
        with open(qss_path, encoding="utf-8") as f:
            qss = f.read()

        # Replace $ variables with their values
        def repl(match: re.Match[str]) -> str:
            var = match.group(0)
            return str(theme_vars.get(var, var))

        qss = re.sub(r"\$_[a-zA-Z0-9_]+", repl, qss)
        app.setStyleSheet(qss)
        print(f"Theme '{theme_name}' loaded successfully")

    except Exception as e:
        print(f"Error loading theme: {e}")
        # Apply default style on error
        app.setStyleSheet("")


# ///////////////////////////////////////////////////////////////
# INPUT EXAMPLE WIDGET
# ///////////////////////////////////////////////////////////////


class InputExampleWidget(QWidget):
    """
    Demonstration widget for all input types.

    This widget showcases the functionality of TabReplaceTextEdit,
    AutoCompleteInput, and SearchInput widgets with interactive examples.

    Attributes:
        tab_replace_textedit: TabReplaceTextEdit widget for text editing.
        autocomplete_input: AutoCompleteInput widget with suggestions.
        search_input: SearchInput widget for search functionality.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the InputExampleWidget.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Input Examples - EzQt Widgets")
        self.setMinimumSize(800, 700)
        self._setup_ui()

    # -----------------------------------------------------------
    # UI Setup
    # -----------------------------------------------------------

    def _setup_ui(self) -> None:
        """Configure the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create ScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        # Content container widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Input Examples - EzQt Widgets")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        content_layout.addWidget(title)

        # Add widget groups
        self._setup_tab_replace_group(content_layout)
        self._setup_autocomplete_group(content_layout)
        self._setup_search_group(content_layout)
        self._setup_test_buttons_group(content_layout)

        # Bottom spacing
        content_layout.addStretch()

        # Configure ScrollArea
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def _setup_tab_replace_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the TabReplaceTextEdit group.

        Args:
            layout: Parent layout to add the group to.
        """
        tab_replace_group = QGroupBox("TabReplaceTextEdit")
        tab_replace_layout = QVBoxLayout(tab_replace_group)

        tab_replace_label = QLabel("Text editor with tab replacement:")
        tab_replace_layout.addWidget(tab_replace_label)

        self.tab_replace_textedit = TabReplaceTextEdit()
        self.tab_replace_textedit.setPlaceholderText(
            "Type here... Tabs will be replaced with spaces."
        )
        self.tab_replace_textedit.setMaximumHeight(100)
        self.tab_replace_textedit.textChanged.connect(self._on_tab_replace_changed)
        tab_replace_layout.addWidget(self.tab_replace_textedit)

        self.tab_replace_output = QLabel("Characters: 0")
        self.tab_replace_output.setStyleSheet("font-weight: bold; color: #4CAF50;")
        tab_replace_layout.addWidget(self.tab_replace_output)

        layout.addWidget(tab_replace_group)

    def _setup_autocomplete_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the AutoCompleteInput group.

        Args:
            layout: Parent layout to add the group to.
        """
        autocomplete_group = QGroupBox("AutoCompleteInput")
        autocomplete_layout = QVBoxLayout(autocomplete_group)

        autocomplete_label = QLabel("Input field with autocompletion:")
        autocomplete_layout.addWidget(autocomplete_label)

        # Suggestions for autocompletion
        suggestions = [
            "Python",
            "JavaScript",
            "Java",
            "C++",
            "C#",
            "PHP",
            "Ruby",
            "Go",
            "Rust",
            "Swift",
        ]

        self.autocomplete_input = AutoCompleteInput()
        self.autocomplete_input.setPlaceholderText(
            "Type 'Py' or 'Ja' to see suggestions..."
        )
        self.autocomplete_input.suggestions = suggestions
        self.autocomplete_input.textChanged.connect(self._on_autocomplete_changed)
        autocomplete_layout.addWidget(self.autocomplete_input)

        self.autocomplete_output = QLabel("Text entered: ")
        self.autocomplete_output.setStyleSheet("font-weight: bold; color: #2196F3;")
        autocomplete_layout.addWidget(self.autocomplete_output)

        layout.addWidget(autocomplete_group)

    def _setup_search_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the SearchInput group.

        Args:
            layout: Parent layout to add the group to.
        """
        search_group = QGroupBox("SearchInput")
        search_layout = QVBoxLayout(search_group)

        search_label = QLabel("Search field with validation:")
        search_layout.addWidget(search_label)

        self.search_input = SearchInput()
        self.search_input.setPlaceholderText("Type to search and press Enter...")
        self.search_input.searchSubmitted.connect(self._on_search_triggered)
        search_layout.addWidget(self.search_input)

        self.search_output = QLabel("Search: None")
        self.search_output.setStyleSheet("font-weight: bold; color: #FF9800;")
        search_layout.addWidget(self.search_output)

        layout.addWidget(search_group)

    def _setup_test_buttons_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the interactive test buttons group.

        Args:
            layout: Parent layout to add the group to.
        """
        test_group = QGroupBox("Interactive Tests")
        test_layout = QHBoxLayout(test_group)

        test_tab_btn = QPushButton("Test Tab")
        test_tab_btn.clicked.connect(self._test_tab_replace)
        test_layout.addWidget(test_tab_btn)

        test_search_btn = QPushButton("Test Search")
        test_search_btn.clicked.connect(self._test_search)
        test_layout.addWidget(test_search_btn)

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._reset_all)
        test_layout.addWidget(reset_btn)

        layout.addWidget(test_group)

    # -----------------------------------------------------------
    # Event Handlers
    # -----------------------------------------------------------

    def _on_tab_replace_changed(self) -> None:
        """Handle text change in TabReplaceTextEdit."""
        text = self.tab_replace_textedit.toPlainText()
        char_count = len(text)
        self.tab_replace_output.setText(f"Characters: {char_count}")
        print(f"Text modified: {char_count} characters")

    def _on_autocomplete_changed(self, text: str) -> None:
        """
        Handle text change in AutoCompleteInput.

        Args:
            text: The new text value.
        """
        self.autocomplete_output.setText(f"Text entered: {text}")
        print(f"Autocompletion: {text}")

    def _on_search_triggered(self, search_text: str) -> None:
        """
        Handle search submission.

        Args:
            search_text: The submitted search text.
        """
        self.search_output.setText(f"Search: '{search_text}'")
        print(f"Search submitted: {search_text}")

    # -----------------------------------------------------------
    # Test Methods
    # -----------------------------------------------------------

    def _test_tab_replace(self) -> None:
        """Test the TabReplaceTextEdit."""
        test_text = "Line 1\n\tLine 2 with tab\n\t\tLine 3 with double tab"
        self.tab_replace_textedit.setPlainText(test_text)
        print("Test: Text with tabs added")

    def _test_search(self) -> None:
        """Test the SearchInput."""
        self.search_input.setText("test search")
        self.search_input.searchSubmitted.emit("test search")
        print("Test: Search simulated")

    def _reset_all(self) -> None:
        """Reset all widgets to initial state."""
        self.tab_replace_textedit.clear()
        self.autocomplete_input.clear()
        self.search_input.clear()
        self.tab_replace_output.setText("Characters: 0")
        self.autocomplete_output.setText("Text entered: ")
        self.search_output.setText("Search: None")
        print("Reset: All fields cleared")


# ///////////////////////////////////////////////////////////////
# MAIN FUNCTION
# ///////////////////////////////////////////////////////////////


def main() -> None:
    """Main function for standalone execution."""
    app = QApplication(sys.argv)

    # Load theme from files
    bin_dir = os.path.join(os.path.dirname(__file__), "bin")
    qss_path = os.path.join(bin_dir, "main_theme.qss")
    yaml_path = os.path.join(bin_dir, "app.yaml")

    if os.path.exists(qss_path) and os.path.exists(yaml_path):
        load_and_apply_qss(app, qss_path, yaml_path, theme_name="dark")
    else:
        # Default style if theme files not found
        app.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLabel {
                color: #2c3e50;
            }
            QLineEdit, QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #3498db;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """
        )

    window = InputExampleWidget()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
