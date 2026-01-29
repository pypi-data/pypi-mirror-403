"""
* CLI Commands: Test - Scryfall
"""
# Standard Library Imports
from pathlib import Path

# Third Party Imports
from pydantic import ValidationError
from pydantic_core import ErrorDetails
from rich.console import Console
from typer import Typer

# Local Imports
from hexproof.providers.scryfall import fetch as ScryfallFetch
from hexproof.providers.scryfall import schema as Scryfall
from hexproof.utils.validation import format_validation_error_report

# Core variables
project_cwd = Path(__file__).parent.parent.parent.parent
rich_console = Console()

# Command group
ScryfallTestCLI = Typer(name="scryfall")

"""
* Commands: Scryfall
"""


@ScryfallTestCLI.command("card", help="Test Scryfall 'Card' object schema.")
def test_scryfall_schema_card() -> None:
    """Tests Scryfall schemas defined in `scryfall.schema.card` module."""
    _SCHEMA = Scryfall.Card

    try:
        _OBJ = ScryfallFetch.get_card_named('Damnation', set_code='TSR')
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


@ScryfallTestCLI.command("ruling", help="Test Scryfall 'Ruling' object schema.")
def test_scryfall_schema_ruling() -> None:
    """Tests Scryfall schemas defined in `scryfall.schema.ruling` module."""
    _ERR: list[ErrorDetails] = []
    _SCHEMA = Scryfall.Ruling

    for n in ScryfallFetch.get_card_rulings('CMA', '176'):
        try:
            # Todo: We need a func for getting raw dict
            # _OBJ = _SCHEMA(**n)
            assert isinstance(n, _SCHEMA)
            # del _OBJ
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


@ScryfallTestCLI.command("set", help="Test Scryfall 'Set' object schema.")
def test_scryfall_schema_set() -> None:
    """Tests Scryfall schemas defined in `scryfall.schema.set` module."""
    _ERR: list[ErrorDetails] = []
    _SCHEMA = Scryfall.Set

    for n in ScryfallFetch.get_set_list():
        try:
            # Todo: We need a func for getting raw dict
            # _OBJ = _SCHEMA(**n)
            assert isinstance(n, _SCHEMA)
            # del _OBJ
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


@ScryfallTestCLI.command(".", help="Test all Scryfall schemas.")
def test_scryfall_schema_all() -> None:
    """Tests all Scryfall schemas."""
    tests = [
        test_scryfall_schema_card,
        test_scryfall_schema_ruling,
        test_scryfall_schema_set
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
