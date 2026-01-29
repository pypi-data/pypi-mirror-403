"""
* Set Model Schemas
"""
# Standard Library Imports
from typing import Optional

# Third Party Imports
from omnitils.schema import Schema

"""
* Schemas
"""


class SetFlags(Schema):
    """Boolean flags for the Set object."""
    is_digital_only: bool
    is_foil_only: bool
    is_foreign_only: bool
    is_nonfoil_only: bool
    is_paper_only: bool
    is_preview: bool


class SetURIScryfall(Schema):
    """Scryfall URI's for Set object."""
    icon: Optional[str] = None
    object: Optional[str] = None
    page: Optional[str] = None
    parent: Optional[str] = None
    search: Optional[str] = None


class Set(Schema):
    """Entire Set object as an API return schema."""
    block: Optional[str]
    block_code: Optional[str]
    code: str
    code_alt: Optional[str]
    code_arena: Optional[str]
    code_keyrune: Optional[str]
    code_mtgo: Optional[str]
    code_parent: Optional[str]
    code_symbol: str
    count_cards: int
    count_printed: Optional[int]
    count_tokens: int
    date_released: str
    flags: SetFlags
    id: str
    id_cardmarket: Optional[int]
    id_cardmarket_extras: Optional[int]
    id_cardsphere: Optional[int]
    id_tcgplayer: Optional[int]
    name: str
    name_cardmarket: Optional[str]
    type: str
    uris_scryfall: SetURIScryfall
    uris_symbol: dict[str, str]
