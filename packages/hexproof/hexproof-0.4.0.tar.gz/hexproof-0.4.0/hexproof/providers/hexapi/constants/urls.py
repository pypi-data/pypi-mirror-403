"""
* Constants: URLs
"""
# Third party imports
from yarl import URL

# Main URLs
SITE = URL('https://hexproof.io')
API = URL('https://api.hexproof.io')
CDN = URL('https://cdn.hexproof.io')

# Endpoints
API_DOCS = API / 'docs'
API_KEYS = API / 'keys'
API_META = API / 'meta'
API_SETS = API / 'sets'
API_SYMBOLS = API / 'symbols'
API_SYMBOLS_SET = API_SYMBOLS / 'set'
API_SYMBOLS_WATERMARK = API_SYMBOLS / 'watermark'
