"""
* MTGJSON Schema: Related Cards
* https://mtgjson.com/data-models/related-cards/
"""
# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema


class RelatedCards(MTGJsonSchema):
    """Model describing the properties of a card that has relations to other cards."""
    reverseRelated: list[str] | None = None
    spellbook: list[str] | None = None
