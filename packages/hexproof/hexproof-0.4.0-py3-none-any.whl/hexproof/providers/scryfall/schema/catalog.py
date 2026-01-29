"""
* Scryfall Schema: Catalog
* https://scryfall.com/docs/api/catalogs
"""
# Standard Library Imports
from typing import Literal

# Local Imports
from hexproof.providers.scryfall.schema._core import ScryfallSchema


class Catalog(ScryfallSchema):
    """An object containing an array of Magic datapoints provided by Scryfall."""
    object: Literal['catalog'] = 'catalog'
    uri: str
    total_values: int
    data: list[str]
