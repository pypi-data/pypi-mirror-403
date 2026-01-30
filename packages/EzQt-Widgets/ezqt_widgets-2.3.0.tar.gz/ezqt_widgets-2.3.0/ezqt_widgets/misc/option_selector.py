# ///////////////////////////////////////////////////////////////
# OPTION_SELECTOR - Option Selector Widget
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Option selector widget module.

Provides an option selector widget with animated selector for PySide6
applications.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QSize, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QGridLayout, QSizePolicy

# Local imports
from ..label.framed_label import FramedLabel

# ///////////////////////////////////////////////////////////////
# UTILITY CLASSES
# ///////////////////////////////////////////////////////////////


class _SelectableOptionLabel(FramedLabel):
    """Internal label class for selectable options."""

    def __init__(
        self,
        text: str,
        option_id: int,
        selector: OptionSelector,
        parent=None,
    ) -> None:
        """Initialize the selectable option label.

        Args:
            text: The option text.
            option_id: The option ID.
            selector: The parent OptionSelector instance.
            parent: The parent widget.
        """
        super().__init__(text, parent)
        self._option_id = option_id
        self._selector = selector

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events.

        Args:
            event: The mouse event.
        """
        self._selector.toggle_selection(self._option_id)
        super().mousePressEvent(event)


# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class OptionSelector(QFrame):
    """Option selector widget with animated selector.

    Features:
        - Multiple selectable options displayed as labels
        - Animated selector that moves between options
        - Single selection mode (radio behavior)
        - Configurable default selection by ID (index)
        - Smooth animations with easing curves
        - Click events for option selection
        - Uses IDs internally for robust value handling

    Args:
        items: List of option texts to display.
        default_id: Default selected option ID (index) (default: 0).
        min_width: Minimum width constraint for the widget (default: None).
        min_height: Minimum height constraint for the widget (default: None).
        orientation: Layout orientation: "horizontal" or "vertical"
            (default: "horizontal").
        animation_duration: Duration of the selector animation in milliseconds
            (default: 300).
        parent: The parent widget (default: None).
        *args: Additional arguments passed to QFrame.
        **kwargs: Additional keyword arguments passed to QFrame.

    Signals:
        clicked(): Emitted when an option is clicked.
        valueChanged(str): Emitted when the selected value changes.
        valueIdChanged(int): Emitted when the selected value ID changes.
    """

    clicked = Signal()
    valueChanged = Signal(str)
    valueIdChanged = Signal(int)

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        items: list[str],
        default_id: int = 0,
        min_width: int | None = None,
        min_height: int | None = None,
        orientation: str = "horizontal",
        animation_duration: int = 300,
        parent=None,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the option selector."""
        super().__init__(parent, *args, **kwargs)
        self.setProperty("type", "OptionSelector")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Initialize variables
        self._value_id = 0
        self._options_list = items
        self._default_id = default_id
        self._options: dict[int, FramedLabel] = {}
        self._selector_animation: QPropertyAnimation | None = None
        self._min_width = min_width
        self._min_height = min_height
        self._orientation = orientation.lower()
        self._animation_duration = animation_duration

        # Setup grid layout
        self.grid = QGridLayout(self)
        self.grid.setObjectName("grid")
        self.grid.setSpacing(4)
        self.grid.setContentsMargins(4, 4, 4, 4)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create selector
        self.selector = QFrame(self)
        self.selector.setObjectName("selector")
        self.selector.setProperty("type", "OptionSelector_Selector")

        # Add options
        for i, option_text in enumerate(self._options_list):
            self.add_option(option_id=i, option_text=option_text)

        # Initialize selector
        if self._options_list:
            self.initialize_selector(self._default_id)

    # ///////////////////////////////////////////////////////////////
    # PROPERTIES
    # ///////////////////////////////////////////////////////////////

    @property
    def value(self) -> str:
        """Get or set the currently selected option text.

        Returns:
            The currently selected option text, or empty string if none.
        """
        if 0 <= self._value_id < len(self._options_list):
            return self._options_list[self._value_id]
        return ""

    @value.setter
    def value(self, new_value: str) -> None:
        """Set the selected option by text.

        Args:
            new_value: The option text to select.
        """
        try:
            new_id = self._options_list.index(new_value)
            self.value_id = new_id
        except ValueError:
            pass  # Value not found in list

    @property
    def value_id(self) -> int:
        """Get or set the currently selected option ID.

        Returns:
            The currently selected option ID.
        """
        return self._value_id

    @value_id.setter
    def value_id(self, new_id: int) -> None:
        """Set the selected option by ID.

        Args:
            new_id: The option ID to select.
        """
        if 0 <= new_id < len(self._options_list) and new_id != self._value_id:
            self._value_id = new_id
            if new_id in self._options:
                self.move_selector(self._options[new_id])
            self.valueChanged.emit(self.value)
            self.valueIdChanged.emit(new_id)

    @property
    def options(self) -> list[str]:
        """Get the list of available options.

        Returns:
            A copy of the options list.
        """
        return self._options_list.copy()

    @property
    def default_id(self) -> int:
        """Get or set the default option ID.

        Returns:
            The default option ID.
        """
        return self._default_id

    @default_id.setter
    def default_id(self, value: int) -> None:
        """Set the default option ID.

        Args:
            value: The new default option ID.
        """
        if 0 <= value < len(self._options_list):
            self._default_id = value
            if not self._value_id and self._options_list:
                self.value_id = value

    @property
    def selected_option(self) -> FramedLabel | None:
        """Get the currently selected option widget.

        Returns:
            The selected option widget, or None if none selected.
        """
        if self._value_id in self._options:
            return self._options[self._value_id]
        return None

    @property
    def orientation(self) -> str:
        """Get or set the orientation of the selector.

        Returns:
            The current orientation ("horizontal" or "vertical").
        """
        return self._orientation

    @orientation.setter
    def orientation(self, value: str) -> None:
        """Set the orientation of the selector.

        Args:
            value: The new orientation ("horizontal" or "vertical").
        """
        if value.lower() in ["horizontal", "vertical"]:
            self._orientation = value.lower()
            self.updateGeometry()

    @property
    def min_width(self) -> int | None:
        """Get or set the minimum width of the widget.

        Returns:
            The minimum width, or None if not set.
        """
        return self._min_width

    @min_width.setter
    def min_width(self, value: int | None) -> None:
        """Set the minimum width of the widget.

        Args:
            value: The new minimum width, or None to auto-calculate.
        """
        self._min_width = value
        self.updateGeometry()

    @property
    def min_height(self) -> int | None:
        """Get or set the minimum height of the widget.

        Returns:
            The minimum height, or None if not set.
        """
        return self._min_height

    @min_height.setter
    def min_height(self, value: int | None) -> None:
        """Set the minimum height of the widget.

        Args:
            value: The new minimum height, or None to auto-calculate.
        """
        self._min_height = value
        self.updateGeometry()

    @property
    def animation_duration(self) -> int:
        """Get or set the animation duration in milliseconds.

        Returns:
            The animation duration in milliseconds.
        """
        return self._animation_duration

    @animation_duration.setter
    def animation_duration(self, value: int) -> None:
        """Set the animation duration in milliseconds.

        Args:
            value: The new animation duration in milliseconds.
        """
        self._animation_duration = value

    # ///////////////////////////////////////////////////////////////
    # PUBLIC METHODS
    # ///////////////////////////////////////////////////////////////

    def initialize_selector(self, default_id: int = 0) -> None:
        """Initialize the selector with default position.

        Args:
            default_id: The default option ID to select.
        """
        if 0 <= default_id < len(self._options_list):
            self._default_id = default_id
            selected_option = self._options.get(default_id)

            if selected_option:
                self._value_id = default_id

                default_pos = self.grid.indexOf(selected_option)
                self.grid.addWidget(self.selector, 0, default_pos)
                self.selector.lower()  # Ensure selector stays below
                self.selector.update()  # Force refresh if needed

    def add_option(self, option_id: int, option_text: str) -> None:
        """Add a new option to the selector.

        Args:
            option_id: The ID for the option.
            option_text: The text to display for the option.
        """
        # Create option label
        option = _SelectableOptionLabel(option_text.capitalize(), option_id, self, self)
        option.setObjectName(f"opt_{option_id}")
        option.setFrameShape(QFrame.Shape.NoFrame)
        option.setFrameShadow(QFrame.Shadow.Raised)
        option.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        option.setProperty("type", "OptionSelector_Option")

        # Add to grid based on orientation
        option_index = len(self._options.items())
        if self._orientation == "horizontal":
            self.grid.addWidget(option, 0, option_index)
        else:  # vertical
            self.grid.addWidget(option, option_index, 0)

        # Store option
        self._options[option_id] = option

        # Update options list
        if option_id >= len(self._options_list):
            # Add empty elements if necessary
            while len(self._options_list) <= option_id:
                self._options_list.append("")
        self._options_list[option_id] = option_text

    def toggle_selection(self, option_id: int) -> None:
        """Handle option selection.

        Args:
            option_id: The ID of the option to select.
        """
        if option_id != self._value_id:
            self._value_id = option_id
            self.clicked.emit()
            self.valueChanged.emit(self.value)
            self.valueIdChanged.emit(option_id)
            self.move_selector(self._options[option_id])

    def move_selector(self, option: FramedLabel) -> None:
        """Animate the selector to the selected option.

        Args:
            option: The option widget to move the selector to.
        """
        start_geometry = self.selector.geometry()
        end_geometry = option.geometry()

        # Create geometry animation
        self._selector_animation = QPropertyAnimation(self.selector, b"geometry")
        self._selector_animation.setDuration(self._animation_duration)
        self._selector_animation.setStartValue(start_geometry)
        self._selector_animation.setEndValue(end_geometry)
        self._selector_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Ensure selector stays below
        self.selector.lower()

        # Start animation
        self._selector_animation.start()

    # ///////////////////////////////////////////////////////////////
    # OVERRIDE METHODS
    # ///////////////////////////////////////////////////////////////

    def sizeHint(self) -> QSize:
        """Get the recommended size for the widget.

        Returns:
            The recommended size.
        """
        return QSize(200, 40)

    def minimumSizeHint(self) -> QSize:
        """Get the minimum size hint for the widget.

        Returns:
            The minimum size hint.
        """
        # Calculate options dimensions
        max_option_width = 0
        max_option_height = 0

        for option_text in self._options_list:
            # Estimate text width using font metrics
            font_metrics = self.fontMetrics()
            text_width = font_metrics.horizontalAdvance(option_text.capitalize())

            # Add padding and margins
            option_width = text_width + 16  # 8px padding on each side
            option_height = max(font_metrics.height() + 8, 30)  # 4px padding top/bottom

            max_option_width = max(max_option_width, option_width)
            max_option_height = max(max_option_height, option_height)

        # Calculate total dimensions based on orientation
        if self._orientation == "horizontal":
            # Horizontal: options side by side with individual widths
            total_width = 0
            for option_text in self._options_list:
                font_metrics = self.fontMetrics()
                text_width = font_metrics.horizontalAdvance(option_text.capitalize())
                option_width = text_width + 16  # 8px padding on each side
                total_width += option_width
            total_width += (len(self._options_list) - 1) * self.grid.spacing()
            total_height = max_option_height
        else:
            # Vertical: options stacked
            total_width = max_option_width
            total_height = max_option_height * len(self._options_list)
            total_height += (len(self._options_list) - 1) * self.grid.spacing()

        # Add grid margins
        total_width += 8  # Grid margins (4px on each side)
        total_height += 8  # Grid margins (4px on each side)

        # Apply minimum constraints
        min_width = self._min_width if self._min_width is not None else total_width
        min_height = self._min_height if self._min_height is not None else total_height

        return QSize(max(min_width, total_width), max(min_height, total_height))

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
