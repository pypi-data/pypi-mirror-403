"""
* MTGJSON Schema: Booster
* https://mtgjson.com/data-models/booster/
"""
# Third Party Imports
from pydantic import Field

# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema

"""
* Schemas
"""


class BoosterPack(MTGJsonSchema):
    """Model describing the properties of how a Set's booster data may be configured."""
    contents: dict[str, int | None]
    weight: int


class BoosterSheet(MTGJsonSchema):
    """Model describing the properties of how a sheet of printed cards can be configured."""
    allowDuplicates: bool | None = None
    balanceColors: bool | None = None
    cards: dict[str, int]
    foil: bool
    fixed: bool | None = None
    totalWeight: int


class BoosterConfig(MTGJsonSchema):
    """Model describing the properties of how a Booster Pack can be configured."""
    boosters: list[BoosterPack] = Field(default_factory=list)
    boostersTotalWeight: int
    # Todo: Not documented on MTGJSON docs
    languages: list[str] | None = None
    name: str | None = None
    sheets: dict[str, BoosterSheet] = Field(default_factory=dict)
    sourceSetCodes: list[str] = Field(default_factory=list)


"""
* Types
"""

Booster = dict[str, BoosterConfig]
"""
* A Booster is a data structure with containing property values 
of Booster configurations, and is not a Data Model itself.
"""
