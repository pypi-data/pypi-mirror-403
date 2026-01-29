"""
* MTGJSON Request Handling
"""
# Standard Library Imports
from collections.abc import Callable, Iterator
import os
from pathlib import Path

# Third Party Imports
from backoff import on_exception, expo
import ijson
from omnitils.fetch import request_header_default, download_file
from omnitils.files.archive import unpack_tar_gz
from ratelimit import sleep_and_retry
from ratelimit.decorators import RateLimitDecorator
import requests
import yarl

# Local Imports
from hexproof.providers.mtgjson import schema as MTGJsonTypes
from hexproof.providers.mtgjson.constants import urls as MTGJsonURL

# Rate limiter to safely limit MTGJSON requests
mtgjson_rate_limit = RateLimitDecorator(calls=20, period=1)
mtgjson_gql_rate_limit = RateLimitDecorator(calls=20, period=1)


"""
* Handlers
"""


def request_handler_mtgjson(func) -> Callable:
    """Wrapper for MTGJSON request functions to handle retries and rate limits.

    Notes:
        There are no known rate limits for requesting JSON file resources.
        We include a 20-per-second rate limit just to be nice.
    """
    @sleep_and_retry
    @mtgjson_rate_limit
    @on_exception(expo, requests.exceptions.RequestException, max_tries=2, max_time=1)
    def decorator(*args, **kwargs):
        return func(*args, **kwargs)
    return decorator


def request_handler_mtgjson_gql(func) -> Callable:
    """Wrapper for MTGJSON GraphQL request functions to handle retries and rate limits.

    Notes:
        MTGJSON GraphQL requests are capped at 500 per-hour per-token at the moment.
        https://mtgjson.com/mtggraphql/#rate-limits
    """
    @sleep_and_retry
    @mtgjson_gql_rate_limit
    @on_exception(expo, requests.exceptions.RequestException, max_tries=2, max_time=1)
    def decorator(*args, **kwargs):
        return func(*args, **kwargs)
    return decorator


"""
* Request Utilities
"""


@request_handler_mtgjson
def get_json(url: yarl.URL, header: dict | None = None) -> dict:
    """Retrieves JSON results from a MTGJSON API request using the proper rate limits.

    Args:
        url: MTGJSON API request URL.
        header: Optional headers to include in the response.

    Returns:
        Dict containing data from the JSON response.
    """
    if header is None:
        header = request_header_default.copy()
    with requests.get(str(url), headers=header) as r:
        r.raise_for_status()
        return r.json()


"""
* Requesting JSON Assets
"""


@request_handler_mtgjson
def get_cards_atomic_all() -> dict[str, MTGJsonTypes.CardAtomic]:
    """Get a dictionary of all MTGJSON 'CardAtomic' objects mapped to their respective card names.

    Returns:
        A dict with card name as the key, MTGJSON 'CardAtomic' object as the value.
    """
    with requests.get(
        url=MTGJsonURL.API_ATOMIC_CARDS,
        headers=request_header_default.copy()
    ) as r:
        r.raise_for_status()
        r.raw.decode_content = True
        return {k: MTGJsonTypes.CardAtomic(**v) for k, v in ijson.kvitems(r.raw, "data")}


@request_handler_mtgjson
def yield_cards_atomic_raw() -> Iterator[tuple[str, MTGJsonTypes.CardAtomic]]:
    """Get a dictionary of all MTGJSON 'CardAtomic' objects mapped to their respective card names,
        in raw dictionary format.

    Returns:
        A dict with card name as the key, a dictionary representing a MTGJSON 'CardAtomic'
            object as the value.
    """
    with requests.get(
        url=MTGJsonURL.API_ATOMIC_CARDS,
        headers=request_header_default.copy(),
        stream=True,
    ) as r:
        r.raise_for_status()
        r.raw.decode_content = True
        for k, v in ijson.kvitems(r.raw, "data"):
            yield k, v


@request_handler_mtgjson
def get_card_types() -> MTGJsonTypes.CardTypes:
    """Get the current MTGJSON 'CardTypes' resource.

    Returns:
        MTGJSON 'CardTypes' object.
    """
    with requests.get(
        url=MTGJsonURL.API_CARD_TYPES,
        headers=request_header_default.copy()
    ) as r:
        r.raise_for_status()
        _obj = r.json().get('data', {})
        return MTGJsonTypes.CardTypes(**_obj)


