"""
* MTGPics Page Scraping
"""
# Standard Library Imports
from concurrent.futures import Future, ThreadPoolExecutor
import os
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import Any, Optional, Iterator
from urllib.parse import unquote

# Third Party Imports
import yarl
from bs4 import BeautifulSoup, ResultSet
from loguru import logger
from omnitils.files import dump_data_file, load_data_file
from omnitils.strings import normalize_str

# Local Imports
from hexproof.mtgpics.constants import urls as MTGPicsURL
from hexproof.mtgpics.fetch import get_page_html
from hexproof.mtgpics.scraping.checklist import (
    scrape_set_code,
    scrape_card_count,
    scrape_date,
    scrape_name,
    get_cards_list,
    yield_cards_list, scrape_url_logo)
from hexproof.mtgpics.scraping.sets_chrono import get_set_chrono_ids
from hexproof.mtgpics import schemas as MTGPics

"""
* Root Scraping Classes
"""


class Page:
    """Represents an MTGPics page."""
    _url_root = MTGPicsURL.SITE

    def __init__(self, params: dict[str, Any] = None):
        if params is None:
            params = {}
        self._url = self._url_root.with_query(params)
        self._html = get_page_html(self._url)
        self._soup = BeautifulSoup(
            markup=self._html,
            features='html.parser')


"""
* Bulk Set Scraping Classes
"""


class PageSets(Page):
    """Parent class representing an MTGPics page which contains 'Set' links to scrape."""

    """
    * Scraped Properties
    """

    @cached_property
    def set_ids(self) -> list[str]:
        """set[str]: A non-repeating list of all Set ID strings present on the page."""
        return []

    """
    * Export Methods
    """

    def get_set_ids(self) -> list[str]:
        """Functional endpoint to access set IDs list property."""
        return [n for n in self.set_ids]

    def get_sets(self) -> list[MTGPics.Set]:
        """Returns a list of each set on this page as a 'ScrapedSet' object."""
        return [PageSetChecklist(n).get_object() for n in self.set_ids]

    def yield_sets(self) -> Iterator[MTGPics.Set]:
        """Yields each set on this page as a 'ScrapedSet' object."""
        for n in self.set_ids:
            yield PageSetChecklist(n).get_object()


class PageSetsAll(PageSets):
    """Represents the MTGPics page from the `sets` endpoint (all sets).

    Note:
        Does not actually list every single set, some are only visible in the chronological list.
    """
    _url_root = MTGPicsURL.SETS

    """
    * Scraped Properties
    """

    @cached_property
    def set_ids(self) -> list[str]:
        """set[str]: A non-repeating list of all Set ID strings present on the page."""
        return list(set(
            link['href'].replace('set?set=', '').strip()
            for link in self._soup.find_all('a', href=True)
            if link.get('href', '').startswith('set?set=')
        ))


class PageSetsChrono(PageSets):
    """Represents an MTGPics page from the `sets_chrono` endpoint.

    Note:
        The 'Chronological Order' page likely does not list every set, some are only available on the main
        'All Sets' page.
    """
    _url_root = MTGPicsURL.SETS_CHRONO

    def __init__(self, number: str):
        super().__init__(
            params={'page_nb': number})

    """
    * Scraped Properties
    """

    @cached_property
    def set_rows(self) -> ResultSet:
        """ResultSet: Returns a set of rows each representing a set on the page."""
        return self._soup.find_all("div", {
            "style": "padding:8px 0px 5px 0px;border-top:1px #cccccc dotted;"
        })

    @cached_property
    def set_ids(self) -> list[str]:
        """set[str]: A non-repeating list of all Set ID strings present on the page."""
        return get_set_chrono_ids(self._soup)


"""
* Target Set Scraping Classes
"""


