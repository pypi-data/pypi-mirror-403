"""
* Constants: URLs
"""
# Third party imports
from yarl import URL

# Main URLs
SITE = URL('https://mtgjson.com')
API = API_SETS = SITE / 'api' / 'v5'

# Root directories
API_CSV = API / 'csv'
API_DECKS = API / 'decks'
API_PARQUET = API / 'parquet'

###
# * Directory of Data files
###

# File Archive: All Decks
API_ALL_DECK_FILES = API / 'AllDeckFiles'
API_ALL_DECK_FILES_GZ = API_ALL_DECK_FILES.with_suffix('.tar.gz')
API_ALL_DECK_FILES_XZ = API_ALL_DECK_FILES.with_suffix('.tar.xz')
API_ALL_DECK_FILES_BZ2 = API_ALL_DECK_FILES.with_suffix('.tar.bz2')
API_ALL_DECK_FILES_ZIP = API_ALL_DECK_FILES.with_suffix('.zip')

# File Archive: All Printings CSV
API_ALL_PRINTINGS_CSV_FILES = API / 'AllPrintingsCSVFiles'
API_ALL_PRINTINGS_CSV_FILES_GZ = API_ALL_PRINTINGS_CSV_FILES.with_suffix('.tar.gz')
API_ALL_PRINTINGS_CSV_FILES_XZ = API_ALL_PRINTINGS_CSV_FILES.with_suffix('.tar.xz')
API_ALL_PRINTINGS_CSV_FILES_BZ2 = API_ALL_PRINTINGS_CSV_FILES.with_suffix('.tar.bz2')
API_ALL_PRINTINGS_CSV_FILES_ZIP = API_ALL_PRINTINGS_CSV_FILES.with_suffix('.zip')

# File Archive: All Printings Parquet
API_ALL_PRINTINGS_PARQUET_FILES = API / 'AllPrintingsParquetFiles'
API_ALL_PRINTINGS_PARQUET_FILES_GZ = API_ALL_PRINTINGS_PARQUET_FILES.with_suffix('.tar.gz')
API_ALL_PRINTINGS_PARQUET_FILES_XZ = API_ALL_PRINTINGS_PARQUET_FILES.with_suffix('.tar.xz')
API_ALL_PRINTINGS_PARQUET_FILES_BZ2 = API_ALL_PRINTINGS_PARQUET_FILES.with_suffix('.tar.bz2')
API_ALL_PRINTINGS_PARQUET_FILES_ZIP = API_ALL_PRINTINGS_PARQUET_FILES.with_suffix('.zip')

# File Archive: All Sets
API_ALL_SET_FILES = API / 'AllSetFiles'
API_ALL_SET_FILES_GZ = API_ALL_SET_FILES.with_suffix('.tar.gz')
API_ALL_SET_FILES_XZ = API_ALL_SET_FILES.with_suffix('.tar.xz')
API_ALL_SET_FILES_BZ2 = API_ALL_SET_FILES.with_suffix('.tar.bz2')
API_ALL_SET_FILES_ZIP = API_ALL_SET_FILES.with_suffix('.tar.zip')

###
# * One Data File
###

# Data File: All Identifiers
API_ALL_IDENTIFIERS = API / 'AllIdentifiers.json'
API_ALL_IDENTIFIERS_GZ = API_ALL_IDENTIFIERS.with_suffix('.json.gz')
API_ALL_IDENTIFIERS_XZ = API_ALL_IDENTIFIERS.with_suffix('.json.xz')
API_ALL_IDENTIFIERS_BZ2 = API_ALL_IDENTIFIERS.with_suffix('.json.bz2')
API_ALL_IDENTIFIERS_ZIP = API_ALL_IDENTIFIERS.with_suffix('.json.zip')

