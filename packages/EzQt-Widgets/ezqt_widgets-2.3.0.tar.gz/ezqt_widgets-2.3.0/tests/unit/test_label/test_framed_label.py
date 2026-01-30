# ///////////////////////////////////////////////////////////////
# TEST_FRAMED_LABEL - FramedLabel Widget Tests
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Unit tests for FramedLabel widget.

Tests for the flexible label widget based on QFrame.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
import pytest
from PySide6.QtCore import QSize, Qt

# Local imports
from ezqt_widgets.label.framed_label import FramedLabel

pytestmark = pytest.mark.unit

# ///////////////////////////////////////////////////////////////
# TEST CLASSES
# ///////////////////////////////////////////////////////////////


class TestFramedLabel:
    """Tests for FramedLabel class."""

    def test_framed_label_creation_default(self, qt_widget_cleanup) -> None:
        """Test creation with default parameters."""
        label = FramedLabel()

        assert label is not None
        assert isinstance(label, FramedLabel)
        assert label.text == ""
        assert label.alignment == Qt.AlignmentFlag.AlignCenter
        assert label.min_width is None
        assert label.min_height is None

    def test_framed_label_creation_with_parameters(self, qt_widget_cleanup) -> None:
        """Test creation with custom parameters."""
        label = FramedLabel(
            text="Test Label",
            alignment=Qt.AlignmentFlag.AlignLeft,
            style_sheet="background-color: red;",
            min_width=200,
            min_height=50,
        )

        assert label.text == "Test Label"
        assert label.alignment == Qt.AlignmentFlag.AlignLeft
        assert label.min_width == 200
        assert label.min_height == 50

    def test_framed_label_properties(self, qt_widget_cleanup) -> None:
        """Test label properties."""
        label = FramedLabel()

        # Test text property
        label.text = "New Text"
        assert label.text == "New Text"

        # Test alignment property
        label.alignment = Qt.AlignmentFlag.AlignRight
        assert label.alignment == Qt.AlignmentFlag.AlignRight

        # Test min_width property
        label.min_width = 150
        assert label.min_width == 150

        # Test min_height property
        label.min_height = 40
        assert label.min_height == 40

        # Test with None
        label.min_width = None
        label.min_height = None
        assert label.min_width is None
        assert label.min_height is None

    def test_framed_label_signals(self, qt_widget_cleanup) -> None:
        """Test label signals."""
        label = FramedLabel()

        # Test textChanged signal
        signal_received = False
        received_text = ""

        def on_text_changed(text: str) -> None:
            nonlocal signal_received, received_text
            signal_received = True
            received_text = text

        label.textChanged.connect(on_text_changed)

        # Change text
        label.text = "Signal Test"

        # Verify that the signal was emitted
        assert signal_received
        assert received_text == "Signal Test"

    def test_framed_label_size_hints(self, qt_widget_cleanup) -> None:
        """Test size hint methods."""
        label = FramedLabel(text="Test Label")

        # Test minimumSizeHint
        min_size_hint = label.minimumSizeHint()
        assert min_size_hint is not None
        assert isinstance(min_size_hint, QSize)
        assert min_size_hint.width() > 0
        assert min_size_hint.height() > 0

    def test_framed_label_refresh_style(self, qt_widget_cleanup) -> None:
        """Test refresh_style method."""
        label = FramedLabel()

        # Method should not raise an exception
        try:
            label.refresh_style()
        except Exception as e:
            pytest.fail(f"refresh_style() raised an exception: {e}")

    def test_framed_label_alignment_options(self, qt_widget_cleanup) -> None:
        """Test different alignment options."""
        # Test alignment left
        label_left = FramedLabel(alignment=Qt.AlignmentFlag.AlignLeft)
        assert label_left.alignment == Qt.AlignmentFlag.AlignLeft

        # Test alignment center
        label_center = FramedLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        assert label_center.alignment == Qt.AlignmentFlag.AlignCenter

        # Test alignment right
        label_right = FramedLabel(alignment=Qt.AlignmentFlag.AlignRight)
        assert label_right.alignment == Qt.AlignmentFlag.AlignRight

        # Test alignment top
        label_top = FramedLabel(alignment=Qt.AlignmentFlag.AlignTop)
        assert label_top.alignment == Qt.AlignmentFlag.AlignTop

        # Test alignment bottom
        label_bottom = FramedLabel(alignment=Qt.AlignmentFlag.AlignBottom)
        assert label_bottom.alignment == Qt.AlignmentFlag.AlignBottom

    def test_framed_label_text_changes(self, qt_widget_cleanup) -> None:
        """Test text changes."""
        label = FramedLabel()

        # Empty text
        label.text = ""
        assert label.text == ""

        # Text with spaces
        label.text = "   Text with spaces   "
        assert label.text == "   Text with spaces   "

        # Long text
        long_text = (
            "This is a very long text that should be handled properly "
            "by the FramedLabel widget"
        )
        label.text = long_text
        assert label.text == long_text

        # Text with special characters
        special_text = "Text with special chars: éàùç€£¥"
        label.text = special_text
        assert label.text == special_text

    def test_framed_label_style_sheet(self, qt_widget_cleanup) -> None:
        """Test stylesheet application."""
        # Create a label with stylesheet
        style_sheet = "background-color: #FF0000; color: white; border: 2px solid blue;"
        label = FramedLabel(style_sheet=style_sheet)

        # Verify that the stylesheet is applied
        # Note: We can't easily test visual rendering in unit tests
        # but we can verify that the widget is created without error
        assert label is not None
        assert isinstance(label, FramedLabel)

    def test_framed_label_dimensions(self, qt_widget_cleanup) -> None:
        """Test minimum dimensions."""
        label = FramedLabel(min_width=100, min_height=30)

        # Verify initial dimensions
        assert label.min_width == 100
        assert label.min_height == 30

        # Modify dimensions
        label.min_width = 200
        label.min_height = 50
        assert label.min_width == 200
        assert label.min_height == 50

        # Test with negative values
        label.min_width = -10
        label.min_height = -5
        assert label.min_width == -10
        assert label.min_height == -5

    def test_framed_label_property_type(self, qt_widget_cleanup) -> None:
        """Test type property for QSS."""
        label = FramedLabel()

        # Verify that the type property is defined
        assert label.property("type") == "FramedLabel"

    def test_framed_label_multiple_instances(self, qt_widget_cleanup) -> None:
        """Test multiple instances."""
        # Create multiple instances
        label1 = FramedLabel(text="Label 1")
        label2 = FramedLabel(text="Label 2")
        label3 = FramedLabel(text="Label 3")

        # Verify that each instance is independent
        assert label1.text == "Label 1"
        assert label2.text == "Label 2"
        assert label3.text == "Label 3"

        # Modify one instance
        label1.text = "Modified Label 1"
        assert label1.text == "Modified Label 1"
        assert label2.text == "Label 2"  # Not affected
        assert label3.text == "Label 3"  # Not affected

    def test_framed_label_empty_constructor(self, qt_widget_cleanup) -> None:
        """Test constructor without parameters."""
        label = FramedLabel()

        # Verify default values
        assert label.text == ""
        assert label.alignment == Qt.AlignmentFlag.AlignCenter
        assert label.min_width is None
        assert label.min_height is None

    def test_framed_label_text_property_changes(self, qt_widget_cleanup) -> None:
        """Test text property changes."""
        label = FramedLabel()

        # Change text multiple times
        label.text = "First text"
        assert label.text == "First text"

        label.text = "Second text"
        assert label.text == "Second text"

        label.text = "Third text"
        assert label.text == "Third text"

        # Return to empty text
        label.text = ""
        assert label.text == ""
