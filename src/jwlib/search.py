"""
Wrapper for the jw.org search API
"""
from __future__ import annotations

from typing import NamedTuple
from urllib.request import urlopen

from .common import _get_json

# Used for search(item_type=)
SEARCH_ALL = 'all'
SEARCH_AUDIO = 'audio'
SEARCH_BIBLE = 'bible'
SEARCH_INDEX = 'indexes'
SEARCH_PUBLICATIONS = 'publications'
SEARCH_VIDEO = 'videos'

# Returned by SearchResult.type
RESULT_AUDIO = 'audio'
RESULT_VIDEO = 'video'
RESULT_BIBLE = 'verse'
RESULT_MAGAZINE = 'periodical'
RESULT_BOOK = 'publication'
RESULT_VIDEO_CAT = 'videoCategory'
RESULT_AUDIO_CAT = 'audioCategory'
RESULT_INDEX = 'index'

_API_BASE = 'https://b.jw-cdn.org/apis/search/results'
_TOKEN_URL = 'https://b.jw-cdn.org/tokens/jworg.jwt'

class Pagination(NamedTuple):
    page_limit: int
    total: int

class SearchResult(dict):
    def __repr__(self):
        return f'<{self.__class__.__name__} {self.key!r}>'

    @property
    def context(self) -> str:
        """Display text for header like 'BOOKS'"""
        return self['context']

    @property
    def duration(self) -> int:
        """Duration in seconds"""
        try:
            t = self['duration'].split(':')
        except AttributeError:
            t = []
        if len(t) == 3:
            return int(t[0]) * 60 * 60 + int(t[1]) * 60 + int(t[2])
        elif len(t) == 2:
            return int(t[0]) * 60 + int(t[1])
        elif len(t) == 1:
            return int(t[0])
        else:
            raise ValueError

    @property
    def image(self) -> str | None:
        try:
            return self['image']['url']
        except (KeyError, TypeError):
            return None

    @property
    def key(self) -> str:
        """Code name excluding language code"""
        return self['lank']

    @property
    def snippet(self) -> str:
        """Matching text, with the match tagged like <strong>this</strong>"""
        return self.get('snippet') or ''

    @property
    def title(self) -> str:
        """Display name"""
        return self['title']

    @property
    def type(self) -> str:
        """Item type

        For valid types see the RESULT_* constants
        """
        return self['subtype']

    @property
    def url_jw(self) -> str | None:
        return self['links'].get('jw.org')

    @property
    def url_wol(self) -> str | None:
        return self['links'].get('wol')


def search(string: str, item_type: str, *, lang='E', offset=0, limit: int | None = None) \
        -> tuple[list[SearchResult], Pagination]:
    """Return a list of SearchResults together with Pagination info and token

    TODO returned ItemCount.per_page is incorrect when search_type=ALL
    TODO does limit=0 mean anything or can we remove it like we do with offset?

    :param string: search term
    :param item_type: item type, see SEARCH_* (default all)
    :param lang: language code
    :param offset: page offset as number of items
    :param limit: max number of items per page
    """

    assert offset >= 0
    assert limit > 0

    query = {
        'q': string,
        'offset': offset or None,
        'limit': limit}
    token = urlopen(_TOKEN_URL).read().decode('utf-8')
    response = _get_json(f'{_API_BASE}/{lang}/{item_type}', query, headers={'Authorization': 'Bearer ' + token})

    items = []
    for r in response['results']:
        # Unpack grouped results
        if r['type'] == 'group':
            for sub in r['results']:
                if sub['type'] == 'item':
                    items.append(SearchResult(sub))
        elif r['type'] == 'item':
            items.append(SearchResult(r))

    try:
        limit = limit or len(items)
        total = response['insight']['total']['value']
    except (KeyError, TypeError):
        limit = 0
        total = 0

    return items, Pagination(limit, total)
