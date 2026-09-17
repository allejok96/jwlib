from __future__ import annotations

from typing import Optional
from urllib.error import HTTPError

from . import const
from ._api_responses import CategoryResponse, LanguageResponse, MediaResponse, RootResponse, TranslationResponse
from ._api_responses import CompleteCategoryDict, LanguageDict, MediaDict
from .._request import get_json as _unsafe_get_json
from ..common import NotFoundError as _NotFoundErrorBase

API_BASE = 'https://b.jw-cdn.org/apis/mediator/v1'


class NotFoundError(_NotFoundErrorBase):
    """Raised when the server returns HTTP 404"""
    # The base class is for backwards compatibility


def get_json(url: str, query: Optional[dict] = None, *, headers: Optional[dict] = None):
    try:
        return _unsafe_get_json(url, query, headers=headers)
    except HTTPError as e:
        if e.code == 404:
            raise NotFoundError from e
        raise


def fetch_top_level(language: str, client: str) -> list[CompleteCategoryDict]:
    """Request list of top-level categories from the server"""

    # Never call this with detailed=1
    # It results in 'subcategories': {} which is a TypeError (should be a list)
    # This is a bug on the server side
    query = {'clientType': client if client != const.CLIENT_NONE else None}
    try:
        response: RootResponse = get_json(f'{API_BASE}/categories/{language}', query)
        return response['categories']
    except (NotFoundError, KeyError) as e:
        raise NotFoundError(f'{language}/') from e


def fetch_category_dict(language: str, key: str, *, client: str, include_media: bool,
                        media_list_offset=0) -> tuple[CompleteCategoryDict, int]:
    """Request category data from the server"""

    assert language
    assert key
    assert key != const.ROOT_CATEGORY

    query = {
        'clientType': client if client != const.CLIENT_NONE else None,
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
        response: CategoryResponse = get_json(f'{API_BASE}/categories/{language}/{key}', query)

        # The more correct way would be to return UNSET on failure, but if we do so, there is no way to actually
        # get the media count anyway, which might result in an infinite loop, so we just return 0
        # and pretend like everything is fine
        media_count: int = response.get('pagination', {}).get('totalCount', 0)

        return response['category'], media_count
    except (NotFoundError, KeyError) as e:
        raise NotFoundError(f'{language}/{key}') from e


def fetch_media_dict(language: str, key: str, *, client: str) -> MediaDict:
    """Request media data from the server"""

    assert language
    assert key

    try:
        query = {'clientType': client if client != const.CLIENT_NONE else None}
        response: MediaResponse = get_json(f'{API_BASE}/media-items/{language}/{key}', query)
        return response['media'][0]
    except (NotFoundError, IndexError) as e:
        raise NotFoundError(f'{language}/{key}') from e


def fetch_languages(language: str) -> list[LanguageDict]:
    assert language

    response: LanguageResponse = get_json(f'{API_BASE}/languages/{language}/web')
    return response['languages']


def fetch_translations(language: str) -> dict[str, str]:
    assert language

    response: TranslationResponse = get_json(f'{API_BASE}/translations/{language}')
    return response['translations'][language]
