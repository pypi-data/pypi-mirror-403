#!/usr/bin/env python3
# ///////////////////////////////////////////////////////////////
# BUTTON EXAMPLE - EzQt Widgets
# Demonstration of button widgets
# ///////////////////////////////////////////////////////////////

"""
Button widgets usage examples for EzQt Widgets.

This script demonstrates the usage of all available button widget types:
    - DateButton: Date picker button with integrated calendar
    - IconButton: Button with icon support and optional text
    - LoaderButton: Button with integrated loading animation

Example:
    Run this script directly to see the button widgets in action::

        $ python button_example.py
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import os
import re
import sys
from datetime import datetime, timedelta

# Third-party imports
import yaml
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap
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
from ezqt_widgets.button import DateButton, IconButton, LoaderButton

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
# BUTTON EXAMPLE WIDGET
# ///////////////////////////////////////////////////////////////


class ButtonExampleWidget(QWidget):
    """
    Demonstration widget for all button types.

    This widget showcases the functionality of DateButton, IconButton,
    and LoaderButton widgets with interactive examples.

    Attributes:
        date_button: DateButton widget for date selection.
        icon_button: IconButton widget with icon and text.
        loader_button: LoaderButton widget with loading states.
        icon_click_count: Counter for icon button clicks.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the ButtonExampleWidget.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Button Examples - EzQt Widgets")
        self.setMinimumSize(800, 600)
        self.icon_click_count = 0
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
        title = QLabel("Button Examples - EzQt Widgets")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        content_layout.addWidget(title)

        # Add widget groups
        self._setup_date_button_group(content_layout)
        self._setup_icon_button_group(content_layout)
        self._setup_loader_button_group(content_layout)
        self._setup_test_buttons_group(content_layout)

        # Bottom spacing
        content_layout.addStretch()

        # Configure ScrollArea
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def _setup_date_button_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the DateButton group.

        Args:
            layout: Parent layout to add the group to.
        """
        date_group = QGroupBox("DateButton")
        date_layout = QVBoxLayout(date_group)

        date_label = QLabel("Date selector with validation:")
        date_layout.addWidget(date_label)

        self.date_button = DateButton()
        self.date_button.date = "2024-01-15"  # type: ignore[assignment]
        self.date_button.dateChanged.connect(self._on_date_changed)
        date_layout.addWidget(self.date_button)

        self.date_output = QLabel("Selected date: 2024-01-15")
        self.date_output.setStyleSheet("font-weight: bold; color: #4CAF50;")
        date_layout.addWidget(self.date_output)

        layout.addWidget(date_group)

    def _setup_icon_button_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the IconButton group.

        Args:
            layout: Parent layout to add the group to.
        """
        icon_group = QGroupBox("IconButton")
        icon_layout = QVBoxLayout(icon_group)

        icon_label = QLabel("Button with icon and text:")
        icon_layout.addWidget(icon_label)

        # Create a simple icon for the example
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.blue)
        icon = QIcon(pixmap)

        self.icon_button = IconButton()
        self.icon_button.setIcon(icon)
        self.icon_button.setText("Button with Icon")
        self.icon_button.clicked.connect(self._on_icon_button_clicked)
        icon_layout.addWidget(self.icon_button)

        self.icon_output = QLabel("Clicks: 0")
        self.icon_output.setStyleSheet("font-weight: bold; color: #2196F3;")
        icon_layout.addWidget(self.icon_output)

        layout.addWidget(icon_group)

    def _setup_loader_button_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the LoaderButton group.

        Args:
            layout: Parent layout to add the group to.
        """
        loader_group = QGroupBox("LoaderButton")
        loader_layout = QVBoxLayout(loader_group)

        loader_label = QLabel("Loading button with states:")
        loader_layout.addWidget(loader_label)

        # Create LoaderButton with complete configuration
        self.loader_button = LoaderButton(
            text="Load Data",
            loading_text="Loading...",
            auto_reset=True,
            success_display_time=2000,
            error_display_time=3000,
        )
        self.loader_button.clicked.connect(self._on_loader_button_clicked)
        loader_layout.addWidget(self.loader_button)

        self.loader_output = QLabel("State: Ready")
        self.loader_output.setStyleSheet("font-weight: bold; color: #FF9800;")
        loader_layout.addWidget(self.loader_output)

        layout.addWidget(loader_group)

    def _setup_test_buttons_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the interactive test buttons group.

        Args:
            layout: Parent layout to add the group to.
        """
        test_group = QGroupBox("Interactive Tests")
        test_layout = QHBoxLayout(test_group)

        test_date_btn = QPushButton("Test Date")
        test_date_btn.clicked.connect(self._test_date_button)
        test_layout.addWidget(test_date_btn)

        test_loader_btn = QPushButton("Test Loader")
        test_loader_btn.clicked.connect(self._test_loader_button)
        test_layout.addWidget(test_loader_btn)

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._reset_all)
        test_layout.addWidget(reset_btn)

        layout.addWidget(test_group)

    # -----------------------------------------------------------
    # Event Handlers
    # -----------------------------------------------------------

    def _on_date_changed(self, date: str) -> None:
        """
        Handle date change event.

        Args:
            date: The new date value.
        """
        self.date_output.setText(f"Selected date: {date}")
        print(f"Date changed: {date}")

    def _on_icon_button_clicked(self) -> None:
        """Handle icon button click event."""
        self.icon_click_count += 1
        self.icon_output.setText(f"Clicks: {self.icon_click_count}")
        print(f"Icon button clicked! Total: {self.icon_click_count}")

    def _on_loader_button_clicked(self) -> None:
        """Handle loader button click event."""
        self.loader_output.setText("State: Loading...")
        print("Loading started...")

        # Simulate loading
        QTimer.singleShot(2000, self._simulate_loading_complete)

    def _simulate_loading_complete(self) -> None:
        """Simulate loading completion."""
        import random

        success = random.choice([True, False])  # noqa: S311

        if success:
            self.loader_output.setText("State: Success!")
            print("Loading successful!")
        else:
            self.loader_output.setText("State: Error!")
            print("Loading error!")

    # -----------------------------------------------------------
    # Test Methods
    # -----------------------------------------------------------

    def _test_date_button(self) -> None:
        """Test the date button."""
        new_date = datetime.now() + timedelta(days=7)
        self.date_button.date = new_date.strftime("%Y-%m-%d")  # type: ignore[assignment]
        print(f"Test: Date changed to {new_date.strftime('%Y-%m-%d')}")

    def _test_loader_button(self) -> None:
        """Test the loader button."""
        self.loader_button.click()
        print("Test: Loading started")

    def _reset_all(self) -> None:
        """Reset all widgets to initial state."""
        self.icon_click_count = 0
        self.icon_output.setText("Clicks: 0")
        self.loader_output.setText("State: Ready")
        self.date_button.date = "2024-01-15"  # type: ignore[assignment]
        print("Reset: All counters reset to zero")


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
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """
        )

    window = ButtonExampleWidget()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
