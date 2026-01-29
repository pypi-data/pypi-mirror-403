"""
* MTGJSON Schema: Sealed Product
* https://mtgjson.com/data-models/sealed-product/
"""
# Third Party Imports
from pydantic import Field

# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema
from hexproof.providers.mtgjson.schema.identifiers import Identifiers
from hexproof.providers.mtgjson.schema.purchase_urls import PurchaseUrls


class SealedProductCard(MTGJsonSchema):
    """Model describing the 'card' product configuration in SealedProductContents."""
    foil: bool = False
    name: str
    number: str
    set: str
    # Todo: Docs mismatch, seems optional
    uuid: str | None = None


class SealedProductDeck(MTGJsonSchema):
    """Model describing the 'deck' product configuration in SealedProductContents."""
    name: str
    set: str


class SealedProductOther(MTGJsonSchema):
    """Model describing the 'obscure' product configuration in SealedProductContents."""
    name: str


class SealedProductPack(MTGJsonSchema):
    """Model describing the 'pack' product configuration in SealedProductContents."""
    code: str
    set: str


class SealedProductSealed(MTGJsonSchema):
    """Model describing the 'sealed' product configuration in SealedProductContents."""
    count: int
    name: str
    set: str
    # Todo: Docs mismatch, seems optional
    uuid: str | None = None


class SealedProductContentsVariable(MTGJsonSchema):
    """Utility definition for the 'variable' property on SealedProductContents schema."""
    configs: list['SealedProductContents'] = Field(default_factory=list)


class SealedProductContentsVariableConfig(MTGJsonSchema):
    """Utility definition for the 'variable_config' property on SealedProductContents schema.

    Todo:
        Currently not documented on MTGJSON.
    """
    chance: int
    weight: int


class SealedProductContents(MTGJsonSchema):
    """Model describing the contents properties of a purchasable product in a Set Data Model."""
    card: list[SealedProductCard] | None = None
    deck: list[SealedProductDeck] | None = None
    other: list[SealedProductOther] | None = None
    pack: list[SealedProductPack] | None = None
    sealed: list[SealedProductSealed] | None = None
    variable: list[SealedProductContentsVariable] | None = None
    variable_config: list[SealedProductContentsVariableConfig] | None = None


class SealedProduct(MTGJsonSchema):
    """Model describing the properties for the purchasable product of a Set Data Model."""
    cardCount: int | None = None
    category: str | None = None
    contents: SealedProductContents | None = None
    identifiers: Identifiers
    # Todo: Not documented
    language: str | None = None
    name: str
    productSize: int | None = None
    purchaseUrls: PurchaseUrls
    releaseDate: str | None = None
    subtype: str | None = None
    uuid: str
