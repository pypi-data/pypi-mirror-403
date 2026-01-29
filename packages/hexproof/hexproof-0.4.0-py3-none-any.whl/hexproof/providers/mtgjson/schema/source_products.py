"""
* MTGJSON Schema: Source Products
* https://mtgjson.com/data-models/source-products/
"""
# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema
from pydantic import Field


class SourceProducts(MTGJsonSchema):
    """Model describing the uuids for the card version in a Sealed Product."""
    etched: list[str] = Field(default_factory=list)
    foil: list[str] = Field(default_factory=list)
    nonfoil: list[str] = Field(default_factory=list)
