"""
* MTGJSON Schema: Foreign Data
* https://mtgjson.com/data-models/foreign-data/
"""
# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema
from hexproof.providers.mtgjson.schema.identifiers import Identifiers
from pydantic import Field


class ForeignData(MTGJsonSchema):
    """Model describing the properties for a card in alternate languages."""
    faceName: str | None = None
    flavorText: str | None = None
    identifiers: Identifiers = Field(default_factory=list)
    language: str
    multiverseId: int | None = None
    name: str
    text: str | None = None
    type: str | None = None
    # Todo: Docs mismatch, seems optional
    uuid: str | None = None
