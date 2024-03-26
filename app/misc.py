"""Miscellaneous functions for the app."""

from bs4 import BeautifulSoup


def convert_html_to_text(html_str: str) -> str:
    """Converts HTML to plain text."""
    soup = BeautifulSoup(html_str, 'html.parser')
    return soup.get_text()


def contains_html(text: str) -> bool:
    """Checks if a string contains HTML.
    Args:
        text: The string to check.
        
    Returns:
        True if the string contains HTML, False otherwise.
    """
    return bool(BeautifulSoup(text, 'html.parser').find())
