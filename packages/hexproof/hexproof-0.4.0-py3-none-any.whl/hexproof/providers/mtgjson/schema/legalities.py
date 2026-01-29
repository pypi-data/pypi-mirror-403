"""
* MTGJSON Schema: Legalities
* https://mtgjson.com/data-models/legalities/
"""
# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema


class Legalities(MTGJsonSchema):
    """Model describing the properties of legalities of a card in various game play formats."""
    alchemy: str | None = None
    brawl: str | None = None
    commander: str | None = None
    duel: str | None = None
    explorer: str | None = None
    future: str | None = None
    gladiator: str | None = None
    historic: str | None = None
    historicbrawl: str | None = None
    legacy: str | None = None
    modern: str | None = None
    oathbreaker: str | None = None
    oldschool: str | None = None
    pauper: str | None = None
    paupercommander: str | None = None
    penny: str | None = None
    pioneer: str | None = None
    predh: str | None = None
    premodern: str | None = None
    standard: str | None = None
    standardbrawl: str | None = None
    timeless: str | None = None
    vintage: str | None = None
