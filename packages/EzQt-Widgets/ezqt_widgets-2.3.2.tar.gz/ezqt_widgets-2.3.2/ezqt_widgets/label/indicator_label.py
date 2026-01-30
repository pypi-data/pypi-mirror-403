# ///////////////////////////////////////////////////////////////
# INDICATOR_LABEL - Indicator Label Widget
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Indicator label widget module.

Provides a dynamic status indicator widget based on QFrame for displaying
a status label and a colored LED in PySide6 applications.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class IndicatorLabel(QFrame):
    """Dynamic status indicator widget with label and colored LED.

    This widget encapsulates a QLabel for the status text and a QLabel for
    the LED, both arranged horizontally. The possible states are defined in
    a configurable dictionary (status_map), allowing for flexible text, color,
    and state property assignment.

    Features:
        - Dynamic states defined via a status_map dictionary (text, state, color)
        - Property-based access to the current status
        - Emits a statusChanged(str) signal when the status changes
        - Allows custom status sets and colors for various use cases
        - Suitable for online/offline indicators, service status, etc.

    Args:
        parent: The parent widget (default: None).
        status_map: Dictionary defining possible states. Each key is a state
            name, and each value is a dict with keys:
                - text (str): The label to display
                - state (str): The value set as a Qt property for styling
                - color (str): The LED color (any valid CSS color)
            Example:
                {
                    "neutral": {"text": "Waiting", "state": "none", "color": "#A0A0A0"},
                    "online": {"text": "Online", "state": "ok", "color": "#4CAF50"},
                    ...
                }
        initial_status: The initial status key to use (default: "neutral").
        *args: Additional arguments passed to QFrame.
        **kwargs: Additional keyword arguments passed to QFrame.

    Signals:
        statusChanged(str): Emitted when the status changes.
    """

    statusChanged = Signal(str)

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        parent=None,
        status_map: dict[str, dict[str, str]] | None = None,
        initial_status: str = "neutral",
        *args,
        **kwargs,
    ) -> None:
        """Initialize the indicator label."""
        super().__init__(parent, *args, **kwargs)

        self.setProperty("type", "IndicatorLabel")

        # Default status map
        self._status_map: dict[str, dict[str, str]] = status_map or {
            "neutral": {"text": "Waiting", "state": "none", "color": "#A0A0A0"},
            "online": {"text": "Online", "state": "ok", "color": "#4CAF50"},
            "partial": {
                "text": "Services disrupted",
                "state": "partial",
                "color": "#FFC107",
            },
            "offline": {"text": "Offline", "state": "ko", "color": "#F44336"},
        }

        # State variables
        self._current_status: str = ""
        self._status_label: QLabel | None = None
        self._led_label: QLabel | None = None

        # Setup widget
        self._setup_widget()

        # Set initial status
        self.status = initial_status

    # ------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------

    def _setup_widget(self) -> None:
        """Setup the widget properties and layout."""
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setContentsMargins(4, 2, 4, 2)
        self.setFixedHeight(24)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self._layout = QHBoxLayout(self)
        self._layout.setObjectName("status_HLayout")
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)

        self._status_label = QLabel()
        self._status_label.setObjectName("status_label")
        self._status_label.setFont(QFont("Segoe UI", 10))
        self._status_label.setLineWidth(0)
        self._status_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self._status_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        self._led_label = QLabel()
        self._led_label.setObjectName("status_led")
        self._led_label.setFixedSize(QSize(13, 16))
        self._led_label.setFont(QFont("Segoe UI", 10))
        self._led_label.setLineWidth(0)
        self._led_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._layout.addWidget(self._status_label, 0, Qt.AlignmentFlag.AlignTop)
        self._layout.addWidget(self._led_label, 0, Qt.AlignmentFlag.AlignTop)

    def _update_display(self) -> None:
        """Update the display based on current status."""
        if not self._status_label or not self._led_label:
            return

        status_info = self._status_map.get(self._current_status, {})
        text = status_info.get("text", "Unknown")
        state = status_info.get("state", "none")
        color = status_info.get("color", "#A0A0A0")

        self._status_label.setText(text)

        self._led_label.setStyleSheet(f"""
            background-color: {color};
            border: 2px solid rgb(66, 66, 66);
            border-radius: 6px;
            margin-top: 3px;
            """)

        self.setProperty("state", state)
        self.style().unpolish(self)
        self.style().polish(self)

    # ///////////////////////////////////////////////////////////////
    # PROPERTIES
    # ///////////////////////////////////////////////////////////////

    @property
    def status(self) -> str:
        """Get the current status key.

        Returns:
            The current status key.
        """
        return self._current_status

    @status.setter
    def status(self, value: str) -> None:
        """Set the current status key.

        Args:
            value: The new status key.
        """
        self.set_status(value)

    # ///////////////////////////////////////////////////////////////
    # PUBLIC METHODS
    # ///////////////////////////////////////////////////////////////

    def set_status(self, status: str) -> None:
        """Set the current status and update the display.

        Args:
            status: The status key to set.

        Raises:
            ValueError: If status is not in the status_map.
        """
        if status not in self._status_map:
            raise ValueError(f"Unknown status: {status}")

        if status != self._current_status:
            self._current_status = status
            self._update_display()
            self.statusChanged.emit(self._current_status)

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
