"""
* MTGJSON Schema: Leadership Skills
* https://mtgjson.com/data-models/leadership-skills/
"""
# Local Imports
from hexproof.providers.mtgjson.schema._core import MTGJsonSchema


class LeadershipSkills(MTGJsonSchema):
    """Model describing the properties of formats that a card is legal to be your Commander in
        play formats that utilize Commanders."""
    brawl: bool
    commander: bool
    oathbreaker: bool
