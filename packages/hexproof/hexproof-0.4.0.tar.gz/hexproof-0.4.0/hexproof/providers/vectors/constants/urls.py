"""
* Constants: URLs
"""
# Third party imports
from yarl import URL

# Main URLs
SITE = URL('https://github.com')
API = URL('https://api.github.com')

# Releases
LATEST_RELEASE = API / 'repos/Investigamer/mtg-vectors/releases/latest'
DOWNLOAD_RELEASE = SITE / 'Investigamer/mtg-vectors/releases/download'
