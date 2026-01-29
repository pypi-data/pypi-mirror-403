"""
* Scryfall Schema: Card
* https://scryfall.com/docs/api/cards
"""
# Standard Library Imports
import datetime
from typing import Literal, Optional

# Local Imports
from hexproof.providers.scryfall.enums import (
    ManaColor,
    BorderColor,
    CardFinishes,
    CardLegality,
    CardFrame,
    CardRarity,
    CardGame,
    CardImageStatus,
    CardLayout,
    CardFrameEffects,
    CardSecurityStamp)
from hexproof.providers.scryfall.schema._core import ScryfallSchema
from hexproof.providers.scryfall.schema.list_object import ListObject

"""
* Schemas
"""


class CardImageURIs(ScryfallSchema):
    """An object representing the image resources available for a Card or CardFace object."""
    png: Optional[str] = None
    border_crop: Optional[str] = None
    art_crop: Optional[str] = None
    large: Optional[str] = None
    normal: Optional[str] = None
    small: Optional[str] = None


class CardFace(ScryfallSchema):
    """An object representing one face of a Card object."""
    artist: Optional[str] = None
    artist_id: Optional[str] = None
    cmc: Optional[float] = None
    color_indicator: Optional[list[ManaColor]] = None
    colors: Optional[list[ManaColor]] = None
    defense: Optional[str] = None
    flavor_text: Optional[str] = None
    illustration_id: Optional[str] = None
    image_uris: Optional[CardImageURIs] = None
    layout: Optional[str] = None
    loyalty: Optional[str] = None
    mana_cost: Optional[str] = None
    name: str
    object: Literal['card_face'] = 'card_face'
    oracle_id: Optional[str] = None
    oracle_text: Optional[str] = None
    power: Optional[str] = None
    printed_name: Optional[str] = None
    printed_text: Optional[str] = None
    printed_type_line: Optional[str] = None
    toughness: Optional[str] = None
    type_line: Optional[str] = None
    watermark: Optional[str] = None


class CardIdentifiers(ScryfallSchema):
    """An object with one or more identifier keys used for generating a card collection via the Scryfall API.

    Notes:
        See docs: https://scryfall.com/docs/api/cards/collection#card-identifiers
    """
    collector_number: Optional[str] = None
    id: Optional[str] = None
    illustration_id: Optional[str] = None
    mtgo_id: Optional[int] = None
    multiverse_id: Optional[int] = None
    name: Optional[str] = None
    oracle_id: Optional[str] = None
    set: Optional[str] = None


class CardLegalities(ScryfallSchema):
    """An object denoting a card's legal, banned, or restricted status for various formats."""
    standard: CardLegality
    future: CardLegality
    historic: CardLegality
    timeless: CardLegality
    gladiator: CardLegality
    pioneer: CardLegality
    modern: CardLegality
    legacy: CardLegality
    pauper: CardLegality
    vintage: CardLegality
    penny: CardLegality
    commander: CardLegality
    oathbreaker: CardLegality
    standardbrawl: CardLegality
    brawl: CardLegality
    alchemy: CardLegality
    paupercommander: CardLegality
    duel: CardLegality
    oldschool: CardLegality
    premodern: CardLegality
    predh: CardLegality


class CardPreview(ScryfallSchema):
    """An object containing card preview information."""
    previewed_at: Optional[str | datetime.date] = None
    source_uri: Optional[str] = None
    source: Optional[str] = None


class CardPrices(ScryfallSchema):
    """An object containing daily price information for a card."""
    usd: Optional[str] = None
    usd_foil: Optional[str] = None
    usd_etched: Optional[str] = None
    eur: Optional[str] = None
    eur_foil: Optional[str] = None
    eur_etched: Optional[str] = None
    tix: Optional[str] = None


class CardRelated(ScryfallSchema):
    """Represents a symbolic card related to another card.

    Notes:
        See docs: https://scryfall.com/docs/api/cards#related-card-objects
    """
    object: Literal['related_card'] = 'related_card'
    id: str
    component: str
    name: str
    type_line: str
    uri: str


