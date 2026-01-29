"""
* MTGJSON Schema: Card
* https://mtgjson.com/data-models/card/
"""
# Third Party Imports
from pydantic import Field

# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema
from hexproof.providers.mtgjson.schema.foreign_data import ForeignData
from hexproof.providers.mtgjson.schema.identifiers import Identifiers
from hexproof.providers.mtgjson.schema.leadership_skills import LeadershipSkills
from hexproof.providers.mtgjson.schema.legalities import Legalities
from hexproof.providers.mtgjson.schema.purchase_urls import PurchaseUrls
from hexproof.providers.mtgjson.schema.related_cards import RelatedCards
from hexproof.providers.mtgjson.schema.rulings import Rulings
from hexproof.providers.mtgjson.schema.source_products import SourceProducts

"""
* Schemas
"""


class CardAtomic(MTGJsonSchema):
    """Model describing the properties of a single "atomic" card, an oracle-like entity of a card that
        only has evergreen properties that would never change from printing to printing."""
    asciiName: str | None = None
    attractionLights: list[float] | None = None
    colorIdentity: list[str] = Field(default_factory=list)
    colorIndicator: list[str] | None = None
    colors: list[str] = Field(default_factory=list)
    # Todo: Docs mismatch, seems optional
    convertedManaCost: float | None = None
    defense: str | None = None
    edhrecRank: float | None = None
    edhrecSaltiness: float | None = None
    faceConvertedManaCost: float | None = None
    faceManaValue: float | None = None
    faceName: str | None = None
    firstPrinting: str | None = None
    foreignData: list[ForeignData] | None = None
    hand: str | None = None
    # Todo: Docs mismatch, seems optional
    hasAlternativeDeckLimit: bool | None = None
    identifiers: Identifiers
    isFunny: bool | None = None
    isGameChanger: bool | None = None
    isReserved: bool | None = None
    keywords: list[str] | None = None
    layout: str
    leadershipSkills: LeadershipSkills | None = None
    legalities: Legalities
    life: str | None = None
    loyalty: str | None = None
    manaCost: str | None = None
    # Todo: Docs mismatch, seems optional
    manaValue: float | None = None
    name: str
    power: str | None = None
    printings: list[str] | None = None
    purchaseUrls: PurchaseUrls
    # Todo: Docs mismatch, seems optional
    relatedCards: RelatedCards | None = None
    rulings: list[Rulings] | None = None
    side: str | None = None
    subsets: list[str] | None = None
    subtypes: list[str] = Field(default_factory=list)
    supertypes: list[str] = Field(default_factory=list)
    text: str | None = None
    toughness: str | None = None
    type: str
    types: list[str] = Field(default_factory=list)


