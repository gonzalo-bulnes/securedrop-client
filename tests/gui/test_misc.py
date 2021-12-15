import unittest

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from securedrop_client.gui import SecureQLabel, SvgLabel, SvgPushButton, SvgToggleButton

app = QApplication([])

LONG_TEXT_202 = "This is a piece of text that is exaclty 202 characters long, lorem ispum dolor sic amet, lorem ipsum dolor sic amet, lorem ispum dolor sic amet, lorem ipsum dolor sic amet, lorem ipsum dolor amet stop."  # noqa: E501

LONG_TEXT_201 = "This is a piece of text that is exactly 200 characters long, lorem ispum dolor sic amet, lorem ipsum dolor sic amet, lorem ispum dolor sic amet, lorem ipsum dolor sic amet, lorem ipsum dolor sic stop."  # noqa: E501

LONG_TEXT_WITH_NEWLINES = (  # noqa: E501
    "1234567890123456789012345678901234567890123456789012345678901234567890\n" "12345678901"
)


class SecureLabelTest(unittest.TestCase):
    def test_displays_verbatim_text_by_default(self):
        label = SecureQLabel("Hello, World!")
        assert label.text() == "Hello, World!"

    def test_does_not_remove_newlines(self):
        label = SecureQLabel(LONG_TEXT_WITH_NEWLINES, wordwrap=True)
        assert label.text() == LONG_TEXT_WITH_NEWLINES

        label = SecureQLabel(LONG_TEXT_WITH_NEWLINES, wordwrap=False)
        assert label.text() == LONG_TEXT_WITH_NEWLINES

    def test_does_preserve_markup_but_does_not_render_it(self):
        markup = '<script>alert("hi!");</script>'
        label = SecureQLabel(markup)
        assert label.text() == markup
        assert label.textFormat() == Qt.PlainText

    def test_displays_elision_when_verbatim_exceeds_max_length(self):
        label = SecureQLabel("Hello, World!", max_length=60)
        assert label.text() == "Hello,..."

    def test_does_not_display_elision_when_verbatim_is_shorter_max_length(self):
        label = SecureQLabel("Hello, World!", max_length=600)
        assert label.text() == "Hello, World!"

    def test_does_not_report_elision_by_default(self):
        label = SecureQLabel("Hello, World!")
        assert not label.is_elided()

    def test_reports_elision_when_relevant(self):
        label = SecureQLabel("Hello, World!", max_length=6)
        assert label.is_elided()

    def test_only_allows_one_line_of_elided_text(self):
        label = SecureQLabel("Hello, World!\nHow are you?")
        assert label.text() == "Hello, World!\nHow are you?"

        label = SecureQLabel("Hello, World!\nHow are you?", max_length=60)
        assert label.text() == "Hello,..."

        label = SecureQLabel("Hello, World!\nHow are you?", max_length=600)
        assert label.text() == "Hello, World!"

    def test_does_not_escape_quotes_for_readability(self):
        label = SecureQLabel("'hello'")
        assert label.text() == "'hello'"

    def test_trims_leading_and_trailing_whitespace(self):
        label = SecureQLabel(" \n  Hello, World! \n\t \r ")
        assert label.text() == "Hello, World!"

    def test_does_not_set_any_tooltip_by_default(self):
        label = SecureQLabel("Hello, World!\nHow are you?")
        assert label.toolTip() == ""

    def test_only_sets_a_tooltip_when_elided(self):
        label = SecureQLabel("Hello, World!", with_tooltip=True, max_length=60)
        assert label.toolTip() == "Hello, World!"

        label = SecureQLabel("Hello, World!", with_tooltip=True)
        assert label.toolTip() == ""

    def test_does_not_elide_the_tooltip(self):
        label = SecureQLabel("Hello, World!\nHow are you?", with_tooltip=True, max_length=60)
        assert label.toolTip() == "Hello, World!\nHow are you?"

    def test_does_not_truncate_the_tooltip(self):
        label = SecureQLabel(LONG_TEXT_202, with_tooltip=True, max_length=60)
        assert label.toolTip() == LONG_TEXT_202

    def test_allows_multiline_tooltips(self):
        label = SecureQLabel("Hello, World!\nHow are you?", with_tooltip=True, max_length=60)
        assert label.toolTip() == "Hello, World!\nHow are you?"

    def test_refresh_preview_text_updates_elision(self):
        label = SecureQLabel("Hello, World!", max_length=32)
        assert label.text() == "He..."
        label.max_length = 60
        label.refresh_preview_text()
        assert label.text() == "Hello,..."

    def test_refresh_preview_text_truncates_text(self):
        label = SecureQLabel(LONG_TEXT_201)
        label.refresh_preview_text()
        assert label.text() == LONG_TEXT_201

        label = SecureQLabel(LONG_TEXT_202)
        label.refresh_preview_text()
        assert label.text() == LONG_TEXT_202[:-1]


