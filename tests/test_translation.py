"""Unittests with pytest for the translation module."""

from app.translation import translate


def test_translate():
    """Test the translate function."""
    text = "Esto es una prueba"
    result = translate(text, dst_language="english")
    assert result == "This is a test"
    result = translate(text, dst_language="deutsch")
    assert result != "This is a test"