class CardDeck(MTGJsonSchema):
    """Model describing the properties of a single card found in a Deck."""
    artist: str | None = None
    artistIds: list[str] | None = None
    asciiName: str | None = None
    attractionLights: list[float] | None = None
    availability: list[str] = Field(default_factory=list)
    boosterTypes: list[str] | None = None
    borderColor: str
    cardParts: list[str] | None = None
    colorIdentity: list[str] = Field(default_factory=list)
    colorIndicator: list[str] | None = None
    colors: list[str] = Field(default_factory=list)
    convertedManaCost: float
    count: float
    defense: str | None = None
    duelDeck: str | None = None
    edhrecRank: float | None = None
    edhrecSaltiness: float | None = None
    faceConvertedManaCost: float | None = None
    faceFlavorName: str | None = None
    faceManaValue: float | None = None
    faceName: str | None = None
    facePrintedName: str | None = None
    finishes: list[str] = Field(default_factory=list)
    flavorName: str | None = None
    flavorText: str | None = None
    foreignData: list[ForeignData] | None = None
    frameEffects: list[str] | None = None
    frameVersion: str
    hand: str | None = None
    hasAlternativeDeckLimit: bool | None = None
    hasContentWarning: bool | None = None
    hasFoil: bool
    hasNonFoil: bool
    identifiers: Identifiers
    isAlternative: bool | None = None
    isEtched: bool
    isFoil: bool
    isFullArt: bool | None = None
    isFunny: bool | None = None
    isGameChanger: bool | None = None
    isOnlineOnly: bool | None = None
    isOversized: bool | None = None
    isPromo: bool | None = None
    isRebalanced: bool | None = None
    isReprint: bool | None = None
    isReserved: bool | None = None
    isStarter: bool | None = None
    isStorySpotlight: bool | None = None
    isTextless: bool | None = None
    isTimeshifted: bool | None = None
    keywords: list[str] | None = None
    language: str
    layout: str
    leadershipSkills: LeadershipSkills | None = None
    legalities: Legalities
    life: str | None = None
    loyalty: str | None = None
    manaCost: str | None = None
    manaValue: float
    name: str
    number: str
    originalPrintings: list[str] | None = None
    originalReleaseDate: str | None = None
    originalText: str | None = None
    originalType: str | None = None
    otherFaceIds: list[str] | None = None
    power: str | None = None
    printedName: str | None = None
    printedText: str | None = None
    printedType: str | None = None
    printings: list[str] | None = None
    promoTypes: list[str] | None = None
    purchaseUrls: PurchaseUrls
    rarity: str
    relatedCards: RelatedCards | None = None
    rebalancedPrintings: list[str] | None = None
    rulings: list[Rulings] | None = None
    securityStamp: str | None = None
    setCode: str
    side: str | None = None
    signature: str | None = None
    sourceProducts: SourceProducts | None = None
    subsets: list[str] | None = None
    subtypes: list[str] = Field(default_factory=list)
    supertypes: list[str] = Field(default_factory=list)
    text: str | None = None
    toughness: str | None = None
    type: str
    types: list[str] = Field(default_factory=list)
    uuid: str
    variations: list[str] | None = None
    watermark: str | None = None


class CardSet(MTGJsonSchema):
    """Model describing the properties of a single card found in a Set."""
    artist: str | None = None
    artistIds: list[str] | None = None
    asciiName: str | None = None
    attractionLights: list[float] | None = None
    availability: list[str] = Field(default_factory=list)
    boosterTypes: list[str] | None = None
    borderColor: str
    cardParts: list[str] | None = None
    colorIdentity: list[str] = Field(default_factory=list)
    colorIndicator: list[str] | None = None
    colors: list[str] = Field(default_factory=list)
    convertedManaCost: float
    defense: str | None = None
    duelDeck: str | None = None
    edhrecRank: float | None = None
    edhrecSaltiness: float | None = None
    faceConvertedManaCost: float | None = None
    faceFlavorName: str | None = None
    faceManaValue: float | None = None
    faceName: str | None = None
    facePrintedName: str | None = None
    finishes: list[str] = Field(default_factory=list)
    flavorName: str | None = None
    flavorText: str | None = None
    foreignData: list[ForeignData] | None = None
    frameEffects: list[str] | None = None
    frameVersion: str
    hand: str | None = None
    hasAlternativeDeckLimit: bool | None = None
    hasContentWarning: bool | None = None
    hasFoil: bool
    hasNonFoil: bool
    identifiers: Identifiers
    isAlternative: bool | None = None
    isFullArt: bool | None = None
    isFunny: bool | None = None
    isGameChanger: bool | None = None
    isOnlineOnly: bool | None = None
    isOversized: bool | None = None
    isPromo: bool | None = None
    isRebalanced: bool | None = None
    isReprint: bool | None = None
    isReserved: bool | None = None
    isStarter: bool | None = None
    isStorySpotlight: bool | None = None
    isTextless: bool | None = None
    isTimeshifted: bool | None = None
    keywords: list[str] | None = None
    language: str
    layout: str
    leadershipSkills: LeadershipSkills | None = None
    legalities: Legalities
    life: str | None = None
    loyalty: str | None = None
    manaCost: str | None = None
    manaValue: float
    name: str
    number: str
    originalPrintings: list[str] | None = None
    originalReleaseDate: str | None = None
    originalText: str | None = None
    originalType: str | None = None
    otherFaceIds: list[str] | None = None
    power: str | None = None
    printedName: str | None = None
    printedText: str | None = None
    printedType: str | None = None
    printings: list[str] | None = None
    promoTypes: list[str] | None = None
    purchaseUrls: PurchaseUrls
    rarity: str
    relatedCards: RelatedCards | None = None
    rebalancedPrintings: list[str] | None = None
    rulings: list[Rulings] | None = None
    securityStamp: str | None = None
    setCode: str
    side: str | None = None
    signature: str | None = None
    sourceProducts: SourceProducts | None = None
    subsets: list[str] | None = None
    subtypes: list[str] = Field(default_factory=list)
    supertypes: list[str] = Field(default_factory=list)
    text: str | None = None
    toughness: str | None = None
    type: str
    types: list[str] = Field(default_factory=list)
    uuid: str
    variations: list[str] | None = None
    watermark: str | None = None


