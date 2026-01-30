# ///////////////////////////////////////////////////////////////
# TEST_TAB_REPLACE_TEXTEDIT - TabReplaceTextEdit Widget Tests
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Unit tests for TabReplaceTextEdit widget.

Tests for the text edit widget with tab replacement and sanitization.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Third-party imports
import pytest

# Local imports
from ezqt_widgets.input.tab_replace_textedit import TabReplaceTextEdit

pytestmark = pytest.mark.unit

# ///////////////////////////////////////////////////////////////
# TEST CLASSES
# ///////////////////////////////////////////////////////////////


class TestTabReplaceTextEdit:
    """Tests for TabReplaceTextEdit class."""

    def test_tab_replace_textedit_creation_default(self, qt_widget_cleanup) -> None:
        """Test creation with default parameters."""
        text_edit = TabReplaceTextEdit()

        assert text_edit is not None
        assert isinstance(text_edit, TabReplaceTextEdit)
        assert text_edit.tab_replacement == "\n"
        assert text_edit.sanitize_on_paste is True
        assert text_edit.remove_empty_lines is True
        assert text_edit.preserve_whitespace is False

    def test_tab_replace_textedit_creation_with_parameters(
        self, qt_widget_cleanup
    ) -> None:
        """Test creation with custom parameters."""
        text_edit = TabReplaceTextEdit(
            tab_replacement=" ",
            sanitize_on_paste=False,
            remove_empty_lines=False,
            preserve_whitespace=True,
        )

        assert text_edit.tab_replacement == " "
        assert text_edit.sanitize_on_paste is False
        assert text_edit.remove_empty_lines is False
        assert text_edit.preserve_whitespace is True

    def test_tab_replace_textedit_properties(self, qt_widget_cleanup) -> None:
        """Test widget properties."""
        text_edit = TabReplaceTextEdit()

        # Test tab_replacement property
        text_edit.tab_replacement = "  "
        assert text_edit.tab_replacement == "  "

        # Test sanitize_on_paste property
        text_edit.sanitize_on_paste = False
        assert text_edit.sanitize_on_paste is False

        # Test remove_empty_lines property
        text_edit.remove_empty_lines = False
        assert text_edit.remove_empty_lines is False

        # Test preserve_whitespace property
        text_edit.preserve_whitespace = True
        assert text_edit.preserve_whitespace is True

    def test_tab_replace_textedit_sanitize_text_basic(self, qt_widget_cleanup) -> None:
        """Test sanitize_text method with basic cases."""
        text_edit = TabReplaceTextEdit()

        # Test default tab replacement
        text = "col1\tcol2\tcol3"
        sanitized = text_edit.sanitize_text(text)
        assert sanitized == "col1\ncol2\ncol3"

        # Test without tabs
        text = "no tabs here"
        sanitized = text_edit.sanitize_text(text)
        assert sanitized == "no tabs here"

    def test_tab_replace_textedit_sanitize_text_custom_replacement(
        self, qt_widget_cleanup
    ) -> None:
        """Test sanitize_text with custom replacement."""
        text_edit = TabReplaceTextEdit(tab_replacement="  ")

        # Test replacement with spaces
        text = "col1\tcol2\tcol3"
        sanitized = text_edit.sanitize_text(text)
        assert sanitized == "col1  col2  col3"

        # Test replacement with comma
        text_edit.tab_replacement = ","
        text = "col1\tcol2\tcol3"
        sanitized = text_edit.sanitize_text(text)
        assert sanitized == "col1,col2,col3"

    def test_tab_replace_textedit_sanitize_text_remove_empty_lines(
        self, qt_widget_cleanup
    ) -> None:
        """Test sanitize_text with empty line removal."""
        text_edit = TabReplaceTextEdit(remove_empty_lines=True)

        # Test with empty lines
        text = "line1\n\nline2\n\t\nline3"
        sanitized = text_edit.sanitize_text(text)
        assert sanitized == "line1\nline2\nline3"

        # Test without empty lines
        text = "line1\nline2\nline3"
        sanitized = text_edit.sanitize_text(text)
        assert sanitized == "line1\nline2\nline3"

    def test_tab_replace_textedit_sanitize_text_preserve_empty_lines(
        self, qt_widget_cleanup
    ) -> None:
        """Test sanitize_text without empty line removal."""
        text_edit = TabReplaceTextEdit(remove_empty_lines=False)

        # Test with empty lines preserved
        text = "line1\n\nline2\n\t\nline3"
        sanitized = text_edit.sanitize_text(text)
        # Tabs become newlines by default, empty lines are preserved
        assert sanitized == "line1\n\nline2\n\n\nline3"

    def test_tab_replace_textedit_sanitize_text_preserve_whitespace(
        self, qt_widget_cleanup
    ) -> None:
        """Test sanitize_text with whitespace preservation."""
        text_edit = TabReplaceTextEdit(
            preserve_whitespace=True, remove_empty_lines=True
        )

        # Test with preserved spaces
        text = "  line1  \n  line2  \n  line3  "
        sanitized = text_edit.sanitize_text(text)
        # Verify that spaces are preserved
        assert "  line1  " in sanitized
        assert "  line2  " in sanitized
        assert "  line3  " in sanitized

        # Test without preserved spaces
        text_edit.preserve_whitespace = False
        sanitized = text_edit.sanitize_text(text)
        # Spaces are preserved but empty lines removed
        assert sanitized == "  line1  \n  line2  \n  line3  "

    def test_tab_replace_textedit_sanitize_text_complex(
        self, qt_widget_cleanup
    ) -> None:
        """Test sanitize_text with complex cases."""
        text_edit = TabReplaceTextEdit(
            tab_replacement="|",
            remove_empty_lines=True,
            preserve_whitespace=False,
        )

        # Test complex case
        text = (
            "  col1\t  col2  \tcol3  \n\n  col4\tcol5\t  col6  \n\t\ncol7\tcol8\tcol9"
        )
        sanitized = text_edit.sanitize_text(text)
        # Tabs become "|", empty lines are removed
        expected = "  col1|  col2  |col3  \n  col4|col5|  col6  \n|\ncol7|col8|col9"
        assert sanitized == expected

    def test_tab_replace_textedit_sanitize_text_mixed_content(
        self, qt_widget_cleanup
    ) -> None:
        """Test sanitize_text with mixed content."""
        text_edit = TabReplaceTextEdit(tab_replacement=" -> ", remove_empty_lines=True)

        # Test mixed content
        text = "header1\theader2\theader3\nvalue1\tvalue2\tvalue3\n\t\t\nfooter1\tfooter2\tfooter3"
        sanitized = text_edit.sanitize_text(text)
        # Tabs become " -> ", empty lines are removed
        expected = "header1 -> header2 -> header3\nvalue1 -> value2 -> value3\n ->  -> \nfooter1 -> footer2 -> footer3"
        assert sanitized == expected

    def test_tab_replace_textedit_sanitize_text_special_characters(
        self, qt_widget_cleanup
    ) -> None:
        """Test sanitize_text with special characters."""
        text_edit = TabReplaceTextEdit(tab_replacement="\t->\t")

        # Test special characters
        text = "email@domain.com\tuser-name_123\tfile/path\nspecial\tchars\there"
        sanitized = text_edit.sanitize_text(text)
        expected = "email@domain.com\t->\tuser-name_123\t->\tfile/path\nspecial\t->\tchars\t->\there"
        assert sanitized == expected

    def test_tab_replace_textedit_sanitize_text_unicode(
        self, qt_widget_cleanup
    ) -> None:
        """Test sanitize_text with Unicode characters."""
        text_edit = TabReplaceTextEdit(tab_replacement=" → ")

        # Test Unicode characters
        text = "你好\t世界\t测试\némojis\t🚀\t🎉\nunicode\ttext\there"
        sanitized = text_edit.sanitize_text(text)
        expected = "你好 → 世界 → 测试\némojis → 🚀 → 🎉\nunicode → text → here"
        assert sanitized == expected

    def test_tab_replace_textedit_sanitize_text_empty_string(
        self, qt_widget_cleanup
    ) -> None:
        """Test sanitize_text with empty string."""
        text_edit = TabReplaceTextEdit()

        # Test empty string
        sanitized = text_edit.sanitize_text("")
        assert sanitized == ""

        # Test string with only tabs
        sanitized = text_edit.sanitize_text("\t\t\t")
        # Tabs become newlines by default, then empty lines are removed
        assert sanitized == ""

    def test_tab_replace_textedit_sanitize_text_only_tabs(
        self, qt_widget_cleanup
    ) -> None:
        """Test sanitize_text with only tabs."""
        text_edit = TabReplaceTextEdit(tab_replacement="SPACE")

        # Test only tabs
        text = "\t\t\t"
        sanitized = text_edit.sanitize_text(text)
        # Tabs become "SPACE", then empty lines are removed
        assert sanitized == "SPACESPACESPACE"

    def test_tab_replace_textedit_sanitize_text_multiple_tabs(
        self, qt_widget_cleanup
    ) -> None:
        """Test sanitize_text with multiple consecutive tabs."""
        text_edit = TabReplaceTextEdit(tab_replacement="|")

        # Test multiple tabs
        text = "col1\t\t\tcol2"
        sanitized = text_edit.sanitize_text(text)
        assert sanitized == "col1|||col2"

    def test_tab_replace_textedit_sanitize_text_edge_cases(
        self, qt_widget_cleanup
    ) -> None:
        """Test sanitize_text with edge cases."""
        text_edit = TabReplaceTextEdit(tab_replacement="TAB")

        # Test tab at the beginning
        text = "\tcol1\tcol2"
        sanitized = text_edit.sanitize_text(text)
        # Tabs become "TAB"
        assert sanitized == "TABcol1TABcol2"

        # Test tab at the end
        text = "col1\tcol2\t"
        sanitized = text_edit.sanitize_text(text)
        assert sanitized == "col1TABcol2TAB"

        # Test tabs at the beginning and end
        text = "\tcol1\tcol2\t"
        sanitized = text_edit.sanitize_text(text)
        assert sanitized == "TABcol1TABcol2TAB"

    def test_tab_replace_textedit_text_handling(self, qt_widget_cleanup) -> None:
        """Test text handling."""
        text_edit = TabReplaceTextEdit()

        # Test setPlainText
        text_edit.setPlainText("test text")
        assert text_edit.toPlainText() == "test text"

        # Test clear
        text_edit.clear()
        assert text_edit.toPlainText() == ""

        # Test insertPlainText
        text_edit.insertPlainText("inserted text")
        assert text_edit.toPlainText() == "inserted text"

    def test_tab_replace_textedit_property_type(self, qt_widget_cleanup) -> None:
        """Test type property for QSS."""
        text_edit = TabReplaceTextEdit()

        # Verify that the type property is defined
        assert text_edit.property("type") == "TabReplaceTextEdit"

    def test_tab_replace_textedit_refresh_style(self, qt_widget_cleanup) -> None:
        """Test refresh_style method."""
        text_edit = TabReplaceTextEdit()

        # Method should not raise an exception
        try:
            text_edit.refresh_style()
        except Exception as e:
            pytest.fail(f"refresh_style() raised an exception: {e}")

    def test_tab_replace_textedit_multiple_instances(self, qt_widget_cleanup) -> None:
        """Test with multiple instances."""
        text_edit1 = TabReplaceTextEdit(tab_replacement="|")
        text_edit2 = TabReplaceTextEdit(tab_replacement="->")

        # Test instance independence
        text = "col1\tcol2\tcol3"
        sanitized1 = text_edit1.sanitize_text(text)
        sanitized2 = text_edit2.sanitize_text(text)

        assert sanitized1 == "col1|col2|col3"
        assert sanitized2 == "col1->col2->col3"

    def test_tab_replace_textedit_dynamic_property_changes(
        self, qt_widget_cleanup
    ) -> None:
        """Test dynamic property changes."""
        text_edit = TabReplaceTextEdit()
        text = "col1\tcol2\tcol3"

        # Test dynamic tab_replacement change
        text_edit.tab_replacement = "|"
        sanitized1 = text_edit.sanitize_text(text)
        assert sanitized1 == "col1|col2|col3"

        text_edit.tab_replacement = "->"
        sanitized2 = text_edit.sanitize_text(text)
        assert sanitized2 == "col1->col2->col3"

        # Test dynamic remove_empty_lines change
        text_with_empty = "line1\n\nline2\n\t\nline3"

        text_edit.remove_empty_lines = True
        sanitized3 = text_edit.sanitize_text(text_with_empty)
        assert sanitized3 == "line1\nline2\n->\nline3"

        text_edit.remove_empty_lines = False
        sanitized4 = text_edit.sanitize_text(text_with_empty)
        assert sanitized4 == "line1\n\nline2\n->\nline3"

    def test_tab_replace_textedit_large_text(self, qt_widget_cleanup) -> None:
        """Test with large text."""
        text_edit = TabReplaceTextEdit(tab_replacement="|")

        # Create large text
        lines = []
        for i in range(1000):
            lines.append(f"col1_{i}\tcol2_{i}\tcol3_{i}")
        large_text = "\n".join(lines)

        # Sanitize large text
        sanitized = text_edit.sanitize_text(large_text)

        # Verify result
        lines_sanitized = sanitized.split("\n")
        assert len(lines_sanitized) == 1000

        # Verify a specific line
        assert "col1_0|col2_0|col3_0" in lines_sanitized[0]
        assert "col1_999|col2_999|col3_999" in lines_sanitized[999]

    def test_tab_replace_textedit_special_replacement_strings(
        self, qt_widget_cleanup
    ) -> None:
        """Test with special replacement strings."""
        text_edit = TabReplaceTextEdit()
        text = "col1\tcol2\tcol3"

        # Test empty string
        text_edit.tab_replacement = ""
        sanitized = text_edit.sanitize_text(text)
        # Empty string = no separation
        assert sanitized == "col1col2col3"

        # Test string with spaces
        text_edit.tab_replacement = "   "
        sanitized = text_edit.sanitize_text(text)
        assert sanitized == "col1   col2   col3"

        # Test string with special characters
        text_edit.tab_replacement = "\n\t"
        sanitized = text_edit.sanitize_text(text)
        assert sanitized == "col1\n\tcol2\n\tcol3"
