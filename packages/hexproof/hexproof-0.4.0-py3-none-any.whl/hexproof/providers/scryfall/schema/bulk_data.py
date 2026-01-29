"""
* Scryfall Schema: Bulk Data
* https://scryfall.com/docs/api/bulk-data
"""
# Standard Library Imports
import datetime
from typing import Literal

# Local Imports
from hexproof.providers.scryfall.schema._core import ScryfallSchema
from hexproof.providers.scryfall.schema.list_object import ListObject


class BulkData(ScryfallSchema):
    """An object representing a bulk dataset provided by Scryfall as a JSON file."""
    object: Literal['bulk-data'] = 'bulk-data'
    id: str
    uri: str
    type: str
    name: str
    description: str
    download_uri: str
    updated_at: str | datetime.datetime
    size: int
    content_type: str
    content_encoding: str


class BulkDataList(ListObject):
    """Represents a sequence of BulkData objects.

    Notes:
        Subset of the 'List' Scryfall object.
        See docs: https://scryfall.com/docs/api/lists
    """
    data: list[BulkData]