# Data File: All Prices
API_ALL_PRICES = API / 'AllPrices.json'
API_ALL_PRICES_GZ = API_ALL_PRICES.with_suffix('.json.gz')
API_ALL_PRICES_XZ = API_ALL_PRICES.with_suffix('.json.xz')
API_ALL_PRICES_BZ2 = API_ALL_PRICES.with_suffix('.json.bz2')
API_ALL_PRICES_ZIP = API_ALL_PRICES.with_suffix('.json.zip')

# Data File: All Prices Today
API_ALL_PRICES_TODAY = API / 'AllPricesToday.json'
API_ALL_PRICES_TODAY_GZ = API_ALL_PRICES_TODAY.with_suffix('.json.gz')
API_ALL_PRICES_TODAY_XZ = API_ALL_PRICES_TODAY.with_suffix('.json.xz')
API_ALL_PRICES_TODAY_BZ2 = API_ALL_PRICES_TODAY.with_suffix('.json.bz2')
API_ALL_PRICES_TODAY_ZIP = API_ALL_PRICES_TODAY.with_suffix('.json.zip')

# Data File: All Prices Today (PSQL)
API_ALL_PRICES_TODAY_PSQL = API / 'AllPricesToday.psql'
API_ALL_PRICES_TODAY_PSQL_GZ = API_ALL_PRICES_TODAY_PSQL.with_suffix('.psql.gz')
API_ALL_PRICES_TODAY_PSQL_XZ = API_ALL_PRICES_TODAY_PSQL.with_suffix('.psql.xz')
API_ALL_PRICES_TODAY_PSQL_BZ2 = API_ALL_PRICES_TODAY_PSQL.with_suffix('.psql.bz2')
API_ALL_PRICES_TODAY_PSQL_ZIP = API_ALL_PRICES_TODAY_PSQL.with_suffix('.psql.zip')

# Data File: All Prices Today (SQL)
API_ALL_PRICES_TODAY_SQL = API / 'AllPricesToday.sql'
API_ALL_PRICES_TODAY_SQL_GZ = API_ALL_PRICES_TODAY_SQL.with_suffix('.sql.gz')
API_ALL_PRICES_TODAY_SQL_XZ = API_ALL_PRICES_TODAY_SQL.with_suffix('.sql.xz')
API_ALL_PRICES_TODAY_SQL_BZ2 = API_ALL_PRICES_TODAY_SQL.with_suffix('.sql.bz2')
API_ALL_PRICES_TODAY_SQL_ZIP = API_ALL_PRICES_TODAY_SQL.with_suffix('.sql.zip')

# Data File: All Prices Today (SQLite)
API_ALL_PRICES_TODAY_SQLITE = API / 'AllPricesToday.sqlite'
API_ALL_PRICES_TODAY_SQLITE_GZ = API_ALL_PRICES_TODAY_SQLITE.with_suffix('.sqlite.gz')
API_ALL_PRICES_TODAY_SQLITE_XZ = API_ALL_PRICES_TODAY_SQLITE.with_suffix('.sqlite.xz')
API_ALL_PRICES_TODAY_SQLITE_BZ2 = API_ALL_PRICES_TODAY_SQLITE.with_suffix('.sqlite.bz2')
API_ALL_PRICES_TODAY_SQLITE_ZIP = API_ALL_PRICES_TODAY_SQLITE.with_suffix('.sqlite.zip')

# Data File: All Printings
API_ALL_PRINTINGS = API / 'AllPrintings.json'
API_ALL_PRINTINGS_GZ = API_ALL_PRINTINGS.with_suffix('.json.gz')
API_ALL_PRINTINGS_XZ = API_ALL_PRINTINGS.with_suffix('.json.xz')
API_ALL_PRINTINGS_BZ2 = API_ALL_PRINTINGS.with_suffix('.json.bz2')
API_ALL_PRINTINGS_ZIP = API_ALL_PRINTINGS.with_suffix('.json.zip')

