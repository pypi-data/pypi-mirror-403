"""
* Constants: URLs
"""
# Third party imports
from yarl import URL

# Main URLs
SITE = URL('https://mtgpics.com')

# Art Page
ART = SITE / 'art'

# Single Card Page
CARD = SITE / 'card'

# Illustrations / Illustrators
ILLUS = SITE / 'illus'
ILLUS_LIST = SITE / 'illus_txt'
ILLUSTRATORS = SITE / 'illustrators'

# Pics Image Urls
PICS = SITE / 'pics'
PICS_ART = PICS / 'art'
PICS_ART_THUMB = PICS / 'art_th'
PICS_BIG = PICS / 'big'
PICS_REG = PICS / 'reg'

# Set Pages
SET = SITE / 'set'
SET_CHECKLIST = SITE / 'set_checklist'

# Sets Pages
SETS = SITE / 'sets'
SETS_CHRONO = SITE / 'sets_chrono'
SETS_SOON = SITE / 'sets_soon'

# Spoiler Page
SPOILER = SITE / 'spoiler'
