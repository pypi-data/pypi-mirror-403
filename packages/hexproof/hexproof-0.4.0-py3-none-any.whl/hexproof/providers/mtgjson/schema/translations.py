"""
* MTGJSON Schema: Translations
* https://mtgjson.com/data-models/translations/
"""
# Third Party Imports
from pydantic import Field

# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema


class Translations(MTGJsonSchema):
    """Model describing the properties of a Set or Set List's name translated in various alternate languages."""
    Ancient_Greek: str | None = Field(None, alias="Ancient Greek")
    Arabic: str | None = Field(None, alias="Arabic")
    Chinese_Simplified: str | None = Field(None, alias="Chinese Simplified")
    Chinese_Traditional: str | None = Field(None, alias="Chinese Traditional")
    French: str | None = Field(None, alias="French")
    German: str | None = Field(None, alias="German")
    Hebrew: str | None = Field(None, alias="Hebrew")
    Italian: str | None = Field(None, alias="Italian")
    Japanese: str | None = Field(None, alias="Japanese")
    Korean: str | None = Field(None, alias="Korean")
    Latin: str | None = Field(None, alias="Latin")
    Phyrexian: str | None = Field(None, alias="Phyrexian")
    Portuguese_Brazil: str | None = Field(None, alias="Portuguese (Brazil)")
    Russian: str | None = Field(None, alias="Russian")
    Sanskrit: str | None = Field(None, alias="Sanskrit")
    Spanish: str | None = Field(None, alias="Spanish")
