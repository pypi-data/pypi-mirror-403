# ///////////////////////////////////////////////////////////////
# TEST_DRAGGABLE_LIST - DraggableList Widget Tests
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Unit tests for DraggableList widget.

This module contains all tests necessary to validate the proper functioning
of the DraggableList widget and its DraggableItem components.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
import pytest
from PySide6.QtCore import QMimeData, QPoint, Qt
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QMouseEvent

# Local imports
from ezqt_widgets.misc.draggable_list import DraggableItem, DraggableList

# ///////////////////////////////////////////////////////////////
# FIXTURES
# ///////////////////////////////////////////////////////////////


@pytest.fixture
def app(qt_application):
    """Fixture to use the global Qt application."""
    return qt_application


@pytest.fixture
def _app(app):
    """Alias fixture for app when not directly used."""
    return app


@pytest.fixture
def draggable_list(_app):
    """Fixture to create a test DraggableList."""
    return DraggableList(
        items=["Item 1", "Item 2", "Item 3"],
        allow_drag_drop=True,
        allow_remove=True,
        max_height=300,
        min_width=150,
        compact=False,
    )


@pytest.fixture
def compact_draggable_list(_app):
    """Fixture to create a compact test DraggableList."""
    return DraggableList(
        items=["Option A", "Option B"],
        compact=True,
        allow_drag_drop=True,
        allow_remove=True,
    )


@pytest.fixture
def draggable_item(_app):
    """Fixture to create a test DraggableItem."""
    return DraggableItem(item_id="test_item", text="Test Item", compact=False)


# ///////////////////////////////////////////////////////////////
# TEST CLASSES
# ///////////////////////////////////////////////////////////////


class TestDraggableItem:
    """Tests for DraggableItem class."""

    def test_init(self, draggable_item) -> None:
        """Test DraggableItem initialization."""
        assert draggable_item.item_id == "test_item"
        assert draggable_item.text == "Test Item"
        assert draggable_item.is_dragging is False
        assert draggable_item._compact is False
        assert draggable_item._icon_color == "grey"

    def test_init_compact(self, app) -> None:
        """Test DraggableItem initialization in compact mode."""
        item = DraggableItem(item_id="compact_item", text="Compact Item", compact=True)
        assert item._compact is True
        assert item.minimumHeight() == 24
        assert item.maximumHeight() == 32

    def test_icon_color_property(self, draggable_item) -> None:
        """Test icon_color property."""
        draggable_item.icon_color = "red"
        assert draggable_item.icon_color == "red"
        assert draggable_item.content_widget.icon_color == "red"

    def test_compact_property(self, draggable_item) -> None:
        """Test compact property."""
        # Normal mode
        assert draggable_item.compact is False
        assert draggable_item.minimumHeight() == 40
        assert draggable_item.maximumHeight() == 60

        # Compact mode
        draggable_item.compact = True
        assert draggable_item.compact is True
        assert draggable_item.minimumHeight() == 24
        assert draggable_item.maximumHeight() == 32

    def test_size_hint(self, draggable_item) -> None:
        """Test sizeHint calculation."""
        size = draggable_item.sizeHint()
        assert size.width() > 0
        assert 40 <= size.height() <= 60

    def test_size_hint_compact(self, _app) -> None:
        """Test sizeHint calculation in compact mode."""
        item = DraggableItem(item_id="compact_item", text="Compact Item", compact=True)
        size = item.sizeHint()
        assert size.width() > 0
        assert 24 <= size.height() <= 32

    def test_minimum_size_hint(self, draggable_item) -> None:
        """Test minimumSizeHint calculation."""
        size = draggable_item.minimumSizeHint()
        assert size.width() > 0
        assert size.height() == 40

    def test_minimum_size_hint_compact(self, _app) -> None:
        """Test minimumSizeHint calculation in compact mode."""
        item = DraggableItem(item_id="compact_item", text="Compact Item", compact=True)
        size = item.minimumSizeHint()
        assert size.width() > 0
        assert size.height() == 24

    def test_mouse_press_event(self, draggable_item) -> None:
        """Test mousePressEvent."""
        # Simulate left click
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(10, 10),
            QPoint(10, 10),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        draggable_item.mousePressEvent(event)
        assert draggable_item.drag_start_pos == QPoint(10, 10)

    def test_on_remove_clicked(self, draggable_item) -> None:
        """Test itemRemoved signal."""
        # Connect a callback to verify signal emission
        called = False

        def callback(item_id: str) -> None:
            nonlocal called
            called = True
            assert item_id == "test_item"

        draggable_item.itemRemoved.connect(callback)
        draggable_item._on_remove_clicked()
        assert called is True

    def test_refresh_style(self, draggable_item) -> None:
        """Test refresh_style method."""
        # This method should not raise an exception
        draggable_item.refresh_style()


