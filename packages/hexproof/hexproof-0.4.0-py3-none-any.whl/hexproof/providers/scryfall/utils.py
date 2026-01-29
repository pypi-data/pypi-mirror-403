"""
* Utilities for Parsing Scryfall Data
"""
# Third Party Imports
import yarl

"""
* Parsing URL resources
"""


def get_url_base(url: str) -> yarl.URL:
    """Parses a Scryfall resource URL and returns as a URL object with no query parameters."""
    return yarl.URL(url).with_query(None)


def get_icon_code(url: str) -> str:
    """Parses a Scryfall icon URL and returns the icon code.

    Args:
        url (str): Scryfall icon URL.

    Returns:
        str: Icon code.
    """
    # Remove cache ID
    url = get_url_base(url)

    # Remove filetype
    url = url.with_suffix('')

    # Return icon
    return url.name.lower()
