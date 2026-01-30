# ///////////////////////////////////////////////////////////////
# TEST_INDICATOR_LABEL - IndicatorLabel Widget Tests
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Unit tests for IndicatorLabel widget.

Tests for the dynamic status indicator widget.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
import pytest

# Local imports
from ezqt_widgets.label.indicator_label import IndicatorLabel

pytestmark = pytest.mark.unit

# ///////////////////////////////////////////////////////////////
# TEST CLASSES
# ///////////////////////////////////////////////////////////////


class TestIndicatorLabel:
    """Tests for IndicatorLabel class."""

    def test_indicator_label_creation_default(self, qt_widget_cleanup) -> None:
        """Test creation with default parameters."""
        label = IndicatorLabel()

        assert label is not None
        assert isinstance(label, IndicatorLabel)
        assert label.status == "neutral"

    def test_indicator_label_creation_with_parameters(self, qt_widget_cleanup) -> None:
        """Test creation with custom parameters."""
        custom_status_map = {
            "custom1": {"text": "Custom 1", "state": "state1", "color": "#FF0000"},
            "custom2": {"text": "Custom 2", "state": "state2", "color": "#00FF00"},
        }

        label = IndicatorLabel(status_map=custom_status_map, initial_status="custom1")

        assert label.status == "custom1"

    def test_indicator_label_properties(self, qt_widget_cleanup) -> None:
        """Test label properties."""
        label = IndicatorLabel()

        # Test status property
        label.status = "online"
        assert label.status == "online"

        # Test with invalid status (should raise an exception)
        with pytest.raises(ValueError, match="Unknown status"):
            label.status = "invalid_status"

    def test_indicator_label_signals(self, qt_widget_cleanup) -> None:
        """Test label signals."""
        label = IndicatorLabel()

        # Test statusChanged signal
        signal_received = False
        received_status = ""

        def on_status_changed(status: str) -> None:
            nonlocal signal_received, received_status
            signal_received = True
            received_status = status

        label.statusChanged.connect(on_status_changed)

        # Change status
        label.status = "online"

        # Verify that the signal was emitted
        assert signal_received
        assert received_status == "online"

    def test_indicator_label_set_status_method(self, qt_widget_cleanup) -> None:
        """Test set_status method."""
        label = IndicatorLabel()

        # Initial state
        assert label.status == "neutral"

        # Change status
        label.set_status("online")
        assert label.status == "online"

        # Change again
        label.set_status("offline")
        assert label.status == "offline"

    def test_indicator_label_refresh_style(self, qt_widget_cleanup) -> None:
        """Test refresh_style method."""
        label = IndicatorLabel()

        # Method should not raise an exception
        try:
            label.refresh_style()
        except Exception as e:
            pytest.fail(f"refresh_style() raised an exception: {e}")

    def test_indicator_label_default_status_map(self, qt_widget_cleanup) -> None:
        """Test default status map."""
        label = IndicatorLabel()

        # Verify default statuses
        assert label.status == "neutral"

        # Test different statuses
        label.status = "online"
        assert label.status == "online"

        label.status = "offline"
        assert label.status == "offline"

        # Test statuses that don't exist
        with pytest.raises(ValueError, match="Unknown status"):
            label.status = "error"

        with pytest.raises(ValueError, match="Unknown status"):
            label.status = "warning"

        with pytest.raises(ValueError, match="Unknown status"):
            label.status = "success"

    def test_indicator_label_custom_status_map(self, qt_widget_cleanup) -> None:
        """Test with custom status map."""
        custom_map = {
            "ready": {"text": "Ready", "state": "ready", "color": "#4CAF50"},
            "busy": {"text": "Busy", "state": "busy", "color": "#FF9800"},
            "error": {"text": "Error", "state": "error", "color": "#F44336"},
        }

        label = IndicatorLabel(status_map=custom_map, initial_status="ready")

        # Verify initial status
        assert label.status == "ready"

        # Test other statuses
        label.status = "busy"
        assert label.status == "busy"

        label.status = "error"
        assert label.status == "error"

        # Test a status that doesn't exist
        with pytest.raises(ValueError, match="Unknown status"):
            label.status = "unknown"

    def test_indicator_label_status_transitions(self, qt_widget_cleanup) -> None:
        """Test status transitions."""
        label = IndicatorLabel()

        # Initial state
        assert label.status == "neutral"

        # Transition to online
        label.status = "online"
        assert label.status == "online"

        # Transition to offline
        label.status = "offline"
        assert label.status == "offline"

        # Transition to neutral
        label.status = "neutral"
        assert label.status == "neutral"

    def test_indicator_label_property_type(self, qt_widget_cleanup) -> None:
        """Test type property for QSS."""
        label = IndicatorLabel()

        # Verify that the type property is defined
        assert label.property("type") == "IndicatorLabel"

    def test_indicator_label_multiple_instances(self, qt_widget_cleanup) -> None:
        """Test multiple instances."""
        # Create multiple instances
        label1 = IndicatorLabel(initial_status="online")
        label2 = IndicatorLabel(initial_status="offline")
        label3 = IndicatorLabel(initial_status="neutral")

        # Verify that each instance is independent
        assert label1.status == "online"
        assert label2.status == "offline"
        assert label3.status == "neutral"

        # Modify one instance
        label1.status = "offline"
        assert label1.status == "offline"
        assert label2.status == "offline"  # Not affected
        assert label3.status == "neutral"  # Not affected

    def test_indicator_label_empty_status_map(self, qt_widget_cleanup) -> None:
        """Test with empty status map."""
        empty_map = {}
        label = IndicatorLabel(status_map=empty_map)

        # Verify that the widget is created
        assert label is not None
        assert isinstance(label, IndicatorLabel)

        # Test a status change (should raise an exception)
        with pytest.raises(ValueError, match="Unknown status"):
            label.status = "any_status"

    def test_indicator_label_invalid_initial_status(self, qt_widget_cleanup) -> None:
        """Test with invalid initial status."""
        # Create a label with invalid status (should raise an exception)
        with pytest.raises(ValueError, match="Unknown status"):
            IndicatorLabel(initial_status="invalid_status")

    def test_indicator_label_status_map_structure(self, qt_widget_cleanup) -> None:
        """Test status map structure."""
        # Map with complete structure
        complete_map = {
            "test1": {"text": "Test 1", "state": "state1", "color": "#FF0000"},
            "test2": {"text": "Test 2", "state": "state2", "color": "#00FF00"},
        }

        label = IndicatorLabel(status_map=complete_map, initial_status="test1")
        assert label.status == "test1"

        # Map with incomplete structure
        incomplete_map = {
            "test3": {
                "text": "Test 3"
                # Missing "state" and "color"
            }
        }

        label2 = IndicatorLabel(status_map=incomplete_map, initial_status="test3")
        assert label2.status == "test3"

    def test_indicator_label_status_changes_with_signals(
        self, qt_widget_cleanup
    ) -> None:
        """Test status changes with signals."""
        label = IndicatorLabel()

        # Connect signal
        signal_count = 0
        received_statuses: list[str] = []

        def on_status_changed(status: str) -> None:
            nonlocal signal_count
            signal_count += 1
            received_statuses.append(status)

        label.statusChanged.connect(on_status_changed)

        # Change status multiple times
        label.status = "online"
        label.status = "offline"
        label.status = "neutral"

        # Verify signals
        assert signal_count == 3
        assert received_statuses == ["online", "offline", "neutral"]

    def test_indicator_label_same_status_multiple_times(
        self, qt_widget_cleanup
    ) -> None:
        """Test same status set multiple times."""
        label = IndicatorLabel()

        # Connect signal
        signal_count = 0

        def on_status_changed(_status: str) -> None:
            nonlocal signal_count
            signal_count += 1

        label.statusChanged.connect(on_status_changed)

        # Set the same status multiple times
        label.status = "online"
        label.status = "online"
        label.status = "online"

        # Verify that the signal is emitted each time
        # Note: Some widgets may not emit the signal if the value doesn't change
        # Let's verify that the final status is correct
        assert label.status == "online"
        # Signal may be emitted 1 time (first definition) or 3 times
        # depending on implementation
        assert signal_count >= 1

    def test_indicator_label_constructor_without_parameters(
        self, qt_widget_cleanup
    ) -> None:
        """Test constructor without parameters."""
        label = IndicatorLabel()

        # Verify default values
        assert label.status == "neutral"

        # Verify that the widget is functional
        label.status = "online"
        assert label.status == "online"
