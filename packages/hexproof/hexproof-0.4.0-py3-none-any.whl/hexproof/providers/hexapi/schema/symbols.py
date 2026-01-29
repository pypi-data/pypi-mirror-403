"""
* Symbol Model Schemas
"""
# Third Party Imports
from omnitils.schema import Schema

"""
* Schemas
"""


class WatermarkSymbolURI(Schema):
    """Endpoint URI's for all 'SymbolCollectionWatermark' objects.
        Watermarks divided into 'watermarks' and 'watermarks_set'."""
    watermarks: dict[str, str]
    watermarks_set: dict[str, str]