# Data File: All Printings (PSQL)
API_ALL_PRINTINGS_PSQL = API / 'AllPrintings.psql'
API_ALL_PRINTINGS_PSQL_GZ = API_ALL_PRINTINGS_PSQL.with_suffix('.psql.gz')
API_ALL_PRINTINGS_PSQL_XZ = API_ALL_PRINTINGS_PSQL.with_suffix('.psql.xz')
API_ALL_PRINTINGS_PSQL_BZ2 = API_ALL_PRINTINGS_PSQL.with_suffix('.psql.bz2')
API_ALL_PRINTINGS_PSQL_ZIP = API_ALL_PRINTINGS_PSQL.with_suffix('.psql.zip')

# Data File: All Printings (SQL)
API_ALL_PRINTINGS_SQL = API / 'AllPrintings.sql'
API_ALL_PRINTINGS_SQL_GZ = API_ALL_PRINTINGS_SQL.with_suffix('.sql.gz')
API_ALL_PRINTINGS_SQL_XZ = API_ALL_PRINTINGS_SQL.with_suffix('.sql.xz')
API_ALL_PRINTINGS_SQL_BZ2 = API_ALL_PRINTINGS_SQL.with_suffix('.sql.bz2')
API_ALL_PRINTINGS_SQL_ZIP = API_ALL_PRINTINGS_SQL.with_suffix('.sql.zip')

# Data File: All Printings (SQLite)
API_ALL_PRINTINGS_SQLITE = API / 'AllPrintings.sqlite'
API_ALL_PRINTINGS_SQLITE_GZ = API_ALL_PRINTINGS_SQLITE.with_suffix('.sqlite.gz')
API_ALL_PRINTINGS_SQLITE_XZ = API_ALL_PRINTINGS_SQLITE.with_suffix('.sqlite.xz')
API_ALL_PRINTINGS_SQLITE_BZ2 = API_ALL_PRINTINGS_SQLITE.with_suffix('.sqlite.bz2')
API_ALL_PRINTINGS_SQLITE_ZIP = API_ALL_PRINTINGS_SQLITE.with_suffix('.sqlite.zip')

# Data File: Atomic Cards
API_ATOMIC_CARDS = API / 'AtomicCards.json'
API_ATOMIC_CARDS_GZ = API_ATOMIC_CARDS.with_suffix('.json.gz')
API_ATOMIC_CARDS_XZ = API_ATOMIC_CARDS.with_suffix('.json.xz')
API_ATOMIC_CARDS_BZ2 = API_ATOMIC_CARDS.with_suffix('.json.bz2')
API_ATOMIC_CARDS_ZIP = API_ATOMIC_CARDS.with_suffix('.json.zip')

# Data File: Card Types
API_CARD_TYPES = API / 'CardTypes.json'
API_CARD_TYPES_GZ = API_CARD_TYPES.with_suffix('.json.gz')
API_CARD_TYPES_XZ = API_CARD_TYPES.with_suffix('.json.xz')
API_CARD_TYPES_BZ2 = API_CARD_TYPES.with_suffix('.json.bz2')
API_CARD_TYPES_ZIP = API_CARD_TYPES.with_suffix('.json.zip')

# Data File: All Identifiers
API_COMPILED_LIST = API / 'CompiledList.json'
API_COMPILED_LIST_GZ = API_COMPILED_LIST.with_suffix('.json.gz')
API_COMPILED_LIST_XZ = API_COMPILED_LIST.with_suffix('.json.xz')
API_COMPILED_LIST_BZ2 = API_COMPILED_LIST.with_suffix('.json.bz2')
API_COMPILED_LIST_ZIP = API_COMPILED_LIST.with_suffix('.json.zip')

# Data File: Deck List
API_DECK_LIST = API / 'DeckList.json'
API_DECK_LIST_GZ = API_DECK_LIST.with_suffix('.json.gz')
API_DECK_LIST_XZ = API_DECK_LIST.with_suffix('.json.xz')
API_DECK_LIST_BZ2 = API_DECK_LIST.with_suffix('.json.bz2')
API_DECK_LIST_ZIP = API_DECK_LIST.with_suffix('.json.zip')

