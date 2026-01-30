#!/usr/bin/env python3
# ///////////////////////////////////////////////////////////////
# MISC EXAMPLE - EzQt Widgets
# Demonstration of miscellaneous widgets
# ///////////////////////////////////////////////////////////////

"""
Miscellaneous widgets usage examples for EzQt Widgets.

This script demonstrates the usage of all available misc widget types:
    - OptionSelector: Option selector with animated selector
    - CircularTimer: Animated circular timer
    - ToggleIcon: Toggleable icon (open/closed states)
    - ToggleSwitch: Modern toggle switch with animation
    - DraggableList: List with draggable and reorderable items

Example:
    Run this script directly to see the misc widgets in action::

        $ python misc_example.py
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
from ezqt_widgets.misc import (
    CircularTimer,
    DraggableList,
    OptionSelector,
    ToggleIcon,
    ToggleSwitch,
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
# MISC EXAMPLE WIDGET
# ///////////////////////////////////////////////////////////////


class MiscExampleWidget(QWidget):
    """
    Demonstration widget for all miscellaneous widget types.

    This widget showcases the functionality of OptionSelector, CircularTimer,
    ToggleIcon, ToggleSwitch, and DraggableList widgets with interactive examples.

    Attributes:
        option_selector: OptionSelector widget for option selection.
        circular_timer: CircularTimer widget for timed operations.
        toggle_icon: ToggleIcon widget for toggling between icons.
        toggle_switch: ToggleSwitch widget for on/off states.
        item_list: DraggableList widget in normal mode.
        compact_list: DraggableList widget in compact mode.
        item_counter: Counter for adding new items.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the MiscExampleWidget.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Misc Examples - EzQt Widgets")
        self.setMinimumSize(900, 800)
        self.item_counter = 5
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
        title = QLabel("Misc Examples - EzQt Widgets")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        content_layout.addWidget(title)

        # Add widget groups
        self._setup_option_selector_group(content_layout)
        self._setup_circular_timer_group(content_layout)
        self._setup_toggle_icon_group(content_layout)
        self._setup_toggle_switch_group(content_layout)
        self._setup_draggable_list_group(content_layout)
        self._setup_test_buttons_group(content_layout)

        # Bottom spacing
        content_layout.addStretch()

        # Configure ScrollArea
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def _setup_option_selector_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the OptionSelector group.

        Args:
            layout: Parent layout to add the group to.
        """
        option_group = QGroupBox("OptionSelector")
        option_layout = QVBoxLayout(option_group)

        option_label = QLabel("Option selector with different configurations:")
        option_layout.addWidget(option_label)

        # Create an option selector
        options = ["Option 1", "Option 2", "Option 3", "Option 4", "Option 5"]
        self.option_selector = OptionSelector(options, default_id=0)
        self.option_selector.valueChanged.connect(self._on_option_changed)
        option_layout.addWidget(self.option_selector)

        self.option_output = QLabel("Selected option: Option 1")
        self.option_output.setStyleSheet("font-weight: bold; color: #4CAF50;")
        option_layout.addWidget(self.option_output)

        layout.addWidget(option_group)

    def _setup_circular_timer_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the CircularTimer group.

        Args:
            layout: Parent layout to add the group to.
        """
        timer_group = QGroupBox("CircularTimer")
        timer_layout = QVBoxLayout(timer_group)

        timer_label = QLabel("Circular timer with control:")
        timer_layout.addWidget(timer_label)

        # Horizontal layout for timer and controls
        timer_control_layout = QHBoxLayout()

        self.circular_timer = CircularTimer(
            duration=10000
        )  # 10 seconds (in milliseconds)
        timer_control_layout.addWidget(self.circular_timer)

        # Timer controls
        timer_buttons_layout = QVBoxLayout()

        start_button = QPushButton("Start")
        start_button.clicked.connect(self._start_timer)
        timer_buttons_layout.addWidget(start_button)

        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(self._stop_timer)
        timer_buttons_layout.addWidget(stop_button)

        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self._reset_timer)
        timer_buttons_layout.addWidget(reset_button)

        timer_control_layout.addLayout(timer_buttons_layout)
        timer_layout.addLayout(timer_control_layout)

        self.timer_status = QLabel("State: Stopped")
        timer_layout.addWidget(self.timer_status)

        # Connect timer signals
        self.circular_timer.cycleCompleted.connect(self._on_timer_timeout)

        layout.addWidget(timer_group)

    def _setup_toggle_icon_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the ToggleIcon group.

        Args:
            layout: Parent layout to add the group to.
        """
        toggle_icon_group = QGroupBox("ToggleIcon")
        toggle_icon_layout = QVBoxLayout(toggle_icon_group)

        toggle_icon_label = QLabel("Toggleable icon:")
        toggle_icon_layout.addWidget(toggle_icon_label)

        # Create simple icons
        pixmap1 = QPixmap(32, 32)
        pixmap1.fill(Qt.GlobalColor.green)
        icon1 = QIcon(pixmap1)

        pixmap2 = QPixmap(32, 32)
        pixmap2.fill(Qt.GlobalColor.red)
        icon2 = QIcon(pixmap2)

        self.toggle_icon = ToggleIcon(opened_icon=icon1, closed_icon=icon2)
        self.toggle_icon.setToolTip("Click to toggle")
        self.toggle_icon.clicked.connect(self._on_toggle_icon_clicked)
        toggle_icon_layout.addWidget(self.toggle_icon)

        self.toggle_icon_status = QLabel("State: Icon 1")
        toggle_icon_layout.addWidget(self.toggle_icon_status)

        layout.addWidget(toggle_icon_group)

    def _setup_toggle_switch_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the ToggleSwitch group.

        Args:
            layout: Parent layout to add the group to.
        """
        toggle_switch_group = QGroupBox("ToggleSwitch")
        toggle_switch_layout = QVBoxLayout(toggle_switch_group)

        toggle_switch_label = QLabel("Toggle switch:")
        toggle_switch_layout.addWidget(toggle_switch_label)

        self.toggle_switch = ToggleSwitch(checked=False)
        self.toggle_switch.toggled.connect(self._on_toggle_switch_changed)
        toggle_switch_layout.addWidget(self.toggle_switch)

        self.toggle_switch_status = QLabel("State: Disabled")
        toggle_switch_layout.addWidget(self.toggle_switch_status)

        layout.addWidget(toggle_switch_group)

    def _setup_draggable_list_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the DraggableList group.

        Args:
            layout: Parent layout to add the group to.
        """
        item_list_group = QGroupBox("DraggableList")
        item_list_layout = QVBoxLayout(item_list_group)

        item_list_label = QLabel("Reorderable item list with drag & drop:")
        item_list_layout.addWidget(item_list_label)

        # Create the item list
        initial_items = [
            "First element",
            "Second element",
            "Third element",
            "Fourth element",
        ]

        # List in normal mode
        self.item_list = DraggableList(
            items=initial_items, icon_color="#FF4444", max_height=200, min_width=120
        )
        self.item_list.itemRemoved.connect(self._on_item_removed)
        self.item_list.itemMoved.connect(self._on_item_moved)
        self.item_list.orderChanged.connect(self._on_order_changed)
        item_list_layout.addWidget(self.item_list)

        # List in compact mode
        compact_label = QLabel("List in compact mode:")
        item_list_layout.addWidget(compact_label)

        self.compact_list = DraggableList(
            items=["Option A", "Option B", "Option C"],
            compact=True,
            icon_color="grey",
            max_height=150,
        )
        self.compact_list.itemRemoved.connect(self._on_item_removed)
        self.compact_list.itemMoved.connect(self._on_item_moved)
        item_list_layout.addWidget(self.compact_list)

        # Controls for the list
        item_controls_layout = QHBoxLayout()

        add_button = QPushButton("Add")
        add_button.clicked.connect(self._add_item)
        item_controls_layout.addWidget(add_button)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.item_list.clear_items)
        item_controls_layout.addWidget(clear_button)

        compact_toggle = QPushButton("Compact Mode")
        compact_toggle.setCheckable(True)
        compact_toggle.clicked.connect(self._toggle_compact_mode)
        item_controls_layout.addWidget(compact_toggle)

        item_list_layout.addLayout(item_controls_layout)

        self.item_list_status = QLabel("Elements: 4 | Mode: Normal")
        item_list_layout.addWidget(self.item_list_status)

        layout.addWidget(item_list_group)

    def _setup_test_buttons_group(self, layout: QVBoxLayout) -> None:
        """
        Set up the interactive test buttons group.

        Args:
            layout: Parent layout to add the group to.
        """
        test_group = QGroupBox("Interactive Tests")
        test_layout = QHBoxLayout(test_group)

        test_option_btn = QPushButton("Test Option")
        test_option_btn.clicked.connect(self._test_option_selector)
        test_layout.addWidget(test_option_btn)

        test_timer_btn = QPushButton("Test Timer")
        test_timer_btn.clicked.connect(self._test_circular_timer)
        test_layout.addWidget(test_timer_btn)

        test_toggle_btn = QPushButton("Test Toggle")
        test_toggle_btn.clicked.connect(self._test_toggle_widgets)
        test_layout.addWidget(test_toggle_btn)

        test_item_btn = QPushButton("Test Items")
        test_item_btn.clicked.connect(self._test_item_list)
        test_layout.addWidget(test_item_btn)

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._reset_all)
        test_layout.addWidget(reset_btn)

        layout.addWidget(test_group)

    # -----------------------------------------------------------
    # Event Handlers
    # -----------------------------------------------------------

    def _on_option_changed(self, option: str) -> None:
        """
        Handle option change event.

        Args:
            option: The selected option.
        """
        self.option_output.setText(f"Selected option: {option}")
        print(f"Option selected: {option}")

    def _start_timer(self) -> None:
        """Start the timer."""
        self.circular_timer.startTimer()
        self.timer_status.setText("State: Running")
        print("Timer started!")

    def _stop_timer(self) -> None:
        """Stop the timer."""
        self.circular_timer.stopTimer()
        self.timer_status.setText("State: Stopped")
        print("Timer stopped!")

    def _reset_timer(self) -> None:
        """Reset the timer."""
        self.circular_timer.resetTimer()
        self.timer_status.setText("State: Stopped")
        print("Timer reset!")

    def _on_timer_timeout(self) -> None:
        """Handle timer timeout event."""
        self.timer_status.setText("State: Completed")
        print("Timer completed!")

    def _on_toggle_icon_clicked(self) -> None:
        """Handle toggle icon click event."""
        current_state = "Icon 2" if self.toggle_icon.state == "opened" else "Icon 1"
        self.toggle_icon_status.setText(f"State: {current_state}")
        print(f"Icon toggled to: {current_state}")

    def _on_toggle_switch_changed(self, checked: bool) -> None:
        """
        Handle toggle switch change event.

        Args:
            checked: Whether the switch is checked.
        """
        state = "Enabled" if checked else "Disabled"
        self.toggle_switch_status.setText(f"State: {state}")
        print(f"Switch: {state}")

    def _on_item_removed(self, item_id: str, position: int) -> None:
        """
        Handle item removed event.

        Args:
            item_id: ID of the removed item.
            position: Position of the removed item.
        """
        print(f"Item removed: {item_id} at position {position}")
        self._update_item_count()

    def _on_item_moved(self, item_id: str, old_pos: int, new_pos: int) -> None:
        """
        Handle item moved event.

        Args:
            item_id: ID of the moved item.
            old_pos: Original position.
            new_pos: New position.
        """
        print(f"Item moved: {item_id} from {old_pos} to {new_pos}")

    def _on_order_changed(self, new_order: list[str]) -> None:
        """
        Handle order changed event.

        Args:
            new_order: New order of items.
        """
        print(f"New order: {new_order}")

    def _add_item(self) -> None:
        """Add a new item to the list."""
        new_item = f"Element {self.item_counter}"
        self.item_list.add_item(new_item, new_item)
        self.item_counter += 1
        self._update_item_count()
        print(f"Item added: {new_item}")

    def _toggle_compact_mode(self) -> None:
        """Toggle between normal and compact mode."""
        is_compact = self.item_list.compact
        self.item_list.compact = not is_compact
        self.compact_list.compact = not is_compact

        mode = "Compact" if not is_compact else "Normal"
        self._update_item_count()
        print(f"Mode changed to: {mode}")

    def _update_item_count(self) -> None:
        """Update the item count display."""
        count = len(self.item_list.items)
        mode = "Compact" if self.item_list.compact else "Normal"
        self.item_list_status.setText(f"Elements: {count} | Mode: {mode}")

    # -----------------------------------------------------------
    # Test Methods
    # -----------------------------------------------------------

    def _test_option_selector(self) -> None:
        """Test the OptionSelector."""
        # Change to the next option
        current_id = self.option_selector.value_id
        next_id = (current_id + 1) % len(self.option_selector.options)
        self.option_selector.value_id = next_id
        print(f"Test: Option changed to index {next_id}")

    def _test_circular_timer(self) -> None:
        """Test the CircularTimer."""
        if not self.circular_timer.running:
            self._start_timer()
        else:
            self._stop_timer()
        print("Test: Timer toggled")

    def _test_toggle_widgets(self) -> None:
        """Test toggle widgets."""
        # Toggle the icon
        self.toggle_icon.clicked.emit()
        # Toggle the switch
        self.toggle_switch.checked = not self.toggle_switch.checked
        print("Test: Toggle widgets tested")

    def _test_item_list(self) -> None:
        """Test the DraggableList."""
        # Add a test item
        self._add_item()
        # Toggle compact mode
        self._toggle_compact_mode()
        print("Test: DraggableList tested (add + compact mode)")

    def _reset_all(self) -> None:
        """Reset all widgets to initial state."""
        # Reset OptionSelector
        self.option_selector.value_id = 0
        self.option_output.setText("Selected option: Option 1")

        # Reset CircularTimer
        self._stop_timer()
        self._reset_timer()

        # Reset ToggleIcon
        self.toggle_icon_status.setText("State: Icon 1")

        # Reset ToggleSwitch
        self.toggle_switch.checked = False
        self.toggle_switch_status.setText("State: Disabled")

        # Reset DraggableList
        initial_items = [
            "First element",
            "Second element",
            "Third element",
            "Fourth element",
        ]
        self.item_list.items = initial_items
        self.item_list.compact = False
        self.compact_list.items = ["Option A", "Option B", "Option C"]
        self.compact_list.compact = True
        self.item_counter = 5
        self._update_item_count()

        print("Reset: All widgets reset to zero")


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

    window = MiscExampleWidget()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