class TestDraggableList:
    """Tests for DraggableList class."""

    def test_init(self, draggable_list) -> None:
        """Test DraggableList initialization."""
        assert draggable_list._items == ["Item 1", "Item 2", "Item 3"]
        assert draggable_list._allow_drag_drop is True
        assert draggable_list._allow_remove is True
        assert draggable_list._max_height == 300
        assert draggable_list._min_width == 150
        assert draggable_list._compact is False
        assert draggable_list._icon_color == "grey"
        assert len(draggable_list._item_widgets) == 3

    def test_init_compact(self, compact_draggable_list) -> None:
        """Test compact DraggableList initialization."""
        assert compact_draggable_list._compact is True
        assert compact_draggable_list._items == ["Option A", "Option B"]
        assert len(compact_draggable_list._item_widgets) == 2

    def test_items_property(self, draggable_list) -> None:
        """Test items property."""
        # Getter
        items = draggable_list.items
        assert items == ["Item 1", "Item 2", "Item 3"]
        assert items is not draggable_list._items  # Copy

        # Setter
        new_items = ["New 1", "New 2"]
        draggable_list.items = new_items
        assert draggable_list._items == new_items
        assert len(draggable_list._item_widgets) == 2

    def test_item_count_property(self, draggable_list) -> None:
        """Test item_count property."""
        assert draggable_list.item_count == 3

    def test_allow_drag_drop_property(self, draggable_list) -> None:
        """Test allow_drag_drop property."""
        assert draggable_list.allow_drag_drop is True

        draggable_list.allow_drag_drop = False
        assert draggable_list.allow_drag_drop is False

    def test_allow_remove_property(self, draggable_list) -> None:
        """Test allow_remove property."""
        assert draggable_list.allow_remove is True

        draggable_list.allow_remove = False
        assert draggable_list.allow_remove is False

        # Verify that remove icon is disabled
        for widget in draggable_list._item_widgets.values():
            assert widget.content_widget.icon_enabled is False

    def test_icon_color_property(self, draggable_list) -> None:
        """Test icon_color property."""
        assert draggable_list.icon_color == "grey"

        draggable_list.icon_color = "red"
        assert draggable_list.icon_color == "red"

        # Verify that all items have the new color
        for widget in draggable_list._item_widgets.values():
            assert widget.icon_color == "red"

    def test_compact_property(self, draggable_list) -> None:
        """Test compact property."""
        assert draggable_list.compact is False

        draggable_list.compact = True
        assert draggable_list.compact is True

        # Verify that all items are in compact mode
        for widget in draggable_list._item_widgets.values():
            assert widget.compact is True

    def test_min_width_property(self, draggable_list) -> None:
        """Test min_width property."""
        assert draggable_list.min_width == 150

        draggable_list.min_width = 200
        assert draggable_list.min_width == 200

    def test_add_item(self, draggable_list) -> None:
        """Test adding an item."""
        initial_count = draggable_list.item_count

        # Connect a callback to verify signal emission
        called = False

        def callback(item_id: str, position: int) -> None:
            nonlocal called
            called = True
            assert item_id == "new_item"
            assert position == initial_count

        draggable_list.itemAdded.connect(callback)

        draggable_list.add_item("new_item", "New Item")

        assert draggable_list.item_count == initial_count + 1
        assert "new_item" in draggable_list._items
        assert "new_item" in draggable_list._item_widgets
        assert called is True

    def test_add_item_duplicate(self, draggable_list) -> None:
        """Test adding an already present item."""
        initial_count = draggable_list.item_count
        draggable_list.add_item("Item 1", "Item 1")  # Already present
        assert draggable_list.item_count == initial_count  # No addition

    def test_remove_item(self, draggable_list) -> None:
        """Test removing an item."""
        initial_count = draggable_list.item_count

        # Connect a callback to verify signal emission
        called = False

        def callback(item_id: str, position: int) -> None:
            nonlocal called
            called = True
            assert item_id == "Item 2"
            assert position == 1

        draggable_list.itemRemoved.connect(callback)

        result = draggable_list.remove_item("Item 2")

        assert result is True
        assert draggable_list.item_count == initial_count - 1
        assert "Item 2" not in draggable_list._items
        assert "Item 2" not in draggable_list._item_widgets
        assert called is True

    def test_remove_item_not_found(self, draggable_list) -> None:
        """Test removing a non-existent item."""
        initial_count = draggable_list.item_count
        result = draggable_list.remove_item("inexistant")
        assert result is False
        assert draggable_list.item_count == initial_count

    def test_clear_items(self, draggable_list) -> None:
        """Test clearing the list."""
        assert draggable_list.item_count > 0

        # Connect a callback to verify signal emission
        called = False

        def callback(new_order: list[str]) -> None:
            nonlocal called
            called = True
            assert new_order == []

        draggable_list.orderChanged.connect(callback)

        draggable_list.clear_items()

        assert draggable_list.item_count == 0
        assert len(draggable_list._items) == 0
        assert len(draggable_list._item_widgets) == 0
        assert called is True

    def test_move_item(self, draggable_list) -> None:
        """Test moving an item."""
        # Connect a callback to verify signal emission
        called = False

        def callback(item_id: str, old_pos: int, new_pos: int) -> None:
            nonlocal called
            called = True
            assert item_id == "Item 1"
            assert old_pos == 0
            assert new_pos == 2

        draggable_list.itemMoved.connect(callback)

        result = draggable_list.move_item("Item 1", 2)

        assert result is True
        assert draggable_list._items == ["Item 2", "Item 3", "Item 1"]
        assert called is True

    def test_move_item_same_position(self, draggable_list) -> None:
        """Test moving an item to the same position."""
        original_items = draggable_list._items.copy()
        result = draggable_list.move_item("Item 1", 0)
        assert result is True
        assert draggable_list._items == original_items

    def test_move_item_not_found(self, draggable_list) -> None:
        """Test moving a non-existent item."""
        result = draggable_list.move_item("inexistant", 1)
        assert result is False

    def test_get_item_position(self, draggable_list) -> None:
        """Test getting an item's position."""
        position = draggable_list.get_item_position("Item 2")
        assert position == 1

    def test_get_item_position_not_found(self, draggable_list) -> None:
        """Test getting position of a non-existent item."""
        position = draggable_list.get_item_position("inexistant")
        assert position == -1

    def test_size_hint(self, draggable_list) -> None:
        """Test sizeHint calculation."""
        size = draggable_list.sizeHint()
        assert size.width() >= draggable_list._min_width
        assert size.height() > 0

    def test_minimum_size_hint(self, draggable_list) -> None:
        """Test minimumSizeHint calculation."""
        size = draggable_list.minimumSizeHint()
        assert size.width() >= draggable_list._min_width
        assert size.height() > 0

    def test_drag_enter_event(self, draggable_list) -> None:
        """Test dragEnterEvent."""
        mime_data = QMimeData()
        mime_data.setText("Item 1")
        event = QDragEnterEvent(
            QPoint(10, 10),
            Qt.DropAction.MoveAction,
            mime_data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        # With drag & drop enabled
        draggable_list.allow_drag_drop = True
        draggable_list.dragEnterEvent(event)
        assert event.isAccepted()

        # With drag & drop disabled
        draggable_list.allow_drag_drop = False
        event = QDragEnterEvent(
            QPoint(10, 10),
            Qt.DropAction.MoveAction,
            mime_data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        draggable_list.dragEnterEvent(event)
        assert not event.isAccepted()

    def test_drag_move_event(self, draggable_list) -> None:
        """Test dragMoveEvent."""
        mime_data = QMimeData()
        mime_data.setText("Item 1")
        event = QDragMoveEvent(
            QPoint(10, 10),
            Qt.DropAction.MoveAction,
            mime_data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        # With drag & drop enabled
        draggable_list.allow_drag_drop = True
        draggable_list.dragMoveEvent(event)
        assert event.isAccepted()

        # With drag & drop disabled
        draggable_list.allow_drag_drop = False
        event = QDragMoveEvent(
            QPoint(10, 10),
            Qt.DropAction.MoveAction,
            mime_data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        draggable_list.dragMoveEvent(event)
        assert not event.isAccepted()

    def test_drop_event(self, draggable_list) -> None:
        """Test dropEvent."""
        mime_data = QMimeData()
        mime_data.setText("Item 1")
        event = QDropEvent(
            QPoint(10, 10),
            Qt.DropAction.MoveAction,
            mime_data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )

        # With drag & drop enabled and valid item
        draggable_list.allow_drag_drop = True
        draggable_list.dropEvent(event)
        assert event.isAccepted()

        # With non-existent item
        mime_data.setText("inexistant")
        event = QDropEvent(
            QPoint(10, 10),
            Qt.DropAction.MoveAction,
            mime_data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        draggable_list.dropEvent(event)
        assert not event.isAccepted()

    def test_calculate_drop_position(self, draggable_list) -> None:
        """Test drop position calculation."""
        # Test with a position at the top
        drop_pos = QPoint(10, 5)
        position = draggable_list._calculate_drop_position(drop_pos)
        assert position == 0

        # Test with a position at the bottom
        drop_pos = QPoint(10, 1000)
        position = draggable_list._calculate_drop_position(drop_pos)
        assert position == 2  # len(items) - 1

    def test_refresh_style(self, draggable_list) -> None:
        """Test refresh_style method."""
        # This method should not raise an exception
        draggable_list.refresh_style()

    def test_on_item_removed(self, draggable_list) -> None:
        """Test on_item_removed callback."""
        # Simulate item removal via signal
        draggable_list._on_item_removed("Item 1")
        assert "Item 1" not in draggable_list._items


class TestDraggableListIntegration:
    """Integration tests for DraggableList."""

    def test_signal_chain(self, draggable_list) -> None:
        """Test signal chain during operations."""
        signals_received: list[tuple[str, ...]] = []

        def on_item_moved(item_id: str, old_pos: int, new_pos: int) -> None:
            signals_received.append(("moved", item_id, old_pos, new_pos))

        def on_order_changed(new_order: list[str]) -> None:
            signals_received.append(("order_changed", new_order))

        draggable_list.itemMoved.connect(on_item_moved)
        draggable_list.orderChanged.connect(on_order_changed)

        # Move an item
        draggable_list.move_item("Item 1", 2)

        assert len(signals_received) == 2
        assert signals_received[0][0] == "moved"
        assert signals_received[1][0] == "order_changed"

    def test_compact_mode_switch(self, draggable_list) -> None:
        """Test compact mode switching."""
        # Verify initial state
        assert draggable_list.compact is False
        for widget in draggable_list._item_widgets.values():
            assert widget.compact is False

        # Switch to compact mode
        draggable_list.compact = True
        assert draggable_list.compact is True
        for widget in draggable_list._item_widgets.values():
            assert widget.compact is True

    def test_icon_color_propagation(self, draggable_list) -> None:
        """Test icon color propagation."""
        # Change color
        draggable_list.icon_color = "blue"

        # Verify that all items have the new color
        for widget in draggable_list._item_widgets.values():
            assert widget.icon_color == "blue"

    def test_allow_remove_propagation(self, draggable_list) -> None:
        """Test allow_remove propagation."""
        # Disable removal
        draggable_list.allow_remove = False

        # Verify that all items have removal disabled
        for widget in draggable_list._item_widgets.values():
            assert widget.content_widget.icon_enabled is False
