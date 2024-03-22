"""Unittests with pytest for the translation module."""

import pytest
from app.translation import translate

def test_translate():
    """Test the translate function."""
    text = "Esto es una prueba"
    result = translate(text, dest="en")
    assert result == "This is a test"