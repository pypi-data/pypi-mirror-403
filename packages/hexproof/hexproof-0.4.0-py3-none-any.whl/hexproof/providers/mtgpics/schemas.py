"""
* MTGPics Schemas
"""
# Standard Library Imports
import datetime

# Third Party Imports
from omnitils.schema import ArbitrarySchema
import yarl

"""
* Scraped Data Object Schemas
"""


class Art(ArbitrarySchema):
    """Represents an MTG 'Art' scraped from MTGPics."""
    artist: str | None = None
    date: datetime.datetime
    url: yarl.URL
    height: int
    width: int
    size: int


class Card(ArbitrarySchema):
    """Represents an MTG 'Card' scraped from MTGPics."""

    # Schema Fields
    number: str
    name: str
    ref: str
    type: str
    url: yarl.URL
    url_img: yarl.URL
    arts: list[Art]

    # Maybe list of artists, or maybe use faces instead
    artist: str | None = None

    # The yellow subtitle or tag name below some cards
    subset: str | None = None

    # May not be relevant enough to include?
    pt: str | None = None


class Set(ArbitrarySchema):
    """Represents an MTG 'Set' scraped from MTGPics."""
    id: str
    code: str
    card_count: int
    date: datetime.datetime
    date_raw: str | None = None
    name: str
    normalized: str
    url_logo: yarl.URL

    # Todo: Should we approach this a different way? Maybe defined set types?
    is_collection: bool = False
