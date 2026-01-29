"""
* MTGJSON Schema: Deck
* https://mtgjson.com/data-models/deck/
"""
# Third Party Imports
from pydantic import Field

# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema
from hexproof.providers.mtgjson.schema.card import CardDeck, CardTokenDeck


class Deck(MTGJsonSchema):
    """Model describing the properties of an individual deck."""
    code: str
    commander: list[CardDeck] = Field(default_factory=list)
    # Todo: This field and many others are undocumented in MTGJSON API
    displayCommander: list[CardDeck] = Field(default_factory=list)
    mainBoard: list[CardDeck] = Field(default_factory=list)
    name: str
    planes: list[CardDeck] = Field(default_factory=list)
    releaseDate: str | None = None
    schemes: list[CardDeck] = Field(default_factory=list)
    sealedProductUuids: list[str] | None = None
    sideBoard: list[CardDeck] = Field(default_factory=list)
    sourceSetCodes: list[str] = Field(default_factory=list)
    tokens: list[CardTokenDeck] = Field(default_factory=list)
    type: str
