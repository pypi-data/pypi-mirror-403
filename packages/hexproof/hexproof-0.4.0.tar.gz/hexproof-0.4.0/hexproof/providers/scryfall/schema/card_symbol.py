"""
* Scryfall Schema: Card Symbol
* https://scryfall.com/docs/api/card-symbols
"""
# Standard Library Imports
from typing import Literal, Optional

# Local Imports
from hexproof.providers.scryfall import ManaColor
from hexproof.providers.scryfall.schema._core import ScryfallSchema
from hexproof.providers.scryfall.schema.list_object import ListObject


class CardSymbol(ScryfallSchema):
    """An object representing an illustrated symbol that may appear in a card's mana cost
        or oracle text.
    """
    object: Literal['card_symbol'] = 'card_symbol'
    symbol: str
    loose_variant: Optional[str] = None
    english: str
    transposable: bool
    represents_mana: bool
    mana_value: Optional[float] = None
    appears_in_mana_costs: bool
    funny: bool
    colors: list[ManaColor]
    hybrid: bool
    phyrexian: bool
    gatherer_alternates: Optional[str] = None
    svg_uri: Optional[str] = None


class CardSymbolList(ListObject):
    """Represents a sequence of CardSymbol objects.

    Notes:
        Subset of the 'List' Scryfall object.
        See docs: https://scryfall.com/docs/api/lists
    """
    data: list[CardSymbol]


class ManaCost(ScryfallSchema):
    """An object representing a parsed mana cost string returned from
        Scryfall's `symbology/parse-mana` endpoint.

    Notes:
        See docs: https://scryfall.com/docs/api/card-symbols/parse-mana
    """
    object: Literal['mana_cost'] = 'mana_cost'
    cost: str
    cmc: float
    colors: list[ManaColor]
    colorless: bool
    monocolored: bool
    multicolored: bool
