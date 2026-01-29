"""
* Constants: URLs
"""
# Third party imports
from yarl import URL

# Main URLs
SITE = URL('https://scryfall.com')
API = URL('https://api.scryfall.com')

# API Endpoints: Bulk Data
API_BULK = API / 'bulk-data'

# API Endpoints: Cards
API_CARDS = API / 'cards'
API_CARDS_NAMED = API_CARDS / 'named'
API_CARDS_SEARCH = API_CARDS / 'search'

# API Endpoints: Catalogs
API_CATS = API / 'catalog'
API_CATS_CARD_NAMES = API_CATS / 'card-names'
API_CATS_ARTIST_NAMES = API_CATS / 'artist-names'
API_CATS_WORD_BANK = API_CATS / 'word-bank'
API_CATS_CREATURE_TYPES = API_CATS / 'creature-types'
API_CATS_PLANESWALKER_TYPES = API_CATS / 'planeswalker-types'
API_CATS_LAND_TYPES = API_CATS / 'land-types'
API_CATS_ARTIFACT_TYPES = API_CATS / 'artifact-types'
API_CATS_ENCHANTMENT_TYPES = API_CATS / 'enchantment-types'
API_CATS_SPELL_TYPES = API_CATS / 'spell-types'
API_CATS_POWERS = API_CATS / 'powers'
API_CATS_TOUGHNESSES = API_CATS / 'toughnesses'
API_CATS_LOYALTIES = API_CATS / 'loyalties'
API_CATS_WATERMARKS = API_CATS / 'watermarks'
API_CATS_KEYWORD_ABILITIES = API_CATS / 'keyword-abilities'
API_CATS_KEYWORD_ACTIONS = API_CATS / 'keyword-actions'
API_CATS_ABILITY_WORDS = API_CATS / 'ability-words'
API_CATS_SUPERTYPES = API_CATS / 'supertypes'

# API Endpoints: Sets
API_SETS = API / 'sets'
API_SETS_TCGPLAYER = API_SETS / 'tcgplayer'

# Site Endpoints: Sets
SITE_SETS = SITE / 'sets'
