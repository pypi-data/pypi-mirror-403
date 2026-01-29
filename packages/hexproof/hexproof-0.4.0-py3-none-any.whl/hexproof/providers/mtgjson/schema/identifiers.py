"""
* MTGJSON Schema: Identifiers
* https://mtgjson.com/data-models/identifiers/
"""
# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema


class Identifiers(MTGJsonSchema):
    """Model describing the properties of identifiers associated to a card."""
    abuId: str | None = None
    cardKingdomEtchedId: str | None = None
    cardKingdomFoilId: str | None = None
    cardKingdomId: str | None = None
    cardsphereId: str | None = None
    cardsphereFoilId: str | None = None
    cardtraderId: str | None = None
    csiId: str | None = None
    deckboxId: str | None = None
    mcmId: str | None = None
    mcmMetaId: str | None = None
    miniaturemarketId: str | None = None
    mtgArenaId: str | None = None
    mtgjsonFoilVersionId: str | None = None
    mtgjsonNonFoilVersionId: str | None = None
    mtgjsonV4Id: str | None = None
    mtgoFoilId: str | None = None
    mtgoId: str | None = None
    multiverseId: str | None = None
    # Todo: Not documented
    mvpId: str | None = None
    scgId: str | None = None
    scryfallId: str | None = None
    scryfallCardBackId: str | None = None
    scryfallOracleId: str | None = None
    scryfallIllustrationId: str | None = None
    tcgplayerProductId: str | None = None
    tcgplayerEtchedProductId: str | None = None
    tntId: str | None = None
