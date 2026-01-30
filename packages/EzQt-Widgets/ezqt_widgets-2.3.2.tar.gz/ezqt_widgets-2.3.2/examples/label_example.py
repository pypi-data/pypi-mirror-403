#!/usr/bin/env python3
# ///////////////////////////////////////////////////////////////
# LABEL EXAMPLE - EzQt Widgets
# Demonstration of label widgets
# ///////////////////////////////////////////////////////////////

"""
Label widgets usage examples for EzQt Widgets.

This script demonstrates the usage of all available label widget types:
    - FramedLabel: Framed label for advanced styling
    - IndicatorLabel: Status indicator with colored LED
    - HoverLabel: Label with hover icon display
    - ClickableTagLabel: Clickable tag with toggle state

Example:
    Run this script directly to see the label widgets in action::

        $ python label_example.py
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
from PySide6.QtCore import Qt, QTimer
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
from ezqt_widgets.label import (
    ClickableTagLabel,
    FramedLabel,
    HoverLabel,
    IndicatorLabel,
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
# LABEL EXAMPLE WIDGET
# ///////////////////////////////////////////////////////////////


class LabelExampleWidget(QWidget):
    """
    Demonstration widget for all label types.

    This widget showcases the functionality of FramedLabel, IndicatorLabel,
    HoverLabel, and ClickableTagLabel widgets with interactive examples.

    Attributes:
        framed_label1: First FramedLabel widget.
        framed_label2: Second FramedLabel widget.
        framed_label3: Third FramedLabel widget.
        success_indicator: IndicatorLabel for success state.
        error_indicator: IndicatorLabel for error state.
        warning_indicator: IndicatorLabel for warning state.
        info_indicator: IndicatorLabel for info state.
        hover_label1: First HoverLabel widget.
        hover_label2: Second HoverLabel widget.
        tag_label1: First ClickableTagLabel widget.
        tag_label2: Second ClickableTagLabel widget.
        tag_label3: Third ClickableTagLabel widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the LabelExampleWidget.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Label Examples - EzQt Widgets")
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
        title = QLabel("Label Examples - EzQt Widgets")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        content_layout.addWidget(title)

        # Add widget groups
        self._setup_framed_label_group(content_layout)
        self._setup_indicator_label_group(content_layout)
        self._setup_hover_label_group(content_layout)
        self._setup_tag_label_group(content_layout)
        self._setup_test_buttons_group(content_layout)

        # Bottom spacing
        content_layout.addStretch()

        # Configure ScrollArea
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def _setup_framed_label_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the FramedLabel group.

        Args:
            layout: Parent layout to add the group to.
        """
        framed_group = QGroupBox("FramedLabel")
        framed_layout = QVBoxLayout(framed_group)

        framed_label = QLabel("Labels with customizable frame:")
        framed_layout.addWidget(framed_label)

        # Horizontal layout for FramedLabels
        framed_buttons_layout = QHBoxLayout()

        self.framed_label1 = FramedLabel("Label 1")
        framed_buttons_layout.addWidget(self.framed_label1)

        self.framed_label2 = FramedLabel("Label 2")
        framed_buttons_layout.addWidget(self.framed_label2)

        self.framed_label3 = FramedLabel("Label 3")
        framed_buttons_layout.addWidget(self.framed_label3)

        framed_layout.addLayout(framed_buttons_layout)

        self.framed_output = QLabel("Label clicked: None")
        self.framed_output.setStyleSheet("font-weight: bold; color: #4CAF50;")
        framed_layout.addWidget(self.framed_output)

        layout.addWidget(framed_group)

    def _setup_indicator_label_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the IndicatorLabel group.

        Args:
            layout: Parent layout to add the group to.
        """
        indicator_group = QGroupBox("IndicatorLabel")
        indicator_layout = QVBoxLayout(indicator_group)

        indicator_label = QLabel("Indicators with different states:")
        indicator_layout.addWidget(indicator_label)

        # Create a custom status_map for our indicators
        custom_status_map = {
            "success": {"text": "Success", "state": "ok", "color": "#4CAF50"},
            "error": {"text": "Error", "state": "ko", "color": "#F44336"},
            "warning": {
                "text": "Warning",
                "state": "partial",
                "color": "#FFC107",
            },
            "info": {"text": "Information", "state": "none", "color": "#2196F3"},
        }

        # Buttons to change indicator state
        button_layout = QHBoxLayout()

        self.success_indicator = IndicatorLabel(
            status_map=custom_status_map, initial_status="success"
        )
        button_layout.addWidget(self.success_indicator)

        self.error_indicator = IndicatorLabel(
            status_map=custom_status_map, initial_status="error"
        )
        button_layout.addWidget(self.error_indicator)

        self.warning_indicator = IndicatorLabel(
            status_map=custom_status_map, initial_status="warning"
        )
        button_layout.addWidget(self.warning_indicator)

        self.info_indicator = IndicatorLabel(
            status_map=custom_status_map, initial_status="info"
        )
        button_layout.addWidget(self.info_indicator)

        indicator_layout.addLayout(button_layout)

        # Button to test indicator animation
        test_animation_btn = QPushButton("Test Animation")
        test_animation_btn.clicked.connect(self._test_indicator_animation)
        indicator_layout.addWidget(test_animation_btn)

        layout.addWidget(indicator_group)

    def _setup_hover_label_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the HoverLabel group.

        Args:
            layout: Parent layout to add the group to.
        """
        hover_group = QGroupBox("HoverLabel")
        hover_layout = QVBoxLayout(hover_group)

        hover_label = QLabel("Labels with hover effect:")
        hover_layout.addWidget(hover_label)

        # Horizontal layout for HoverLabels
        hover_buttons_layout = QHBoxLayout()

        self.hover_label1 = HoverLabel("Hover over me to see the effect!")
        self.hover_label1.hoverIconClicked.connect(self._on_hover_label_clicked)
        hover_buttons_layout.addWidget(self.hover_label1)

        self.hover_label2 = HoverLabel("Another interactive label")
        self.hover_label2.hoverIconClicked.connect(self._on_hover_label_clicked)
        hover_buttons_layout.addWidget(self.hover_label2)

        hover_layout.addLayout(hover_buttons_layout)

        self.hover_output = QLabel("Hovered label: None")
        self.hover_output.setStyleSheet("font-weight: bold; color: #2196F3;")
        hover_layout.addWidget(self.hover_output)

        layout.addWidget(hover_group)

    def _setup_tag_label_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the ClickableTagLabel group.

        Args:
            layout: Parent layout to add the group to.
        """
        tag_group = QGroupBox("ClickableTagLabel")
        tag_layout = QVBoxLayout(tag_group)

        tag_label = QLabel("Clickable labels with tag style:")
        tag_layout.addWidget(tag_label)

        # Horizontal layout for ClickableTagLabels
        tag_buttons_layout = QHBoxLayout()

        self.tag_label1 = ClickableTagLabel("Tag 1")
        self.tag_label1.clicked.connect(self._on_tag_label_clicked)
        tag_buttons_layout.addWidget(self.tag_label1)

        self.tag_label2 = ClickableTagLabel("Tag 2")
        self.tag_label2.clicked.connect(self._on_tag_label_clicked)
        tag_buttons_layout.addWidget(self.tag_label2)

        self.tag_label3 = ClickableTagLabel("Tag 3")
        self.tag_label3.clicked.connect(self._on_tag_label_clicked)
        tag_buttons_layout.addWidget(self.tag_label3)

        tag_layout.addLayout(tag_buttons_layout)

        self.tag_output = QLabel("Tag clicked: None")
        self.tag_output.setStyleSheet("font-weight: bold; color: #FF9800;")
        tag_layout.addWidget(self.tag_output)

        layout.addWidget(tag_group)

    def _setup_test_buttons_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the interactive test buttons group.

        Args:
            layout: Parent layout to add the group to.
        """
        test_group = QGroupBox("Interactive Tests")
        test_layout = QHBoxLayout(test_group)

        test_framed_btn = QPushButton("Test Framed")
        test_framed_btn.clicked.connect(self._test_framed_labels)
        test_layout.addWidget(test_framed_btn)

        test_hover_btn = QPushButton("Test Hover")
        test_hover_btn.clicked.connect(self._test_hover_labels)
        test_layout.addWidget(test_hover_btn)

        test_tag_btn = QPushButton("Test Tags")
        test_tag_btn.clicked.connect(self._test_tag_labels)
        test_layout.addWidget(test_tag_btn)

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._reset_all)
        test_layout.addWidget(reset_btn)

        layout.addWidget(test_group)

    # -----------------------------------------------------------
    # Event Handlers
    # -----------------------------------------------------------

    def _on_framed_label_clicked(self) -> None:
        """Handle FramedLabel click event."""
        sender = self.sender()
        if sender and hasattr(sender, "text"):
            text = sender.text
            self.framed_output.setText(f"Label clicked: {text}")
            print(f"FramedLabel clicked: {text}")

    def _on_hover_label_clicked(self) -> None:
        """Handle HoverLabel click event."""
        sender = self.sender()
        if sender and hasattr(sender, "text"):
            text = sender.text
            self.hover_output.setText(f"Hovered label: {text}")
            print(f"HoverLabel clicked: {text}")

    def _on_tag_label_clicked(self) -> None:
        """Handle ClickableTagLabel click event."""
        sender = self.sender()
        if sender and hasattr(sender, "text"):
            text = sender.text
            self.tag_output.setText(f"Tag clicked: {text}")
            print(f"ClickableTagLabel clicked: {text}")

    # -----------------------------------------------------------
    # Test Methods
    # -----------------------------------------------------------

    def _test_indicator_animation(self) -> None:
        """Test indicator animation by swapping states."""
        # Simulate state change
        self.success_indicator.status = "error"
        self.error_indicator.status = "success"
        self.warning_indicator.status = "info"
        self.info_indicator.status = "warning"

        # Reset to original states after 2 seconds
        QTimer.singleShot(2000, self._reset_indicators)

    def _reset_indicators(self) -> None:
        """Reset indicators to their original state."""
        self.success_indicator.status = "success"
        self.error_indicator.status = "error"
        self.warning_indicator.status = "warning"
        self.info_indicator.status = "info"

    def _test_framed_labels(self) -> None:
        """Test FramedLabel widgets."""
        self.framed_label1.text = "Test 1"
        self.framed_label2.text = "Test 2"
        self.framed_label3.text = "Test 3"
        print("Test: FramedLabel texts modified")

    def _test_hover_labels(self) -> None:
        """Test HoverLabel widgets."""
        self.hover_label1.setText("Hover Test 1")
        self.hover_label2.setText("Hover Test 2")
        print("Test: HoverLabel texts modified")

    def _test_tag_labels(self) -> None:
        """Test ClickableTagLabel widgets."""
        self.tag_label1.name = "Tag Test 1"
        self.tag_label2.name = "Tag Test 2"
        self.tag_label3.name = "Tag Test 3"
        print("Test: ClickableTagLabel texts modified")

    def _reset_all(self) -> None:
        """Reset all widgets to initial state."""
        # Reset FramedLabel
        self.framed_label1.text = "Label 1"
        self.framed_label2.text = "Label 2"
        self.framed_label3.text = "Label 3"
        self.framed_output.setText("Label clicked: None")

        # Reset HoverLabel
        self.hover_label1.setText("Hover over me to see the effect!")
        self.hover_label2.setText("Another interactive label")
        self.hover_output.setText("Hovered label: None")

        # Reset ClickableTagLabel
        self.tag_label1.name = "Tag 1"
        self.tag_label2.name = "Tag 2"
        self.tag_label3.name = "Tag 3"
        self.tag_output.setText("Tag clicked: None")

        # Reset IndicatorLabel
        self._reset_indicators()

        print("Reset: All labels reset to zero")


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

    window = LabelExampleWidget()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
