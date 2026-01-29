"""
* Scryfall Schema Definitions
* https://scryfall.com/docs/api
"""
# Standard Library Imports
from typing import Union

# Local Imports
from .bulk_data import BulkData, BulkDataList
from .card import (
    Card,
    CardFace,
    CardIdentifiers,
    CardImageURIs,
    CardLegalities,
    CardList,
    CardPreview,
    CardPrices,
    CardRelated
)
from .card_symbol import CardSymbol, CardSymbolList, ManaCost
from .catalog import Catalog
from .error import Error
from .list_object import ListObject
from .migration import CardMigration, CardMigrationList
from .ruling import Ruling, RulingList
from .set import Set, SetList

"""
* Generic Types
"""

ScryfallList = Union[
    BulkDataList,
    CardList,
    CardMigrationList,
    CardSymbolList,
    ListObject,
    RulingList,
    SetList
]

ScryfallListSchema = Union[
    type[BulkDataList],
    type[CardList],
    type[CardMigrationList],
    type[CardSymbolList],
    type[ListObject],
    type[RulingList],
    type[SetList]
]
