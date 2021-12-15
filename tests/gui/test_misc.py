"""
Tests for the gui helper functions in __init__.py
"""
import unittest

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from securedrop_client.gui import SecureQLabel, SvgLabel, SvgPushButton, SvgToggleButton

app = QApplication([])


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


def test_SvgLabel_init(mocker):
    """
    Ensure SvgLabel calls the expected methods correctly to set the icon and size.
    """
    svg_size = QSize(1, 1)
    svg = mocker.MagicMock()
    load_svg_fn = mocker.patch("securedrop_client.gui.misc.load_svg", return_value=svg)
    mocker.patch("PyQt5.QtWidgets.QHBoxLayout.addWidget")

    sl = SvgLabel(filename="mock", svg_size=svg_size)

    load_svg_fn.assert_called_once_with("mock")
    sl.svg.setFixedSize.assert_called_once_with(svg_size)
    assert sl.svg == svg


def test_SvgLabel_update(mocker):
    """
    Ensure SvgLabel calls the expected methods correctly to set the icon and size.
    """
    svg = mocker.MagicMock()
    load_svg_fn = mocker.patch("securedrop_client.gui.misc.load_svg", return_value=svg)
    mocker.patch("PyQt5.QtWidgets.QHBoxLayout.addWidget")
    sl = SvgLabel(filename="mock", svg_size=QSize(1, 1))

    sl.update_image(filename="mock_two", svg_size=QSize(2, 2))

    assert sl.svg == svg
    assert load_svg_fn.call_args_list[0][0][0] == "mock"
    assert load_svg_fn.call_args_list[1][0][0] == "mock_two"
    assert sl.svg.setFixedSize.call_args_list[0][0][0] == QSize(1, 1)
    assert sl.svg.setFixedSize.call_args_list[1][0][0] == QSize(2, 2)


def test_SecureQLabel_init():
    label_text = '<script>alert("hi!");</script>'
    sl = SecureQLabel(label_text)
    assert sl.text() == label_text


def test_SecureQLabel_init_wordwrap(mocker):
    """
    Regression test to make sure we don't remove newlines.
    """
    long_string = (
        "1234567890123456789012345678901234567890123456789012345678901234567890\n" "12345678901"
    )
    sl = SecureQLabel(long_string, wordwrap=False)
    assert sl.text() == long_string


def test_SecureQLabel_init_no_wordwrap(mocker):
    long_string = (
        "1234567890123456789012345678901234567890123456789012345678901234567890\n" "12345678901"
    )
    sl = SecureQLabel(long_string, wordwrap=False)
    assert sl.text() == long_string


def test_SecureQLabel_setText(mocker):
    sl = SecureQLabel("hello")
    assert sl.text() == "hello"

    label_text = '<script>alert("hi!");</script>'
    sl.setTextFormat = mocker.MagicMock()
    sl.setText(label_text)
    assert sl.text() == label_text
    # Ensure *safe* plain text with no HTML entities.
    sl.setTextFormat.assert_called_once_with(Qt.PlainText)


def test_SecureQLabel_get_elided_text(mocker):
    # 70 character string
    long_string = "1234567890123456789012345678901234567890123456789012345678901234567890"
    sl = SecureQLabel(long_string, wordwrap=False, max_length=100)
    elided_text = sl.get_elided_text(long_string)
    assert sl.text() == elided_text
    assert "..." in elided_text


def test_SecureQLabel_get_elided_text_short_string(mocker):
    # 70 character string
    long_string = "123456789"
    sl = SecureQLabel(long_string, wordwrap=False, max_length=100)
    elided_text = sl.get_elided_text(long_string)
    assert sl.text() == elided_text
    assert elided_text == "123456789"


def test_SecureQLabel_get_elided_text_only_returns_oneline(mocker):
    # 70 character string
    string_with_newline = "this is a string\n with a newline"
    sl = SecureQLabel(string_with_newline, wordwrap=False, max_length=100)
    elided_text = sl.get_elided_text(string_with_newline)
    assert sl.text() == elided_text
    assert elided_text == "this is a string"


def test_SecureQLabel_get_elided_text_only_returns_oneline_elided(mocker):
    # 70 character string
    string_with_newline = "this is a string\n with a newline"
    sl = SecureQLabel(string_with_newline, wordwrap=False, max_length=38)
    elided_text = sl.get_elided_text(string_with_newline)
    assert sl.text() == elided_text
    assert "..." in elided_text


def test_SecureQLabel_quotes_not_escaped_for_readability():
    sl = SecureQLabel("'hello'")
    assert sl.text() == "'hello'"


def test_SecureQLabel_trims_leading_and_trailing_whitespace():
    string_with_whitespace = "\n \n this is a string with leading and trailing whitespace \n"
    sl = SecureQLabel(string_with_whitespace)
    assert sl.text() == "this is a string with leading and trailing whitespace"
