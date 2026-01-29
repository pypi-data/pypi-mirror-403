"""
* MTGJSON Schema: TCGPlayer SKUs
* https://mtgjson.com/data-models/tcgplayer-skus/
"""
# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema


class TcgplayerSkus(MTGJsonSchema):
    """Model describing the properties of the TCGplayer SKUs for a product."""
    condition: str
    finishes: list[str] = []
    language: str
    printing: str
    productId: str
    skuId: str
