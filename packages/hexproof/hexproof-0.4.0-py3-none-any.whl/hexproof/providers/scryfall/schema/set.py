"""
* Scryfall Schema: Set
* https://scryfall.com/docs/api/sets
"""
# Standard Library Imports
from typing import Literal, Optional

# Local Imports
from hexproof.providers.scryfall.enums import SetType
from hexproof.providers.scryfall.schema._core import ScryfallSchema
from hexproof.providers.scryfall.schema.list_object import ListObject

"""
* Schemas
"""


class Set(ScryfallSchema):
    """Scryfall 'Set' object representing a group of related Magic cards."""
    object: Literal['set'] = 'set'
    arena_code: Optional[str] = None
    block: Optional[str] = None
    block_code: Optional[str] = None
    card_count: int
    code: str
    digital: bool = False
    foil_only: bool = False
    icon_svg_uri: str
    id: str
    mtgo_code: Optional[str] = None
    name: str
    nonfoil_only: bool = False
    parent_set_code: Optional[str] = None
    printed_size: Optional[int] = None
    released_at: Optional[str] = None
    scryfall_uri: str
    search_uri: str
    set_type: SetType
    tcgplayer_id: Optional[int] = None
    uri: str


class SetList(ListObject):
    """Represents a sequence of Set objects.

    Notes:
        Subset of the 'List' Scryfall object.
        See docs: https://scryfall.com/docs/api/lists
    """
    data: list[Set]