class Card(ScryfallSchema):
    """Represents a card object on Scryfall.

    Notes:
        See docs: https://scryfall.com/docs/api/cards
    """
    object: Literal['card'] = 'card'

    """Core Fields (REQUIRED): Core properties that must be defined."""
    id: str
    lang: str
    layout: CardLayout
    uri: str
    prints_search_uri: str
    rulings_uri: str
    scryfall_uri: str

    """Core Fields (OPTIONAL): Core properties that might not be defined."""
    arena_id: Optional[int] = None
    mtgo_id: Optional[int] = None
    mtgo_foil_id: Optional[int] = None
    multiverse_ids: Optional[list[int]] = None
    tcgplayer_id: Optional[int] = None
    tcgplayer_etched_id: Optional[int] = None
    cardmarket_id: Optional[int] = None
    oracle_id: Optional[str] = None

    """Gameplay Fields (REQUIRED): Properties relevant to the game rules that must be defined."""
    cmc: float
    color_identity: list[ManaColor]
    keywords: list[str]
    legalities: CardLegalities
    name: str
    reserved: bool
    type_line: str

    """Gameplay Fields (OPTIONAL): Properties relevant to the game rules that might not be defined."""
    all_parts: Optional[list[CardRelated]] = None
    card_faces: Optional[list[CardFace]] = None
    color_indicator: Optional[list[ManaColor]] = None
    colors: Optional[list[ManaColor]] = None
    defense: Optional[str] = None
    edhrec_rank: Optional[int] = None
    hand_modifier: Optional[str] = None
    life_modifier: Optional[str] = None
    loyalty: Optional[str] = None
    mana_cost: Optional[str] = None
    oracle_text: Optional[str] = None
    penny_rank: Optional[int] = None
    power: Optional[str] = None
    produced_mana: Optional[list[ManaColor]] = None
    toughness: Optional[str] = None

    """Print Fields (REQUIRED): Properties unique to a specific card printing that must be defined."""
    booster: bool
    border_color: BorderColor
    card_back_id: Optional[str] = None
    collector_number: str
    digital: bool
    finishes: list[CardFinishes]
    frame: CardFrame
    full_art: bool
    games: list[CardGame]
    highres_image: bool
    image_status: CardImageStatus
    oversized: bool
    prices: CardPrices
    promo: bool
    rarity: CardRarity
    # No codified list of related URI keys
    related_uris: dict[str, str]
    released_at: str | datetime.date
    reprint: bool
    scryfall_set_uri: str
    set_name: str
    set_search_uri: str
    set_type: str
    set_uri: str
    set: str
    set_id: str
    story_spotlight: bool
    textless: bool
    variation: bool

    """Print Fields (OPTIONAL): Properties unique to a specific card printing that might not be defined."""
    artist: Optional[str] = None
    artist_ids: Optional[list[str]] = None
    attraction_lights: Optional[list[int]] = None
    # Could be null, default to False for booleans?
    content_warning: bool = False
    flavor_name: Optional[str] = None
    flavor_text: Optional[str] = None
    frame_effects: Optional[list[CardFrameEffects]] = None
    illustration_id: Optional[str] = None
    image_uris: Optional[CardImageURIs] = None
    printed_name: Optional[str] = None
    printed_text: Optional[str] = None
    printed_type_line: Optional[str] = None
    # No codified list of possible promo types
    promo_types: Optional[list[str]] = None
    # No codified list of possible purchase URI keys
    purchase_uris: Optional[dict[str, str]] = None
    variation_of: Optional[str] = None
    security_stamp: Optional[CardSecurityStamp] = None
    watermark: Optional[str] = None
    preview: Optional[CardPreview] = None

    """Fields currently undocumented."""
    foil: Optional[bool] = None
    nonfoil: Optional[bool] = None
    game_changer: Optional[bool] = None


class CardList(ListObject):
    """Represents a sequence of Card objects.

    Notes:
        Subset of the 'List' Scryfall object.
        See docs: https://scryfall.com/docs/api/lists
    """
    data: list[Card]
    total_cards: Optional[int] = None
