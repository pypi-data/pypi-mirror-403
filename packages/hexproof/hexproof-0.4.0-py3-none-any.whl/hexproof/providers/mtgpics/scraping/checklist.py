"""
* Checklist Targeted Scraping
* Scrapes from: https://www.mtgpics.com/set_checklist?set={num}
"""
# Standard Libray Imports
from datetime import datetime
from typing import Iterator

# Third Party Imports
from bs4 import BeautifulSoup, Tag
from omnitils.exceptions import return_on_exception
from omnitils.strings import normalize_datestr
import yarl

# Local Imports
from hexproof.mtgpics.constants import urls as MTGPicsURL
from hexproof.mtgpics import schemas as MTGPics


@return_on_exception([])
def scrape_card_rows(soup: BeautifulSoup) -> list[Tag]:
    """Returns a list of rows representing cards on an MTGPics set 'checklist' page.

    Args:
        soup: A BeautifulSoup object generated from parsing a web page.

    Returns:
        A list of div element tags representing MTGPics cards.
    """
    return soup.find_all(
        "div",
        {"style": "display:block;margin:0px 2px 0px 2px;border-top:1px #cccccc dotted;"}
    )


@return_on_exception(0)
def scrape_card_count(soup: BeautifulSoup) -> int:
    """Returns the card count displayed on an MTGPIcs set 'checklist' page.

    Args:
        soup: A BeautifulSoup object generated from parsing a web page.

    Returns:
        A list of div element tags representing MTGPics cards.
    """
    div = soup.find("div", {"id": "select_nb_All"})
    if not div:
        return 0
    return int(''.join(n for n in div.text if n.isdigit()) or '0')


@return_on_exception(None)
def scrape_set_code(soup: BeautifulSoup) -> str | None:
    """Returns the code string for an MTGPics set by scraping its card checklist page.

    Args:
        soup: A BeautifulSoup object generated from parsing a web page.

    Returns:
        A string representing the 'code' of an MTGPics set page.
    """

    # Grab the first card div listed
    div = scrape_card_rows(soup)
    if not div:
        return None
    div = div[0]

    # Get columns from the first card listed
    cols = div.find_all("td")
    if len(cols) < 3:
        return None

    # Grab a URL tag from the name column
    url = cols[2].find("a", href=True)
    if url is None or url.get('href') is None:
        return None
    if 'card?ref=' not in url['href']:
        return None

    # Parse the code
    return url['href'].split('card?ref=')[-1][:3].lower()


def scrape_date(soup: BeautifulSoup) -> datetime:
    """Returns the release date displayed on an MTGPIcs set 'checklist' page.

    Args:
        soup: A BeautifulSoup object generated from parsing a web page.

    Returns:
        A date string in format 'YYYY-MM-DD'.
    """
    date = soup.find('div', class_='titleB16')
    date_str = normalize_datestr(date.text.split(':')[-1].strip())
    return datetime.strptime(date_str, '%Y-%m-%d')


@return_on_exception('Unnamed Set')
def scrape_name(soup: BeautifulSoup) -> str:
    """Returns the set name from the title tag of an MTGPIcs set 'checklist' page.

    Args:
        soup: A BeautifulSoup object generated from parsing a web page.

    Returns:
        A string representing the name of this set.
    """
    name = soup.find('title')
    if not name:
        return 'Unnamed Set'
    return name.text.replace(' - mtgpics.com', '').strip()


@return_on_exception(None)
def scrape_url_logo(soup: BeautifulSoup) -> yarl.URL:
    """Returns the image URL of the logo for an MTGPics set 'checklist' page.

    Args:
        soup: A BeautifulSoup object generated from parsing a web page.

    Returns:
        A URL for this set's logo image.
    """
    url = MTGPicsURL.SITE / soup.find("td", {
        "class": "titleB16",
        "align": "center",
        "width": "50%"
    }).find('img').get('src')
    return url


@return_on_exception([])
def get_cards_list(
    soup: BeautifulSoup,
    first_only: bool = False,
    multi: bool = False
) -> list[MTGPics.Card]:
    """Retrieves a dictionary of cards scraped from a Set 'checklist' page.

    Args:
        soup: A BeautifulSoup object generated from parsing a web page.
        first_only: Whether to only retrieve the first card in the list.
        multi: Whether to treat this as a MTGPics set that contains multiple Scryfall sets.

    Returns:
        A list of MTGPics checklist cards.
    """
    cards = []

    # Iterate over numbered cards
    for row in scrape_card_rows(soup):

        # Extract other columns
        cols = row.find_all('td')
        if not cols:
            return []
        name_tag = cols[2].find('a', href=True)
        subset_tag = cols[2].find('div') if multi else None
        artist_tag = cols[6].find('a')
        ref = name_tag['href'].split('=')[-1]
        url = MTGPicsURL.SITE / name_tag['href']
        url_img = MTGPicsURL.PICS_REG / f"{ref[:3]}/{ref[3:]}.jpg"

        # Add card to dataset
        cards.append(
            MTGPics.Card(
                number=cols[0].text.strip(),
                name=name_tag.text.strip(),
                ref=name_tag['href'].split('=')[-1],
                type=cols[3].text.strip(),
                subset=subset_tag.text.strip() if subset_tag else None,
                artist=artist_tag.text.strip() if artist_tag else None,
                pt=cols[4].text.strip(),
                # Todo: Add arts
                arts=[],
                url=url,
                url_img=url_img
            ))
        if first_only:
            return cards

    # Return dataset
    return cards


@return_on_exception([])
def yield_cards_list(
    soup: BeautifulSoup,
    multi: bool = False
) -> Iterator[MTGPics.Card]:
    """Retrieves a dictionary of cards scraped from a Set 'checklist' page.

    Args:
        soup: A BeautifulSoup object generated from parsing a web page.
        multi: Whether to treat this as a MTGPics set that contains multiple Scryfall sets.

    Returns:
        A list of MTGPics checklist cards.
    """

    # Iterate over numbered cards
    for row in scrape_card_rows(soup):

        # Extract other columns
        cols = row.find_all('td')
        if not cols:
            return []
        name_tag = cols[2].find('a', href=True)
        subset_tag = cols[2].find('div') if multi else None
        artist_tag = cols[6].find('a')
        ref = name_tag['href'].split('=')[-1]
        url = MTGPicsURL.SITE / name_tag['href']
        url_img = MTGPicsURL.PICS_REG / f"{ref[:3]}/{ref[3:]}.jpg"

        # Add card to dataset
        yield MTGPics.Card(
            number=cols[0].text.strip(),
            name=name_tag.text.strip(),
            ref=name_tag['href'].split('=')[-1],
            type=cols[3].text.strip(),
            subset=subset_tag.text.strip() if subset_tag else None,
            artist=artist_tag.text.strip() if artist_tag else None,
            pt=cols[4].text.strip(),
            # Todo: Add arts
            arts=[],
            url=url,
            url_img=url_img)
    return None