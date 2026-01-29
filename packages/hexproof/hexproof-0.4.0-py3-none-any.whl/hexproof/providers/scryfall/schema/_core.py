"""
* Scryfall - Schemas: Base Schemas
"""
# Third Party Imports
from omnitils.schema import Schema
from pydantic import ConfigDict


class ScryfallSchema(Schema):
    """Base Schema class for Scryfall data models."""
    model_config = ConfigDict(extra='forbid')