# Data File: Enum Values
API_ENUM_VALUES = API / 'EnumValues.json'
API_ENUM_VALUES_GZ = API_ENUM_VALUES.with_suffix('.json.gz')
API_ENUM_VALUES_XZ = API_ENUM_VALUES.with_suffix('.json.xz')
API_ENUM_VALUES_BZ2 = API_ENUM_VALUES.with_suffix('.json.bz2')
API_ENUM_VALUES_ZIP = API_ENUM_VALUES.with_suffix('.json.zip')

# Data File: Keywords
API_KEYWORDS = API / 'Keywords.json'
API_KEYWORDS_GZ = API_KEYWORDS.with_suffix('.json.gz')
API_KEYWORDS_XZ = API_KEYWORDS.with_suffix('.json.xz')
API_KEYWORDS_BZ2 = API_KEYWORDS.with_suffix('.json.bz2')
API_KEYWORDS_ZIP = API_KEYWORDS.with_suffix('.json.zip')

# Data File: Legacy
API_LEGACY = API / 'Legacy.json'
API_LEGACY_GZ = API_LEGACY.with_suffix('.json.gz')
API_LEGACY_XZ = API_LEGACY.with_suffix('.json.xz')
API_LEGACY_BZ2 = API_LEGACY.with_suffix('.json.bz2')
API_LEGACY_ZIP = API_LEGACY.with_suffix('.json.zip')

# Data File: Legacy Atomic
API_LEGACY_ATOMIC = API / 'LegacyAtomic.json'
API_LEGACY_ATOMIC_GZ = API_LEGACY_ATOMIC.with_suffix('.json.gz')
API_LEGACY_ATOMIC_XZ = API_LEGACY_ATOMIC.with_suffix('.json.xz')
API_LEGACY_ATOMIC_BZ2 = API_LEGACY_ATOMIC.with_suffix('.json.bz2')
API_LEGACY_ATOMIC_ZIP = API_LEGACY_ATOMIC.with_suffix('.json.zip')

# Data File: Meta
API_META = API / 'Meta.json'
API_META_GZ = API_META.with_suffix('.json.gz')
API_META_XZ = API_META.with_suffix('.json.xz')
API_META_BZ2 = API_META.with_suffix('.json.bz2')
API_META_ZIP = API_META.with_suffix('.json.zip')

# Data File: Modern
API_MODERN = API / 'Modern.json'
API_MODERN_GZ = API_MODERN.with_suffix('.json.gz')
API_MODERN_XZ = API_MODERN.with_suffix('.json.xz')
API_MODERN_BZ2 = API_MODERN.with_suffix('.json.bz2')
API_MODERN_ZIP = API_MODERN.with_suffix('.json.zip')

# Data File: Modern Atomic
API_MODERN_ATOMIC = API / 'ModernAtomic.json'
API_MODERN_ATOMIC_GZ = API_MODERN_ATOMIC.with_suffix('.json.gz')
API_MODERN_ATOMIC_XZ = API_MODERN_ATOMIC.with_suffix('.json.xz')
API_MODERN_ATOMIC_BZ2 = API_MODERN_ATOMIC.with_suffix('.json.bz2')
API_MODERN_ATOMIC_ZIP = API_MODERN_ATOMIC.with_suffix('.json.zip')

# Data File: Pauper Atomic
API_PAUPER_ATOMIC = API / 'PauperAtomic.json'
API_PAUPER_ATOMIC_GZ = API_PAUPER_ATOMIC.with_suffix('.json.gz')
API_PAUPER_ATOMIC_XZ = API_PAUPER_ATOMIC.with_suffix('.json.xz')
API_PAUPER_ATOMIC_BZ2 = API_PAUPER_ATOMIC.with_suffix('.json.bz2')
API_PAUPER_ATOMIC_ZIP = API_PAUPER_ATOMIC.with_suffix('.json.zip')

