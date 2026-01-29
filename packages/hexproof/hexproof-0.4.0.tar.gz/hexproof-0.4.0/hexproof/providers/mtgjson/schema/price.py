"""
* MTGJSON Schema: Price
* https://mtgjson.com/data-models/price/
"""
# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema

"""
* Schemas
"""


class PricePoints(MTGJsonSchema):
    """Model describing the properties of a card's price provider prices."""
    etched: dict[str, float] | None = None
    foil: dict[str, float] | None = None
    normal: dict[str, float] | None = None


class PriceList(MTGJsonSchema):
    """Model describing the properties of a card providers list of buying and selling ability."""
    buylist: PricePoints | None = None
    currency: str
    retail: PricePoints | None = None


class PriceListForProvider(MTGJsonSchema):
    """Utility schema for use with the PriceFormats model outlining the possible providers of a PriceList object."""
    cardhoarder: PriceList | None = None
    cardkingdom: PriceList | None = None
    cardmarket: PriceList | None = None
    cardsphere: PriceList | None = None
    manapool: PriceList | None = None
    tcgplayer: PriceList | None = None


class PriceFormats(MTGJsonSchema):
    """Model describing the properties of all product formats that the price providers provide."""
    mtgo: PriceListForProvider | None = None
    paper: PriceListForProvider | None = None


"""
* Types
"""

Price = dict[str, PriceFormats]
"""
* A Price is a data structure containing property values of prices for a card, organized by
its uuid, and is not a Data Model itself.
"""