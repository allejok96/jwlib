"""
Functions for the different API endpoints
"""
from __future__ import annotations

from ..common import NotFoundError, _get_json
from .const import CATEGORY_CONTAINER, CLIENT_NONE, ROOT_CATEGORY

_API_BASE = 'https://b.jw-cdn.org/apis/mediator/v1'


def _request_category_data(language: str, key: str, *, client: str, include_media: bool, media_list_offset=0) -> dict:
    """Request category data from the server"""

    # If this is called for ROOT_CATEGORY it means we're trying to refresh() it
    if key == ROOT_CATEGORY:
        return _root_category_dict(subcategories=_request_top_categories(language, client))

    query = {
        'clientType': client if client != CLIENT_NONE else None,
        # detailed controls whether subcategories will be included in the response
        # None means no, anything else means yes
        'detailed': 1,
        # offset controls at which index the media list will start
        # this is useful in case the total length is larger than 'limit'
        'offset': (media_list_offset or None) if include_media else None,
        # limit controls the max length of the media list
        # None means the server will decide
        'limit': None if include_media else 0,
        # mediaLimit controls the max length of the media list inside subcategories
        # None means the server will decide
        'mediaLimit': None if include_media else 0,
    }
    try:
        response = _get_json(f'{_API_BASE}/categories/{language}/{key}', query)
        category_data = response['category']
        if not isinstance(category_data, dict):
            raise TypeError(f'expected dict, got {type(category_data)}')
    except (NotFoundError, KeyError, TypeError) as e:
        raise NotFoundError(f'{language}/{key}') from e

    # Save the total number of media items available, it may be used later for pagination
    # (this is only available for type 'ondemand' categories)
    try:
        category_data['_paginationTotalCount'] = response['pagination']['totalCount']
    except (KeyError, TypeError):
        pass

    # If we requested no media items for subcategories, we must make the subcategories aware of this
    # so that calls to get_media() doesn't think there is actually no media.
    if include_media is False:
        for subcategory_data in category_data.get('subcategories', []):
            try:
                subcategory_data['_paginationLimit'] = 0
            except TypeError:
                pass

    return category_data


def _request_top_categories(language: str, client: str) -> list[dict]:
    """Request list of top-level categories from the server"""

    # Never call this with detailed=1
    # It results in 'subcategories': {} which is a TypeError (should be a list)
    # This is a bug on the server side
    query = {'clientType': client if client != CLIENT_NONE else None}
    try:
        response = _get_json(f'{_API_BASE}/categories/{language}', query)
        top_level_list = response['categories']
        if not isinstance(top_level_list, list):
            raise TypeError(f'expected list, got {type(top_level_list)}')
    except (NotFoundError, KeyError, TypeError) as e:
        raise NotFoundError(f'{language}') from e
    return top_level_list


def _root_category_dict(**kwargs) -> dict:
    """Return a dict with root category data

    The server has no 'root' category, it's just a list of top-level categories. But we make one to
    make things more convenient and also give it a 'key' to not produce empty values for templates.

    We use a function return a unique object each time, instead of just having this as a global constant,
    since dicts are mutable that could (and have) messed things up during testing.
    """
    return dict(
        description='Top-level category of all video and audio categories',
        images={},
        key=ROOT_CATEGORY,
        name='All Categories',
        tags=[],
        type=CATEGORY_CONTAINER,
        **kwargs
    )


def _request_media_data(language: str, key: str, *, client: str) -> dict:
    """Request media data from the server"""

    try:
        query = {'clientType': client if client != CLIENT_NONE else None}
        response = _get_json(f'{_API_BASE}/media-items/{language}/{key}', query)
        media_data = response['media'][0]
    # It seems to return HTTP 200 with a response of [] if the item doesn't exist...
    except (NotFoundError, TypeError, KeyError, IndexError) as e:
        raise NotFoundError(f'{language}/{key}') from e
    return media_data


def _request_languages(language: str) -> list[dict]:
    """Request list of language data from the server"""

    return _get_json(f'{_API_BASE}/languages/{language}/web')['languages']


def request_translations(language: str) -> dict:
    """Return a dict of string IDs and translated string used at the website"""

    return _get_json(f'{_API_BASE}/translations/{language}')['translations'][language]
