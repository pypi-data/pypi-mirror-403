"""
* MTGJSON Schema: Set List
* https://mtgjson.com/data-models/set-list/
"""
# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema
from hexproof.providers.mtgjson.schema.deck_set import DeckSet
from hexproof.providers.mtgjson.schema.sealed_product import SealedProduct
from hexproof.providers.mtgjson.schema.translations import Translations


class SetList(MTGJsonSchema):
    """Model describing the metadata properties of an individual Set."""
    baseSetSize: int
    block: str | None = None
    cardsphereSetId: int | None = None
    code: str
    codeV3: str | None = None
    decks: list[DeckSet] | None = None
    isForeignOnly: bool | None = None
    isFoilOnly: bool = False
    isNonFoilOnly: bool | None = None
    isOnlineOnly: bool = False
    isPaperOnly: bool | None = None
    isPartialPreview: bool | None = None
    keyruneCode: str
    languages: list[str] | None = None
    mcmId: int | None = None
    mcmIdExtras: int | None = None
    mcmName: str | None = None
    mtgoCode: str | None = None
    name: str
    parentCode: str | None = None
    releaseDate: str
    sealedProduct: list[SealedProduct] | None = None
    tcgplayerGroupId: int | None = None
    totalSetSize: int
    tokenSetCode: str | None = None
    translations: Translations
    type: str