@request_handler_mtgjson
def get_deck(name: str) -> MTGJsonTypes.Deck:
    """Get a target MTGJSON 'Deck' resource.

    Args:
        name: Name of the deck on MTGJSON.

    Returns:
        MTGJSON 'Deck' object.
    """
    with requests.get(
        url=(MTGJsonURL.API_DECKS / name).with_suffix('.json'),
        headers=request_header_default.copy()
    ) as r:
        r.raise_for_status()
        _obj = r.json().get('data', {})
        return MTGJsonTypes.Deck(**_obj)


@request_handler_mtgjson
def get_deck_list() -> list[MTGJsonTypes.DeckList]:
    """Get the current MTGJSON 'DeckList' resource.

    Returns:
        A list of MTGJSON 'DeckList' objects.
    """
    with requests.get(
        url=MTGJsonURL.API_DECK_LIST,
        headers=request_header_default.copy(),
        stream=True,
    ) as r:
        r.raise_for_status()
        r.raw.decode_content = True
        return [MTGJsonTypes.DeckList(**n) for n in ijson.items(r.raw, "data.item")]


@request_handler_mtgjson
def yield_deck_list_raw() -> Iterator[dict]:
    """Get the current MTGJSON 'DeckList' resource, yielding each item as a raw dictionary.

    Returns:
        A list of dictionaries representing MTGJSON 'Decklist' objects.
    """
    with requests.get(
        url=MTGJsonURL.API_DECK_LIST,
        headers=request_header_default.copy(),
        stream=True,
    ) as r:
        r.raise_for_status()
        r.raw.decode_content = True
        for n in ijson.items(r.raw, "data.item"):
            yield n


@request_handler_mtgjson
def get_keywords() -> MTGJsonTypes.Keywords:
    """Get the current MTGJSON 'Keywords' resource.

    Returns:
        MTGJSON 'Keywords' object.
    """
    with requests.get(
        url=MTGJsonURL.API_KEYWORDS,
        headers=request_header_default.copy()
    ) as r:
        r.raise_for_status()
        _obj = r.json().get('data', {})
        return MTGJsonTypes.Keywords(**_obj)


@request_handler_mtgjson
def get_meta() -> MTGJsonTypes.Meta:
    """Get the current MTGJSON 'Meta' resource.

    Returns:
        MTGJSON 'Meta' object.
    """
    with requests.get(
        url=MTGJsonURL.API_META,
        headers=request_header_default.copy()
    ) as r:
        r.raise_for_status()
        _obj = r.json().get('data', {})
        return MTGJsonTypes.Meta(**_obj)


@request_handler_mtgjson
def get_prices_today_all() -> MTGJsonTypes.Price:
    """Get today's MTGJSON 'PriceFormats' objects mapped to their respective card UUID's.

    Returns:
        A dict with card UUID as the key, MTGJSON 'PriceFormats' object as the value.
    """
    with requests.get(
        url=MTGJsonURL.API_ALL_PRICES_TODAY,
        headers=request_header_default.copy()
    ) as r:
        r.raise_for_status()
        r.raw.decode_content = True
        return {k: MTGJsonTypes.PriceFormats(**v) for k, v in ijson.kvitems(r.raw, "data")}


@request_handler_mtgjson
def yield_prices_today_raw() -> Iterator[tuple[str, dict]]:
    """Get today's MTGJSON 'PriceFormats' resource for the current day and yield each item.

    Returns:
        A dict with card UUID as the key, a dictionary representing a MTGJSON 'PriceFormats'
            object as the value.
    """
    with requests.get(
        url=MTGJsonURL.API_ALL_PRICES_TODAY,
        headers=request_header_default.copy(),
        stream=True,
    ) as r:
        r.raise_for_status()
        r.raw.decode_content = True
        for k, v in ijson.kvitems(r.raw, "data"):
            yield k, v


