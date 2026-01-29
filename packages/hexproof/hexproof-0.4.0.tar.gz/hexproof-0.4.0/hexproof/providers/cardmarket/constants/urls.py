"""
* Constants: URLs
"""
# Third party imports
from yarl import URL

# Main URLs
SITE = URL('https://cardmarket.com')
MTG = SITE / 'en' / 'Magic'

# Pages
MTG_SET = MTG / 'Expansions'