class PageSetChecklist(Page):
    """Represents an MTGPics page from the `set_checklist` endpoint."""
    _url_root = MTGPicsURL.SET_CHECKLIST

    def __init__(self, ref: str):
        super().__init__(
            params={'set': ref})

    """
    * Scraped Properties
    """

    @cached_property
    def code(self) -> str | None:
        """str | None: The 'set code' of this set page. Returns None if unavailable."""
        return scrape_set_code(self._soup)

    @cached_property
    def id(self) -> str:
        """str: The numbered 'ref' that identifies this page."""
        return unquote(str(self._url)).split('=')[-1]

    @cached_property
    def card_count(self) -> int:
        """int: The number of cards listed on this page."""
        return scrape_card_count(self._soup)

    @cached_property
    def date(self) -> datetime:
        """str: The release date of this page's set. Uses YYYY-MM-DD format."""
        return scrape_date(self._soup)

    @cached_property
    def name(self) -> str:
        """str: The name of this page's set."""
        return scrape_name(self._soup)

    @cached_property
    def normalized(self) -> str:
        """str: The name of this page's set, string normalized with spaces removed."""
        return normalize_str(self.name, no_space=True)

    @cached_property
    def url_logo(self) -> yarl.URL:
        """URL: The logo image url of this page's set."""
        return scrape_url_logo(self._soup)

    """
    * Export Methods
    """

    def get_object(self) -> Optional[MTGPics.Set]:
        """Combines this page's scraped data into an MTGPicsSet object.

        Returns:
            An MTGPicsSet object.
        """
        if not self._html:
            return None
        return MTGPics.Set(
            code=self.code,
            id=self.id,
            card_count=self.card_count,
            date=self.date,
            name=self.name,
            normalized=self.normalized,
            url_logo=self.url_logo
        )

    def get_cards(self, multi: bool = False) -> list[MTGPics.Card]:
        """Retrieves a list of all cards listed on this set checklist page.

        Args:
            multi: Whether to treat this as an MTGPics set that contains multiple sets.

        Returns:
            A list of MTGPicsChecklistCard objects.
        """
        return get_cards_list(self._soup, multi=multi)

    def yield_cards(self, multi: bool = False) -> Iterator[MTGPics.Card]:
        """Yields each card listed on this set checklist page.

        Args:
            multi: Whether to treat this as an MTGPics set that contains multiple sets.

        Returns:
            A generator of MTGPicsChecklistCard objects.
        """
        for n in yield_cards_list(self._soup, multi=multi):
            yield n


"""
* Bulk Scraping Functions
"""


def get_all_set_ids(chrono_pages: int = 19) -> list[str]:
    """Collects all set ID's from MTGPics using all known pages containing sets.

    Todo:
        Implement quick check to grab number of chronological sets pages. Deprecate `chrono_pages` arg.

    Args:
        chrono_pages: Number of pages on the chronological sets endpoint.

    Returns:
        A list of ID strings (non-repeating).
    """

    # Use pool to execute jobs concurrently
    results: list[Future] = []
    set_ids: list[str] = []
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as runner:

        # Get set IDs from 'All Sets' page
        results.append(runner.submit(PageSetsAll().get_set_ids))

        # Get set ID's from each chronological page
        for n in range(1, chrono_pages):
            results.append(runner.submit(PageSetsChrono(str(n)).get_set_ids))

        # Wait for each job to finish, then remove repeating
        [set_ids.extend(n.result()) for n in results]
    return list(set(set_ids))


def get_all_sets(cached_file: Optional[Path] = None, chrono_pages: int = 19) -> dict[str, MTGPics.Set]:
    """Scrapes all sets from MTGPics, or returns current cached data if specified and available.

    Todo:
        Implement quick check to grab number of chronological sets pages. Deprecate `chrono_pages` arg.

    Args:
        cached_file: Cached data file to use if path is provided and exists. If path is provided but doesn't
            exist, will cache new data pulled.
        chrono_pages: Number of pages on the chronological sets endpoint.

    Returns:
        Each set on MTGPics as a ScrapedSet object.
    """

    # Use cached version if specified and available
    if cached_file and cached_file.is_file():
        try:
            data = load_data_file(cached_file)
            return data
        except Exception as e:
            logger.exception(e)
            logger.warning('Unable to load cached MTGPics set data!')

    def _get_data(_ref: str) -> MTGPics.Set:
        """Scrapes a checklist page and exports 'ScrapedSet' object."""
        return PageSetChecklist(ref=_ref).get_object()

    # Retrieve set details from each URL
    set_ids = get_all_set_ids(chrono_pages)
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as runner:
        results = runner.map(_get_data, set_ids)
        data = {r['id']: r for r in list(results) if r}

    # Cache results if needed
    if cached_file:
        try:
            dump_data_file(data, cached_file)
        except Exception as e:
            logger.exception(e)
            logger.info('Unable to dump scraped MTGPics set data!')
    return data
