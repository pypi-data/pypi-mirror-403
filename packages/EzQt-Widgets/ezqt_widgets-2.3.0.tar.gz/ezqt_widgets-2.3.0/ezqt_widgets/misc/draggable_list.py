# ///////////////////////////////////////////////////////////////
# DRAGGABLE_LIST - Draggable List Widget
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Draggable list widget module.

Provides a list widget with draggable and reorderable items for PySide6
applications.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
from typing import Any

# Third-party imports
from PySide6.QtCore import QMimeData, QPoint, QSize, Qt, Signal
from PySide6.QtGui import (
    QDrag,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QMouseEvent,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# Local imports
from ..label.hover_label import HoverLabel

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class DraggableItem(QFrame):
    """Draggable item widget for DraggableList.

    This item can be moved by drag & drop and always contains a HoverLabel
    for a consistent interface.

    Args:
        item_id: Unique identifier for the item.
        text: Text to display in the item.
        parent: Parent widget (default: None).
        icon: Icon for the item (default: None, uses default icon).
        compact: Whether to display in compact mode (default: False).
        **kwargs: Additional keyword arguments passed to HoverLabel.

    Signals:
        itemClicked(str): Emitted when the item is clicked.
        itemRemoved(str): Emitted when the item is removed.
    """

    itemClicked = Signal(str)
    itemRemoved = Signal(str)

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        item_id: str,
        text: str,
        parent: QWidget | None = None,
        icon: str | Any | None = None,
        compact: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize the draggable item."""
        super().__init__(parent)
        self.setProperty("type", "DraggableItem")

        # Initialize attributes
        self.item_id = item_id
        self.text = text
        self.is_dragging = False
        self.drag_start_pos = QPoint()
        self._compact = compact

        # Configure widget
        self.setFrameShape(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setMidLineWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Height based on compact mode
        if self._compact:
            self.setMinimumHeight(24)
            self.setMaximumHeight(32)
        else:
            self.setMinimumHeight(40)
            self.setMaximumHeight(60)

        # Main layout
        layout = QHBoxLayout(self)
        if self._compact:
            layout.setContentsMargins(6, 2, 6, 2)  # Reduced margins in compact mode
        else:
            layout.setContentsMargins(8, 4, 8, 4)  # Normal margins
        layout.setSpacing(8)

        # Default icon for drag & drop if no icon is provided
        if icon is None:
            icon = "https://img.icons8.com/?size=100&id=8329&format=png&color=000000"

        # Content widget (HoverLabel with removal icon)
        icon_size = QSize(16, 16) if self._compact else QSize(20, 20)
        icon_padding = 2 if self._compact else 4

        self.content_widget = HoverLabel(
            text=text,
            icon=icon,  # Trash icon for removal
            icon_size=icon_size,
            icon_padding=icon_padding,
            **kwargs,
        )
        self.content_widget.hoverIconClicked.connect(self._on_remove_clicked)

        # Icon color property
        self._icon_color = "grey"
        # Apply initial color
        self.content_widget.icon_color = self._icon_color

        # Add widget to layout (takes full width)
        layout.addWidget(self.content_widget)

    # ------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------

    def _on_remove_clicked(self) -> None:
        """Handle click on removal icon."""
        self.itemRemoved.emit(self.item_id)

    # ///////////////////////////////////////////////////////////////
    # PROPERTIES
    # ///////////////////////////////////////////////////////////////

    @property
    def icon_color(self) -> str:
        """Get the icon color of the HoverLabel.

        Returns:
            The current icon color.
        """
        return self._icon_color

    @icon_color.setter
    def icon_color(self, value: str) -> None:
        """Set the icon color of the HoverLabel.

        Args:
            value: The new icon color.
        """
        self._icon_color = value
        if self.content_widget:
            self.content_widget.icon_color = value

    @property
    def compact(self) -> bool:
        """Get the compact mode.

        Returns:
            True if compact mode is enabled, False otherwise.
        """
        return self._compact

    @compact.setter
    def compact(self, value: bool) -> None:
        """Set the compact mode and adjust height.

        Args:
            value: Whether to enable compact mode.
        """
        self._compact = value
        if self._compact:
            self.setMinimumHeight(24)
            self.setMaximumHeight(32)
        else:
            self.setMinimumHeight(40)
            self.setMaximumHeight(60)
        self.updateGeometry()  # Force layout update

    # ///////////////////////////////////////////////////////////////
    # EVENT HANDLERS
    # ///////////////////////////////////////////////////////////////

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events for drag start.

        Args:
            event: The mouse event.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse movement for drag & drop.

        Args:
            event: The mouse event.
        """
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        if not self.is_dragging:
            if (
                event.position().toPoint() - self.drag_start_pos
            ).manhattanLength() < 10:
                return

            self.is_dragging = True
            self.setProperty("dragging", True)
            self.style().unpolish(self)
            self.style().polish(self)

            # Create drag
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.item_id)
            drag.setMimeData(mime_data)

            # Execute drag
            drag.exec(Qt.DropAction.MoveAction)

            # Cleanup after drag
            self.is_dragging = False
            self.setProperty("dragging", False)
            self.style().unpolish(self)
            self.style().polish(self)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release events for drag end.

        Args:
            event: The mouse event.
        """
        self.is_dragging = False
        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().mouseReleaseEvent(event)

    # ///////////////////////////////////////////////////////////////
    # OVERRIDE METHODS
    # ///////////////////////////////////////////////////////////////

    def sizeHint(self) -> QSize:
        """Get the recommended size for the widget based on content.

        Returns:
            The recommended size.
        """
        # Get suggested size from HoverLabel
        content_size = self.content_widget.sizeHint()

        # Add layout margins and padding
        layout = self.layout()
        if layout is None:
            return QSize(content_size.width(), content_size.height())
        layout_margins = layout.contentsMargins()

        # Calculate total width
        total_width = (
            content_size.width() + layout_margins.left() + layout_margins.right()
        )

        # Calculate total height based on compact mode
        if self._compact:
            min_height = max(
                24,
                content_size.height() + layout_margins.top() + layout_margins.bottom(),
            )
            max_height = 32
        else:
            min_height = max(
                40,
                content_size.height() + layout_margins.top() + layout_margins.bottom(),
            )
            max_height = 60

        return QSize(total_width, min(min_height, max_height))

    def minimumSizeHint(self) -> QSize:
        """Get the minimum size for the widget.

        Returns:
            The minimum size hint.
        """
        # Get minimum size from HoverLabel
        content_min_size = self.content_widget.minimumSizeHint()

        # Add layout margins
        layout = self.layout()
        if layout is None:
            return QSize(content_min_size.width(), content_min_size.height())
        layout_margins = layout.contentsMargins()

        # Minimum width based on content + margins
        min_width = (
            content_min_size.width() + layout_margins.left() + layout_margins.right()
        )

        # Minimum height based on compact mode
        min_height = 24 if self._compact else 40

        return QSize(min_width, min_height)

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


class DraggableList(QWidget):
    """List widget with reorderable items via drag & drop and removal.

    This widget allows managing a list of items that users can reorder by
    drag & drop and remove individually.

    Features:
        - List of items reorderable by drag & drop
        - Item removal via HoverLabel (red icon on hover)
        - Consistent interface with HoverLabel for all items
        - Signals for reordering and removal events
        - Smooth and intuitive interface
        - Appearance customization
        - Automatic item order management
        - Integrated removal icon in HoverLabel

    Use cases:
        - Reorderable task list
        - Option selector with customizable order
        - File management interface
        - Priority-ordered element configuration

    Args:
        parent: The parent widget (default: None).
        items: Initial list of items (default: []).
        allow_drag_drop: Allow drag & drop for reordering (default: True).
        allow_remove: Allow item removal via HoverLabel (default: True).
        max_height: Maximum height of the widget (default: 300).
        min_width: Minimum width of the widget (default: 150).
        compact: Display items in compact mode (reduced height) (default: False).
        *args: Additional arguments passed to item widgets.
        **kwargs: Additional keyword arguments passed to item widgets.

    Signals:
        itemMoved(str, int, int): Emitted when an item is moved
            (item_id, old_position, new_position).
        itemRemoved(str, int): Emitted when an item is removed
            (item_id, position).
        itemAdded(str, int): Emitted when an item is added
            (item_id, position).
        itemClicked(str): Emitted when an item is clicked (item_id).
        orderChanged(list): Emitted when the item order changes
            (new ordered list).

    Example:
        >>> draggable_list = DraggableList(
        ...     items=["Item 1", "Item 2", "Item 3"],
        ...     icon="https://img.icons8.com/?size=100&id=8329&format=png&color=000000"
        ... )
        >>> draggable_list.itemMoved.connect(
        ...     lambda item_id, old_pos, new_pos: print(f"Moved {item_id} from {old_pos} to {new_pos}")
        ... )
        >>> draggable_list.itemRemoved.connect(
        ...     lambda item_id, pos: print(f"Removed {item_id} at {pos}")
        ... )
    """

    itemMoved = Signal(str, int, int)  # item_id, old_position, new_position
    itemRemoved = Signal(str, int)  # item_id, position
    itemAdded = Signal(str, int)  # item_id, position
    itemClicked = Signal(str)  # item_id
    orderChanged = Signal(list)  # new ordered list

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(
        self,
        parent: QWidget | None = None,
        items: list[str] | None = None,
        allow_drag_drop: bool = True,
        allow_remove: bool = True,
        max_height: int = 300,
        min_width: int = 150,
        compact: bool = False,
        *args: Any,  # noqa: ARG002
        **kwargs: Any,
    ) -> None:
        """Initialize the draggable list."""
        super().__init__(parent)
        self.setProperty("type", "DraggableList")

        # Initialize attributes
        self._items: list[str] = items or []
        self._allow_drag_drop: bool = allow_drag_drop
        self._allow_remove: bool = allow_remove
        self._max_height: int = max_height
        self._min_width: int = min_width
        self._compact: bool = compact
        self._item_widgets: dict[str, DraggableItem] = {}
        self._kwargs = kwargs
        self._icon_color = "grey"  # Default icon color

        # Configure widget
        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumWidth(min_width)
        self.setMaximumHeight(max_height)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Container widget for items
        self.container_widget = QWidget()
        self.container_layout = QVBoxLayout(self.container_widget)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(4)
        self.container_layout.addStretch()  # Flexible space at the end

        self.scroll_area.setWidget(self.container_widget)
        layout.addWidget(self.scroll_area)

        # Initialize items
        self._create_items()

    # ///////////////////////////////////////////////////////////////
    # PROPERTIES
    # ///////////////////////////////////////////////////////////////

    @property
    def items(self) -> list[str]:
        """Get the list of items.

        Returns:
            A copy of the current items list.
        """
        return self._items.copy()

    @items.setter
    def items(self, value: list[str]) -> None:
        """Set the list of items.

        Args:
            value: The new items list.
        """
        self._items = value.copy()
        self._create_items()

    @property
    def item_count(self) -> int:
        """Get the number of items in the list.

        Returns:
            The number of items (read-only).
        """
        return len(self._items)

    @property
    def allow_drag_drop(self) -> bool:
        """Get whether drag & drop is allowed.

        Returns:
            True if drag & drop is allowed, False otherwise.
        """
        return self._allow_drag_drop

    @allow_drag_drop.setter
    def allow_drag_drop(self, value: bool) -> None:
        """Set whether drag & drop is allowed.

        Args:
            value: Whether to allow drag & drop.
        """
        self._allow_drag_drop = value

    @property
    def allow_remove(self) -> bool:
        """Get whether item removal is allowed.

        Returns:
            True if removal is allowed, False otherwise.
        """
        return self._allow_remove

    @allow_remove.setter
    def allow_remove(self, value: bool) -> None:
        """Set whether item removal is allowed.

        Args:
            value: Whether to allow item removal.
        """
        self._allow_remove = value
        for widget in self._item_widgets.values():
            widget.content_widget.icon_enabled = value

    @property
    def icon_color(self) -> str:
        """Get the icon color of the items.

        Returns:
            The current icon color.
        """
        return self._icon_color

    @icon_color.setter
    def icon_color(self, value: str) -> None:
        """Set the icon color for all items.

        Args:
            value: The new icon color.
        """
        self._icon_color = value
        for widget in self._item_widgets.values():
            widget.icon_color = value

    @property
    def compact(self) -> bool:
        """Get the compact mode.

        Returns:
            True if compact mode is enabled, False otherwise.
        """
        return self._compact

    @compact.setter
    def compact(self, value: bool) -> None:
        """Set the compact mode and update all items.

        Args:
            value: Whether to enable compact mode.
        """
        self._compact = value
        for widget in self._item_widgets.values():
            widget.compact = value

    @property
    def min_width(self) -> int:
        """Get the minimum width of the widget.

        Returns:
            The minimum width.
        """
        return self._min_width

    @min_width.setter
    def min_width(self, value: int) -> None:
        """Set the minimum width of the widget.

        Args:
            value: The new minimum width.
        """
        self._min_width = value
        self.updateGeometry()  # Force layout update

    # ///////////////////////////////////////////////////////////////
    # PUBLIC METHODS
    # ///////////////////////////////////////////////////////////////

    def add_item(self, item_id: str, text: str | None = None) -> None:
        """Add an item to the list.

        Args:
            item_id: Unique identifier for the item.
            text: Text to display (uses item_id if None).
        """
        if item_id in self._items:
            return  # Item already present

        text = text or item_id
        self._items.append(item_id)

        # Create widget
        item_widget = DraggableItem(
            item_id=item_id, text=text, compact=self._compact, **self._kwargs
        )

        # Connect signals
        item_widget.itemRemoved.connect(self._on_item_removed)

        # Hide removal icon if necessary
        if not self._allow_remove:
            item_widget.content_widget.icon_enabled = False

        # Add to layout (before stretch)
        self.container_layout.insertWidget(len(self._items) - 1, item_widget)
        self._item_widgets[item_id] = item_widget

        # Emit signal
        self.itemAdded.emit(item_id, len(self._items) - 1)
        self.orderChanged.emit(self._items.copy())

    def remove_item(self, item_id: str) -> bool:
        """Remove an item from the list.

        Args:
            item_id: Identifier of the item to remove.

        Returns:
            True if the item was removed, False otherwise.
        """
        if item_id not in self._items:
            return False

        # Remove from list
        position = self._items.index(item_id)
        self._items.remove(item_id)

        # Remove widget
        if item_id in self._item_widgets:
            widget = self._item_widgets[item_id]
            self.container_layout.removeWidget(widget)
            widget.deleteLater()
            del self._item_widgets[item_id]

        # Emit signals
        self.itemRemoved.emit(item_id, position)
        self.orderChanged.emit(self._items.copy())

        return True

    def clear_items(self) -> None:
        """Remove all items from the list."""
        # Clean up widgets
        for widget in self._item_widgets.values():
            self.container_layout.removeWidget(widget)
            widget.deleteLater()
        self._item_widgets.clear()

        # Clear list
        self._items.clear()

        # Emit signal
        self.orderChanged.emit([])

    def move_item(self, item_id: str, new_position: int) -> bool:
        """Move an item to a new position.

        Args:
            item_id: Identifier of the item to move.
            new_position: New position (0-based).

        Returns:
            True if the item was moved, False otherwise.
        """
        if item_id not in self._items:
            return False

        old_position = self._items.index(item_id)
        if old_position == new_position:
            return True

        # Move in list
        self._items.pop(old_position)
        self._items.insert(new_position, item_id)

        # Move widget
        if item_id in self._item_widgets:
            widget = self._item_widgets[item_id]
            self.container_layout.removeWidget(widget)
            self.container_layout.insertWidget(new_position, widget)

        # Emit signals
        self.itemMoved.emit(item_id, old_position, new_position)
        self.orderChanged.emit(self._items.copy())

        return True

    def get_item_position(self, item_id: str) -> int:
        """Get the position of an item.

        Args:
            item_id: Identifier of the item.

        Returns:
            Position of the item (-1 if not found).
        """
        try:
            return self._items.index(item_id)
        except ValueError:
            return -1

    # ------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------

    def _create_items(self) -> None:
        """Create widgets for all items."""
        # Clean up existing widgets
        for widget in self._item_widgets.values():
            self.container_layout.removeWidget(widget)
            widget.deleteLater()
        self._item_widgets.clear()

        # Create new widgets
        for i, item_id in enumerate(self._items):
            item_widget = DraggableItem(
                item_id=item_id, text=item_id, compact=self._compact, **self._kwargs
            )

            # Connect signals
            item_widget.itemRemoved.connect(self._on_item_removed)

            # Hide removal icon if necessary
            if not self._allow_remove:
                item_widget.content_widget.icon_enabled = False

            # Add to layout
            self.container_layout.insertWidget(i, item_widget)
            self._item_widgets[item_id] = item_widget

    def _on_item_removed(self, item_id: str) -> None:
        """Handle item removal."""
        self.remove_item(item_id)

    def _calculate_drop_position(self, drop_pos: QPoint) -> int:
        """Calculate drop position based on coordinates.

        Args:
            drop_pos: Drop position coordinates.

        Returns:
            The calculated drop position index.
        """
        # Convert global coordinates to container local coordinates
        local_pos = self.container_widget.mapFrom(self, drop_pos)

        # Find position in layout
        for i in range(self.container_layout.count() - 1):  # -1 to exclude stretch
            item = self.container_layout.itemAt(i)
            widget = item.widget() if item else None
            if widget is not None:
                widget_rect = widget.geometry()
                if local_pos.y() < widget_rect.center().y():
                    return i

        return len(self._items) - 1

    # ///////////////////////////////////////////////////////////////
    # EVENT HANDLERS
    # ///////////////////////////////////////////////////////////////

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter events.

        Args:
            event: The drag enter event.
        """
        if self._allow_drag_drop and event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Handle drag move events.

        Args:
            event: The drag move event.
        """
        if self._allow_drag_drop and event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop events.

        Args:
            event: The drop event.
        """
        if not self._allow_drag_drop:
            return

        item_id = event.mimeData().text()
        if item_id not in self._items:
            return

        # Calculate new position
        drop_pos = event.position().toPoint()
        new_position = self._calculate_drop_position(drop_pos)

        # Move item
        self.move_item(item_id, new_position)

        event.acceptProposedAction()

    # ///////////////////////////////////////////////////////////////
    # OVERRIDE METHODS
    # ///////////////////////////////////////////////////////////////

    def sizeHint(self) -> QSize:
        """Get the recommended size for the widget based on content.

        Returns:
            The recommended size.
        """
        # Calculate maximum width of items
        max_item_width = 0

        if self._item_widgets:
            # Get maximum width of existing items
            item_widths = [
                widget.sizeHint().width() for widget in self._item_widgets.values()
            ]
            max_item_width = max(item_widths) if item_widths else 0

        # Use minimum width only if necessary
        if max_item_width < self._min_width:
            max_item_width = self._min_width

        # Add main widget margins
        margins = self.contentsMargins()
        total_width = max_item_width + margins.left() + margins.right()

        # Calculate height based on number of items
        item_height = 50  # Approximate item height
        spacing = 4  # Spacing between items
        total_items_height = len(self._item_widgets) * (item_height + spacing)

        # Add margins and limit to maximum height
        total_height = min(
            total_items_height + margins.top() + margins.bottom(), self._max_height
        )

        return QSize(total_width, max(200, total_height))

    def minimumSizeHint(self) -> QSize:
        """Get the minimum size for the widget.

        Returns:
            The minimum size hint.
        """
        # Minimum width based on items or configured minimum width
        min_width = 0

        if self._item_widgets:
            # Get minimum width of existing items
            item_min_widths = [
                widget.minimumSizeHint().width()
                for widget in self._item_widgets.values()
            ]
            min_width = max(item_min_widths) if item_min_widths else 0

        # Use minimum width only if necessary
        if min_width < self._min_width:
            min_width = self._min_width

        # Add margins
        margins = self.contentsMargins()
        total_width = min_width + margins.left() + margins.right()

        # Minimum height based on at least one item
        item_min_height = 40  # Minimum item height
        spacing = 4  # Spacing
        min_height = item_min_height + spacing + margins.top() + margins.bottom()

        return QSize(total_width, min_height)

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
