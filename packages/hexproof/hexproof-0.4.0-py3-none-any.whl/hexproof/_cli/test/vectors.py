"""
* CLI Commands: Test - MTG-Vectors
"""
# Standard Library Imports
from pathlib import Path

# Third Party Imports
from pydantic import ValidationError
from pydantic_core import ErrorDetails
from rich.console import Console
from typer import Typer

# Local Imports
from hexproof.providers.vectors import fetch as VectorsFetch
from hexproof.providers.vectors import schema as Vectors
from hexproof.utils.validation import format_validation_error_report

# Core variables
project_cwd = Path(__file__).parent.parent.parent.parent
rich_console = Console()

# Command group
VectorsTestCLI = Typer(name="vectors")

"""
* Commands: MTG-Vectors
"""


@VectorsTestCLI.command("release", help='Test MTG Vectors release schema.')
def test_vectors_schema_release() -> None:
    """Tests MTG Vectors 'Manifest' schema and nested schemas defined in `vectors.schema` module."""
    _ERR: list[ErrorDetails] = []
    _SCHEMA = Vectors.Meta

    for n in VectorsFetch.get_latest_release().values():
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


@VectorsTestCLI.command(".", help='Test all MTG Vectors schemas.',)
def test_vectors_schema_all() -> None:
    """Tests all MTG Vectors schemas."""
    tests = [
        test_vectors_schema_release,
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