# Data File: Pioneer
API_PIONEER = API / 'Pioneer.json'
API_PIONEER_GZ = API_PIONEER.with_suffix('.json.gz')
API_PIONEER_XZ = API_PIONEER.with_suffix('.json.xz')
API_PIONEER_BZ2 = API_PIONEER.with_suffix('.json.bz2')
API_PIONEER_ZIP = API_PIONEER.with_suffix('.json.zip')

# Data File: Pioneer Atomic
API_PIONEER_ATOMIC = API / 'PioneerAtomic.json'
API_PIONEER_ATOMIC_GZ = API_PIONEER_ATOMIC.with_suffix('.json.gz')
API_PIONEER_ATOMIC_XZ = API_PIONEER_ATOMIC.with_suffix('.json.xz')
API_PIONEER_ATOMIC_BZ2 = API_PIONEER_ATOMIC.with_suffix('.json.bz2')
API_PIONEER_ATOMIC_ZIP = API_PIONEER_ATOMIC.with_suffix('.json.zip')

# Data File: Set List
API_SET_LIST = API / 'SetList.json'
API_SET_LIST_GZ = API_SET_LIST.with_suffix('.json.gz')
API_SET_LIST_XZ = API_SET_LIST.with_suffix('.json.xz')
API_SET_LIST_BZ2 = API_SET_LIST.with_suffix('.json.bz2')
API_SET_LIST_ZIP = API_SET_LIST.with_suffix('.json.zip')

# Data File: Standard
API_STANDARD = API / 'Standard.json'
API_STANDARD_GZ = API_STANDARD.with_suffix('.json.gz')
API_STANDARD_XZ = API_STANDARD.with_suffix('.json.xz')
API_STANDARD_BZ2 = API_STANDARD.with_suffix('.json.bz2')
API_STANDARD_ZIP = API_STANDARD.with_suffix('.json.zip')

# Data File: Standard Atomic
API_STANDARD_ATOMIC = API / 'StandardAtomic.json'
API_STANDARD_ATOMIC_GZ = API_STANDARD_ATOMIC.with_suffix('.json.gz')
API_STANDARD_ATOMIC_XZ = API_STANDARD_ATOMIC.with_suffix('.json.xz')
API_STANDARD_ATOMIC_BZ2 = API_STANDARD_ATOMIC.with_suffix('.json.bz2')
API_STANDARD_ATOMIC_ZIP = API_STANDARD_ATOMIC.with_suffix('.json.zip')

# Data File: TCGPlayer SKUs
API_TCGPLAYER_SKUS = API / 'TcgplayerSkus.json'
API_TCGPLAYER_SKUS_GZ = API_TCGPLAYER_SKUS.with_suffix('.json.gz')
API_TCGPLAYER_SKUS_XZ = API_TCGPLAYER_SKUS.with_suffix('.json.xz')
API_TCGPLAYER_SKUS_BZ2 = API_TCGPLAYER_SKUS.with_suffix('.json.bz2')
API_TCGPLAYER_SKUS_ZIP = API_TCGPLAYER_SKUS.with_suffix('.json.zip')

# Data File: Vintage
API_VINTAGE = API / 'Vintage.json'
API_VINTAGE_GZ = API_VINTAGE.with_suffix('.json.gz')
API_VINTAGE_XZ = API_VINTAGE.with_suffix('.json.xz')
API_VINTAGE_BZ2 = API_VINTAGE.with_suffix('.json.bz2')
API_VINTAGE_ZIP = API_VINTAGE.with_suffix('.json.zip')

# Data File: Vintage Atomic
API_VINTAGE_ATOMIC = API / 'VintageAtomic.json'
API_VINTAGE_ATOMIC_GZ = API_VINTAGE_ATOMIC.with_suffix('.json.gz')
API_VINTAGE_ATOMIC_XZ = API_VINTAGE_ATOMIC.with_suffix('.json.xz')
API_VINTAGE_ATOMIC_BZ2 = API_VINTAGE_ATOMIC.with_suffix('.json.bz2')
API_VINTAGE_ATOMIC_ZIP = API_VINTAGE_ATOMIC.with_suffix('.json.zip')
