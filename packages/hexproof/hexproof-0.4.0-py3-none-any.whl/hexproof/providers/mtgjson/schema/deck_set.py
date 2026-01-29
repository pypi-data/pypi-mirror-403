"""
* MTGJSON Schema: Deck Set
* https://mtgjson.com/data-models/deck-set/
"""
# Third Party Imports
from pydantic import Field

# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema
from hexproof.providers.mtgjson.schema.card import CardSetDeck, CardToken


class DeckSet(MTGJsonSchema):
    """Model Describing the properties of an individual Deck within a Set."""
    code: str
    commander: list[CardSetDeck] = Field(default_factory=list)
    # Todo: This field and many others are undocumented in MTGJSON API
    displayCommander: list[CardSetDeck] = Field(default_factory=list)
    mainBoard: list[CardSetDeck] = Field(default_factory=list)
    name: str
    planes: list[CardSetDeck] = Field(default_factory=list)
    releaseDate: str | None = None
    schemes: list[CardSetDeck] = Field(default_factory=list)
    sealedProductUuids: list[str] | None = None
    sideBoard: list[CardSetDeck] = Field(default_factory=list)
    sourceSetCodes: list[str] = Field(default_factory=list)
    tokens: list[CardSetDeck] = Field(default_factory=list)
    type: str
