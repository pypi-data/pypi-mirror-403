"""
* Chronological Sets Targeted Scraping
* Scrapes from: https://www.mtgpics.com/sets_chrono?page_nb={num}
"""
# Third Party Imports
from bs4 import BeautifulSoup, ResultSet
from loguru import logger


def get_set_chrono_ids(soup: BeautifulSoup) -> list[str]:
    """Collects all set ID's from an MTGPics chronological set page.

    Args:
        soup: A BeautifulSoup object generated from parsing a web page.

    Returns:
        A list of ID strings (non-repeating).
    """
    # Grab set rows from page
    rows = soup.find_all("div", {
        "style": "padding:8px 0px 5px 0px;border-top:1px #cccccc dotted;"
    })

    sets = []
    for row in rows:
        cols: ResultSet = row.find_all("td")

        # Get columns for this set, skip if required columns are missing
        if len(cols) < 7:
            logger.warning(f"Couldn't extract data from this row:")
            logger.info(str(row))
            continue

        # Parse basic columns
        href = cols[0].find("a", href=True).get("href", "").split("=")
        if len(href) < 2:
            logger.warning(f"Couldn't extract valid link from this row:")
            logger.info(str(row))
            continue
        sets.append(href[-1])

    # Return set ID's
    return list(set(sets))
