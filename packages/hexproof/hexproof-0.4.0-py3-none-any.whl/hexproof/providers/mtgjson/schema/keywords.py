"""
* MTGJSON Schema: Keywords
* https://mtgjson.com/data-models/keywords/
"""
# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema


class Keywords(MTGJsonSchema):
    """Model describing the properties of keywords available to any card."""
    abilityWords: list[str] = []
    keywordAbilities: list[str] = []
    keywordActions: list[str] = []