class CardSetDeck(MTGJsonSchema):
    """Model describing the properties of a single card found in a Deck (Set)."""
    count: float
    isEtched: bool | None = None
    isFoil: bool | None = None
    uuid: str


class CardToken(MTGJsonSchema):
    """Model describing the properties of a single token card found in a Set."""
    artist: str | None = None
    artistIds: list[str] | None = None
    asciiName: str | None = None
    availability: list[str] = Field(default_factory=list)
    boosterTypes: list[str] | None = None
    borderColor: str
    cardParts: list[str] | None = None
    colorIdentity: list[str] = Field(default_factory=list)
    colorIndicator: list[str] | None = None
    colors: list[str] = Field(default_factory=list)
    edhrecSaltiness: float | None = None
    faceName: str | None = None
    faceFlavorName: str | None = None
    finishes: list[str] = Field(default_factory=list)
    flavorName: str | None = None
    flavorText: str | None = None
    frameEffects: list[str] | None = None
    frameVersion: str
    hasFoil: bool
    hasNonFoil: bool
    identifiers: Identifiers
    isFullArt: bool | None = None
    isFunny: bool | None = None
    isOnlineOnly: bool | None = None
    isOversized: bool | None = None
    isPromo: bool | None = None
    isReprint: bool | None = None
    isTextless: bool | None = None
    keywords: list[str] | None = None
    language: str
    layout: str
    loyalty: str | None = None
    manaCost: str | None = None
    name: str
    number: str
    orientation: str | None = None
    originalText: str | None = None
    originalType: str | None = None
    otherFaceIds: list[str] | None = None
    power: str | None = None
    printedType: str | None = None
    promoTypes: list[str] | None = None
    relatedCards: RelatedCards | None = None
    reverseRelated: list[str] | None = None
    securityStamp: str | None = None
    setCode: str
    side: str | None = None
    signature: str | None = None
    sourceProducts: SourceProducts | None = None
    subsets: list[str] | None = None
    subtypes: list[str] = Field(default_factory=list)
    supertypes: list[str] = Field(default_factory=list)
    text: str | None = None
    toughness: str | None = None
    type: str
    types: list[str] = Field(default_factory=list)
    uuid: str
    watermark: str | None = None


class CardTokenDeck(CardToken):
    """Model describing the properties of a single token card found in a Deck.

    Todo:
        Not included in MTGJSON API, tokens in `Deck` model appear to be synthesized from
            `CardToken` and `CardDeck.`
    """
    count: int
    isEtched: bool
    isFoil: bool


"""
* Types
"""

Card = CardAtomic | CardDeck | CardSet | CardSetDeck | CardToken
"""
* A Card is a data structure with variations of Data Models that is found within files 
    that reference cards, and is not a Data Model itself.
"""
