"""
* Scryfall Schema: Ruling
* https://scryfall.com/docs/api/rulings
"""
# Standard Library Imports
import datetime
from typing import Literal

# Local Imports
from hexproof.providers.scryfall.schema._core import ScryfallSchema
from hexproof.providers.scryfall.schema.list_object import ListObject


class Ruling(ScryfallSchema):
    """Object representing rulings, release notes, or scryfall notes for a particular card."""
    object: Literal['ruling'] = 'ruling'
    oracle_id: str
    source: Literal['wotc'] | Literal['scryfall']
    published_at: str | datetime.date
    comment: str


class RulingList(ListObject):
    """Represents a sequence of Ruling objects.

    Notes:
        Subset of the 'List' Scryfall object.
        See docs: https://scryfall.com/docs/api/lists
    """
    data: list[Ruling]
