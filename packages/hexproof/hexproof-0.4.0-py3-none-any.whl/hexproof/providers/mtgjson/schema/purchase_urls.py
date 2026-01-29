"""
* MTGJSON Schema: Purchase Urls
* https://mtgjson.com/data-models/purchase-urls/
"""
# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema


class PurchaseUrls(MTGJsonSchema):
    """Model describing the properties of links to purchase a product from a marketplace."""
    cardKingdom: str | None = None
    cardKingdomEtched: str | None = None
    cardKingdomFoil: str | None = None
    cardmarket: str | None = None
    tcgplayer: str | None = None
    tcgplayerEtched: str | None = None
