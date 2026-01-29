"""
* CLI Commands: Test - MTGJSON
"""
# Standard Library Imports
import json
import os
from pathlib import Path

# Third Party Imports
from omnitils.files import DisposableDir
from pydantic import ValidationError
from pydantic_core import ErrorDetails
from rich.console import Console
from typer import Typer

# Local Imports
from hexproof.providers.mtgjson import fetch as MTGJsonFetch
from hexproof.providers.mtgjson import schema as MTGJson
from hexproof.utils.validation import format_validation_error_report

# Core variables
project_cwd = Path(__file__).parent.parent.parent.parent
rich_console = Console()

# Command group
MTGJsonTestCLI = Typer(name="mtgjson")

"""
* Commands: MTGJSON
"""


@MTGJsonTestCLI.command("card", help="Test MTGJSON 'Card' object schema.")
def test_mtgjson_schema_card() -> None:
    """Tests MTGJSON schemas defined in `mtgjson.schema.card` module."""
    _ERR: list[ErrorDetails] = []
    _SCHEMA = MTGJson.CardAtomic

    # Test schema for each object
    for k, card_list in MTGJsonFetch.yield_cards_atomic_raw():
        for v in card_list:
            try:
                _OBJ = _SCHEMA(**v)
                assert isinstance(k, str) and isinstance(_OBJ, _SCHEMA)
                del _OBJ
            except ValidationError as e:
                # Track validation errors
                _ERR.extend(e.errors())
            except (OSError, Exception):
                # Critical error
                rich_console.print_exception()
                return rich_console.print(f'❌ Validation Failed: {_SCHEMA.__name__}')

    # Handle user response
    if _ERR:
        rich_console.print(format_validation_error_report(_ERR))
        return rich_console.print(f'❌ Validation Failed: {_SCHEMA.__name__}')
    return rich_console.print(f'✅ Schemas Validated: {_SCHEMA.__name__}')


@MTGJsonTestCLI.command("cardtypes", help="Test MTGJSON 'CardTypes' object schema.")
def test_mtgjson_schema_card_types() -> None:
    """Tests MTGJSON schemas defined in `mtgjson.schema.card_types` module."""
    _SCHEMA = MTGJson.CardTypes

    try:
        _OBJ = MTGJsonFetch.get_card_types()
        assert isinstance(_OBJ, _SCHEMA)
    except ValidationError as e:
        # Validation error
        rich_console.print(format_validation_error_report(e.errors()))
        return rich_console.print(f'❌ Validation Failed: {_SCHEMA.__name__}')
    except (OSError, Exception):
        # Critical error
        rich_console.print_exception()
        return rich_console.print(f'❌ Validation Failed: {_SCHEMA.__name__}')
    return rich_console.print(f'✅ Schemas Validated: {_SCHEMA.__name__}')


@MTGJsonTestCLI.command("deck", help="Test MTGJSON 'Deck' object schema.")
def test_mtgjson_schema_deck() -> None:
    """Tests MTGJSON schemas defined in `mtgjson.schema.deck` module."""
    _ERR: list[ErrorDetails] = []
    _SCHEMA = MTGJson.Deck

    # Check all deck files
    with DisposableDir(path=project_cwd) as _path:
        all_decks = MTGJsonFetch.cache_decks_all(_path)
        for _deck in os.listdir(all_decks):
            _FILE = all_decks / _deck

            # Check deck JSON data file
            if _FILE.is_file() and _FILE.suffix == '.json':
                try:
                    with open(_FILE, 'r', encoding='utf-8') as f:
                        _OBJ = _SCHEMA(**json.load(f).get('data', {}))
                    assert isinstance(_OBJ, _SCHEMA)
                    del _OBJ
                except ValidationError as e:
                    # Track validation errors
                    _ERR.extend(e.errors())
                except (OSError, Exception):
                    # Critical error
                    rich_console.print_exception()
                    return rich_console.print(f'❌ Validation Failed: {_SCHEMA.__name__}')

    # Handle user response
    if _ERR:
        rich_console.print(format_validation_error_report(_ERR))
        return rich_console.print(f'❌ Validation Failed: {_SCHEMA.__name__}')
    return rich_console.print(f'✅ Schemas Validated: {_SCHEMA.__name__}')


@MTGJsonTestCLI.command("decklist", help="Test MTGJSON 'DeckList' object schema.")
def test_mtgjson_schema_deck_list() -> None:
    """Tests MTGJSON schemas defined in `mtgjson.schema.deck_list` module."""
    _ERR: list[ErrorDetails] = []
    _SCHEMA = MTGJson.DeckList

    for n in MTGJsonFetch.yield_deck_list_raw():
        try:
            _OBJ = _SCHEMA(**n)
            assert isinstance(_OBJ, _SCHEMA)
            del _OBJ
        except ValidationError as e:
            # Track validation errors
            _ERR.extend(e.errors())
        except (OSError, Exception):
            # Critical error
            rich_console.print_exception()
            return rich_console.print(f'❌ Validation Failed: {_SCHEMA.__name__}')

    # Handle user response
    if _ERR:
        rich_console.print(format_validation_error_report(_ERR))
        return rich_console.print(f'❌ Validation Failed: {_SCHEMA.__name__}')
    return rich_console.print(f'✅ Schemas Validated: {_SCHEMA.__name__}')


