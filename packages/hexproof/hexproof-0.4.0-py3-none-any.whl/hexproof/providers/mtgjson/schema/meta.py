"""
* MTGJSON Schema: Meta
* https://mtgjson.com/data-models/meta/
"""
# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema


class Meta(MTGJsonSchema):
    """Model describing the properties of the MTGJSON application meta data."""
    date: str
    version: str
