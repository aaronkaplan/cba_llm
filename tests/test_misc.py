"""Unit tests for the misc module."""

from app.misc import convert_html_to_text, contains_html


def test_convert_html_to_text():
    """Test the convert_html_to_text function."""
    html_str = "<p>This is a test</p>"
    result = convert_html_to_text(html_str)
    assert result == "This is a test"

def test_contains_html():
    """Test the contains_html function."""
    text = "This is a test"
    result = contains_html(text)
    assert not result
    text = "<p>This is a test</p>"
    result = contains_html(text)
    assert result 