@request_handler_mtgjson
def get_set(card_set: str) -> MTGJsonTypes.Set:
    """Get a target MTGJSON 'Set' resource.

    Args:
        card_set: The set to look for, e.g. MH2

    Returns:
        MTGJson 'Set' object.
    """
    with requests.get(
        url=(MTGJsonURL.API_SETS / card_set.upper()).with_suffix('.json'),
        headers=request_header_default.copy()
    ) as r:
        r.raise_for_status()
        _obj = r.json().get('data', {})
        return MTGJsonTypes.Set(**_obj)


@request_handler_mtgjson
def get_set_list() -> list[MTGJsonTypes.SetList]:
    """Get the current MTGJSON 'SetList' resource.

    Returns:
        A list of MTGJSON 'SetList' objects.
    """
    with requests.get(
        url=MTGJsonURL.API_SET_LIST,
        headers=request_header_default.copy(),
        stream=True,
    ) as r:
        r.raise_for_status()
        r.raw.decode_content = True
        return [MTGJsonTypes.SetList(**n) for n in ijson.items(r.raw, "data.item")]


@request_handler_mtgjson
def yield_set_list_raw() -> Iterator[dict]:
    """Get the current MTGJSON 'SetList' resource as raw dictionaries.

    Returns:
        A list of dictionaries representing MTGJSON 'SetList' objects.
    """
    with requests.get(
        url=MTGJsonURL.API_SET_LIST,
        headers=request_header_default.copy(),
        stream=True,
    ) as r:
        r.raise_for_status()
        r.raw.decode_content = True
        for n in ijson.items(r.raw, "data.item"):
            yield n


"""
* Downloading JSON Assets
"""


@request_handler_mtgjson
def cache_meta(path: Path) -> Path:
    """Stream a target MTGJSON 'Meta' resource and save it to a file.

    Args:
        path: Path object where the JSON data will be saved.
    """
    download_file(
        url=MTGJsonURL.API_META,
        path=path)
    return path


@request_handler_mtgjson
def cache_set(card_set: str, path: Path) -> Path:
    """Stream a target MTGJSON 'Set' resource and save it to a file.

    Args:
        card_set: The set to look for, ex: MH2
        path: Path object where the JSON data will be saved.
    """
    download_file(
        url=(MTGJsonURL.API_SETS / card_set.upper()).with_suffix('.json'),
        path=path)
    return path


@request_handler_mtgjson
def cache_set_list(path: Path) -> Path:
    """Stream the current MTGJSON 'SetList' resource and save it to a file.

    Args:
        path: Path object where the JSON data will be saved.
    """
    download_file(
        url=MTGJsonURL.API_SET_LIST,
        path=path)
    return path


@request_handler_mtgjson
def cache_decks_all(path: Path, remove: bool = False) -> Path:
    """Stream the current MTGJSON 'AllDeckFiles' archive, save it, and extract it.

    Args:
        path: Directory to unpack the 'AllDeckFiles' MTGJSON archive.
        remove: Whether to remove archive after extracting.

    Returns:
        Path to the unpacked 'AllDeckFiles' MTGJSON directory.
    """
    archive = path / MTGJsonURL.API_ALL_DECK_FILES_GZ.name
    download_file(
        url=MTGJsonURL.API_ALL_DECK_FILES_GZ,
        path=archive)

    # Unpack the contents
    unpack_tar_gz(archive)
    if remove:
        os.remove(archive)
    # Remove suffix (twice for .tar.gz)
    return archive.with_suffix('').with_suffix('')


@request_handler_mtgjson
def cache_sets_all(path: Path, remove: bool = False) -> Path:
    """Stream the current MTGJSON 'AllSetFiles' archive, save it, and extract it.

    Args:
        path: Directory to unpack the 'AllSetFiles' MTGJSON archive.
        remove: Whether to remove archive after extracting.

    Returns:
        Path to the unpacked 'AllSetFiles' MTGJSON directory.
    """
    archive = path / MTGJsonURL.API_ALL_SET_FILES_GZ.name
    download_file(
        url=MTGJsonURL.API_ALL_SET_FILES_GZ,
        path=archive)

    # Unpack the contents
    unpack_tar_gz(archive)
    if remove:
        os.remove(archive)
    # Remove suffix (twice for .tar.gz)
    return archive.with_suffix('').with_suffix('')