class SvgLabelTest(unittest.TestCase):
    def test_displays_no_text(self):
        label = SvgLabel("error_icon.svg")
        assert label.text() == ""

    @unittest.skip("This seems like it should be the correct behavior.")
    def test_adopts_the_specified_size(self):
        label = SvgLabel(filename="error_icon.svg", svg_size=QSize(800, 600))
        assert label.size() == QSize(800, 600)

    def test_only_the_svg_adopts_the_specified_size(self):
        label = SvgLabel(filename="error_icon.svg", svg_size=QSize(800, 600))
        # The following assertion relies on an implementation detail.
        assert label.svg.size() == QSize(800, 600)

    def test_update_image_updates_the_svg_size(self):
        label = SvgLabel(filename="error_icon.svg", svg_size=QSize(800, 600))
        label.update_image(filename="error_icon.svg", svg_size=QSize(400, 300))
        assert label.svg.size() == QSize(400, 300)

    @unittest.skip("I don't know how to test this.")
    def test_update_image_replaces_the_svg(self):
        label = SvgLabel(filename="error_icon.svg", svg_size=QSize(800, 600))
        label.update_image(filename="printer.svg")
        assert False


class SvgPushButtonTest(unittest.TestCase):
    def test_sets_an_icon(self):
        button = SvgPushButton("error_icon.svg")
        assert not button.icon().isNull()

    @unittest.skip("I couldn't find out how to test this properly.")
    def test_sets_the_icon_size_to_the_specified_dimensions(self):
        button = SvgPushButton("error_icon.svg", svg_size=QSize(800, 600))
        assert button.icon().actualSize(QSize(1000, 1000)) == QSize(800, 600)


class SvgToggleButtonTest(unittest.TestCase):
    def test_sets_an_icon(self):
        button = SvgToggleButton(on="error_icon.svg", off="error_icon.svg")
        assert not button.icon().isNull()

    def test_is_checkable(self):
        button = SvgToggleButton(on="error_icon.svg", off="error_icon.svg")
        assert button.isCheckable()

    def test_can_be_toggled(self):
        button = SvgToggleButton(on="error_icon.svg", off="error_icon.svg")
        assert not button.isChecked()
        button.toggle()
        assert button.isChecked()
        button.toggle()
        assert not button.isChecked()

    @unittest.skip("I couldn't find out how to test this properly.")
    def test_sets_the_icon_size_to_the_specified_dimensions(self):
        button = SvgToggleButton(
            on="error_icon.svg", off="error_icon.svg", svg_size=QSize(800, 600)
        )
        assert button.icon().actualSize(QSize(1000, 1000)) == QSize(800, 600)

    def test_set_icon_overides_the_icon(self):
        button = SvgToggleButton(on="error_icon.svg", off="error_icon.svg")
        button.setIcon(QIcon())  # set a null icon

        button.set_icon(on="printer.svg", off="printer.svg")
        assert not button.icon().isNull()

    @unittest.skip("I couldn't find out how to test this properly.")
    def test_set_icon_sets_the_icon_size_to_the_specified_dimensions(self):
        button = SvgToggleButton(
            on="error_icon.svg", off="error_icon.svg", svg_size=QSize(800, 600)
        )
        button.set_icon(on="printer.svg", off="printer.svg", svg_size=QSize(400, 300))
        assert button.icon().actualSize(QSize(1000, 1000)) == QSize(400, 300)
