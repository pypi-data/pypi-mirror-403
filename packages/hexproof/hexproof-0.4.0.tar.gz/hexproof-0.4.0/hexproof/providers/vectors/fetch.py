"""
* MTG Vectors Request Handling
"""
import os
# Standard Library Imports
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

# Third Party Imports
from loguru import logger
from omnitils.api.github import gh_get_data_json, gh_download_file
from omnitils.files import mkdir_full_perms
from omnitils.files.archive import unpack_zip
from requests import RequestException
import yarl

# Local Imports
from hexproof.providers.vectors.constants import urls as VectorURL
from hexproof.providers.vectors import schema as VectorSchema

"""
* Request Funcs
"""


def get_latest_release(
    owner_repo: Optional[str] = None,
    header: Optional[dict] = None,
    auth_token: Optional[str] = None
) -> Optional[dict[str, VectorSchema.Meta]]:
    """Gets a dictionary of 'Meta' objects, each representing one of the latest release packages
        from the mtg-vectors repository.

    Args:
        owner_repo: Str in '{OWNER}/{REPO}' notation, uses the default mtg-vectors repository if not provided.
        header: Header object to pass with request, uses default if not provided.
        auth_token: Optional auth token to pass with request, increases rate limits.

    Returns:
        A dictionary where keys are the type of release package and values are a 'Meta' object
            describing the date, version, and download URI for that release package.
    """
    url = VectorURL.LATEST_RELEASE
    if owner_repo is not None:
        url = VectorURL.API / 'repos' / owner_repo / 'releases' / 'latest'
    try:
        # Get packages from latest release
        releases = gh_get_data_json(
            url=url,
            header=header,
            auth_token=auth_token)
        _tag = releases['tag_name']
        _, _date = _tag.split('+')

        # Return a dictionary of 'Meta' objects
        return {
            # Package name splits to either "optimized" or "all"
            pkg['name'].split('.')[1]: VectorSchema.Meta(
                date=datetime.strptime(_date, '%Y%m%d').strftime('%Y-%m-%d'),
                version=_tag,
                uri=pkg['browser_download_url']
            ) for pkg in releases['assets']
        }
    except RequestException:
        return logger.error('Unable to pull mtg-vectors release from GitHub!')
    except KeyError:
        return logger.error('Incorrect JSON data returned from mtg-vectors GitHub release!')


"""
* Download Funcs
"""


def cache_vectors_package(
    directory: Path,
    url: Union[yarl.URL, str] = None,
    header: Optional[dict] = None,
    auth_token: Optional[str] = None,
    chunk_size: int = 1024 * 1024 * 8,
    remove_zip: bool = True
) -> Optional[Path]:
    """Updates our 'Set' symbol local assets.

    Args:
        directory: Directory to save and extract the package into.
        url: URL to fetch manifest from.
        header: Header object to pass with request, uses default if not provided.
        auth_token: Optional auth token to pass with request, increases rate limits.
        chunk_size: Chunk size to use when writing package file from stream, default is 8MB.
        remove_zip: Whether to remove the zip after extraction.

    Returns:
        Directory the package was extracted to, if successful, otherwise None.
    """

    # Get zip
    if not directory.is_dir():
        mkdir_full_perms(directory)
    path = directory / 'package.zip'
    try:
        gh_download_file(
            url=url,
            path=path,
            header=header,
            auth_token=auth_token,
            chunk_size=chunk_size)
    except RequestException:
        return logger.error('Unable to reach mtg-vectors symbol package!')
    except FileExistsError:
        return logger.error('Unable to write new mtg-vectors symbol package!')

    # Unpack zip
    try:
        unpack_zip(path)
        if remove_zip:
            os.remove(path)
        return directory
    except Exception as e:
        logger.exception(e)
        logger.error('Unable to unpack vectors package!')
