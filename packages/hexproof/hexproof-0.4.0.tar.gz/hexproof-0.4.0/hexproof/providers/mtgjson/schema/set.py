"""
* MTGJSON Schema: Set
* https://mtgjson.com/data-models/set/
"""
# Third Party Imports
from pydantic import Field

# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema
from hexproof.providers.mtgjson.schema.booster import Booster
from hexproof.providers.mtgjson.schema.card import CardSet, CardToken
from hexproof.providers.mtgjson.schema.deck_set import DeckSet
from hexproof.providers.mtgjson.schema.sealed_product import SealedProduct
from hexproof.providers.mtgjson.schema.translations import Translations


class Set(MTGJsonSchema):
    """Model describing the properties of an individual set."""
    baseSetSize: int
    block: str | None = None
    booster: Booster | None = None
    cards: list[CardSet] = []
    cardsphereSetId: int | None = None
    code: str
    codeV3: str | None = None
    decks: list[DeckSet] = []
    isForeignOnly: bool | None = None
    isFoilOnly: bool
    isNonFoilOnly: bool | None = None
    isOnlineOnly: bool
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
    sealedProduct: list[SealedProduct] = []
    tcgplayerGroupId: int | None = None
    tokens: list[CardToken] = Field(default_factory=list)
    tokenSetCode: str | None = None
    totalSetSize: int
    translations: Translations
    type: str
