"""
* MTGJSON Schema: Card Types
* https://mtgjson.com/data-models/card-types/
"""
# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema
from hexproof.providers.mtgjson.schema.card_type import CardType


class CardTypes(MTGJsonSchema):
    """Model describing the properties of a Card Data Model that has possible configurations of
        associated subtypes and supertypes."""
    artifact: CardType
    battle: CardType
    conspiracy: CardType
    creature: CardType
    enchantment: CardType
    instant: CardType
    land: CardType
    phenomenon: CardType
    plane: CardType
    planeswalker: CardType
    scheme: CardType
    sorcery: CardType
    tribal: CardType
    vanguard: CardType
