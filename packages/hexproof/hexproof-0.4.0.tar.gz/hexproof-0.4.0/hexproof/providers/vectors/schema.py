"""
* MTG Vectors Schemas
"""
# Third Party Imports
from omnitils.schema import Schema

"""
* Enums
"""


class Meta(Schema):
    date: str
    version: str
    uri: str


class SetSymbolManifest(Schema):
    aliases: dict[str, str]
    routes: dict[str, str]
    rarities: dict[str, str]
    symbols: dict[str, list[str]]


class SetSymbolMap(Schema):
    rarities: list[str]
    children: list[str]


class WatermarkSymbolManifest(Schema):
    routes: dict[str, str]
    symbols: list[str]


class Manifest(Schema):
    meta: Meta
    set: SetSymbolManifest
    watermark: WatermarkSymbolManifest
