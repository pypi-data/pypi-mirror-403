"""
* CLI: Testing
"""
# Third Party Imports
from typer import Typer

# Local Imports
from hexproof._cli.test.mtgjson import MTGJsonTestCLI
from hexproof._cli.test.scryfall import ScryfallTestCLI
from hexproof._cli.test.vectors import VectorsTestCLI

# Command group
TestCLI = Typer()
TestCLI.add_typer(MTGJsonTestCLI, name="mtgjson")
TestCLI.add_typer(ScryfallTestCLI, name="scryfall")
TestCLI.add_typer(VectorsTestCLI, name="vectors")