@MTGJsonTestCLI.command("keywords", help="Test MTGJSON 'Keywords' object schema.")
def test_mtgjson_schema_keywords() -> None:
    """Tests MTGJSON schemas defined in `mtgjson.schema.keywords` module."""
    _SCHEMA = MTGJson.Keywords

    try:
        _OBJ = MTGJsonFetch.get_keywords()
        assert isinstance(_OBJ, _SCHEMA)
    except ValidationError as e:
        # Validation error
        rich_console.print(format_validation_error_report(e.errors()))
        return rich_console.print(f'❌ Validation Failed: {_SCHEMA.__name__}')
    except (OSError, Exception):
        # Critical error
        rich_console.print_exception()
        return rich_console.print(f'❌ Validation Failed: {_SCHEMA.__name__}')
    return rich_console.print(f'✅ Schemas Validated: {_SCHEMA.__name__}')


@MTGJsonTestCLI.command("meta", help="Test MTGJSON 'Meta' object schema.")
def test_mtgjson_schema_meta() -> None:
    """Tests MTGJSON schemas defined in `mtgjson.schema.meta` module."""
    _SCHEMA = MTGJson.Meta

    try:
        _OBJ = MTGJsonFetch.get_meta()
        assert isinstance(_OBJ, _SCHEMA)
    except ValidationError as e:
        # Validation error
        rich_console.print(format_validation_error_report(e.errors()))
        return rich_console.print(f'❌ Validation Failed: {_SCHEMA.__name__}')
    except (OSError, Exception):
        # Critical error
        rich_console.print_exception()
        return rich_console.print(f'❌ Validation Failed: {_SCHEMA.__name__}')
    return rich_console.print(f'✅ Schemas Validated: {_SCHEMA.__name__}')


@MTGJsonTestCLI.command("price", help="Test MTGJSON 'PriceFormats' object schema.")
def test_mtgjson_schema_price() -> None:
    """Tests MTGJSON schemas defined in `mtgjson.schema.price` module."""
    _ERR: list[ErrorDetails] = []
    _SCHEMA = MTGJson.PriceFormats

    for k, v in MTGJsonFetch.yield_prices_today_raw():
        try:
            _OBJ = _SCHEMA(**v)
            assert isinstance(k, str) and isinstance(_OBJ, _SCHEMA)
            del _OBJ
        except ValidationError as e:
            # Track validation errors
            _ERR.extend(e.errors())
        except (OSError, Exception):
            # Critical error
            rich_console.print_exception()
            return rich_console.print(f'❌ Validation Failed: {_SCHEMA.__name__}')

    # Handle user response
    if _ERR:
        rich_console.print(format_validation_error_report(_ERR))
        return rich_console.print(f'❌ Validation Failed: {_SCHEMA.__name__}')
    return rich_console.print(f'✅ Schemas Validated: {_SCHEMA.__name__}')


@MTGJsonTestCLI.command("set", help="Test MTGJSON 'Set' object schema.")
def test_mtgjson_schema_set() -> None:
    """Tests MTGJSON schemas defined in `mtgjson.schema.set` module."""
    _ERR: list[ErrorDetails] = []
    _SCHEMA = MTGJson.Set

    # Check all deck files
    with DisposableDir(path=project_cwd) as _path:
        for _FILE in MTGJsonFetch.cache_sets_all(_path).iterdir():
            if not _FILE.is_file() or _FILE.suffix != '.json':
                continue
            try:
                with open(_FILE, 'r', encoding='utf-8') as f:
                    _OBJ = _SCHEMA(**json.load(f).get('data', {}))
                assert isinstance(_OBJ, _SCHEMA)
                del _OBJ
            except ValidationError as e:
                # Track validation errors
                _ERR.extend(e.errors())
            except (OSError, Exception):
                # Critical error
                rich_console.print_exception()
                return rich_console.print(f'❌ Validation Failed: {_SCHEMA.__name__}')

    # Handle user response
    if _ERR:
        rich_console.print(format_validation_error_report(_ERR))
        return rich_console.print(f'❌ Validation Failed: {_SCHEMA.__name__}')
    return rich_console.print(f'✅ Schemas Validated: {_SCHEMA.__name__}')


@MTGJsonTestCLI.command("setlist", help="Test MTGJSON 'SetList' object schema.")
def test_mtgjson_schema_set_list() -> None:
    """Tests MTGJSON schemas defined in `mtgjson.schema.set_list` module."""
    _ERR: list[ErrorDetails] = []
    _SCHEMA = MTGJson.SetList

    for n in MTGJsonFetch.yield_set_list_raw():
        try:
            _OBJ = _SCHEMA(**n)
            assert isinstance(_OBJ, _SCHEMA)
            del _OBJ
        except ValidationError as e:
            # Track validation errors
            _ERR.extend(e.errors())
        except (OSError, Exception):
            # Critical error
            rich_console.print_exception()
            return rich_console.print(f'❌ Validation Failed: {_SCHEMA.__name__}')

    # Handle user response
    if _ERR:
        rich_console.print(format_validation_error_report(_ERR))
        return rich_console.print(f'❌ Validation Failed: {_SCHEMA.__name__}')
    return rich_console.print(f'✅ Schemas Validated: {_SCHEMA.__name__}')


@MTGJsonTestCLI.command(".", help="Test all MTGJSON schemas.")
def test_mtgjson_schema_all() -> None:
    """Tests all MTGJSON schemas."""
    tests = [
        test_mtgjson_schema_card,
        test_mtgjson_schema_card_types,
        test_mtgjson_schema_deck,
        test_mtgjson_schema_deck_list,
        test_mtgjson_schema_keywords,
        test_mtgjson_schema_meta,
        test_mtgjson_schema_price,
        test_mtgjson_schema_set,
        test_mtgjson_schema_set_list
    ]

    # Test each schema
    error_encountered = False
    for func in tests:
        try:
            func()
        except (Exception, AssertionError):
            error_encountered = True
    if error_encountered:
        raise OSError('One or more tests failed!')
