"""
* Scryfall Schema: List
* https://scryfall.com/docs/api/errors
"""
# Standard Library Imports
from typing import Literal, Optional

# Local Imports
from hexproof.providers.scryfall.schema._core import ScryfallSchema


class ListObject(ScryfallSchema):
    """An object representing a sequence of Scryfall objects which may be paginated or contain warnings
        raised when generating the list."""
    object: Literal['list'] = 'list'
    data: list[dict | ScryfallSchema]
    has_more: bool
    next_page: Optional[str] = None
    warnings: Optional[list[str]] = None
