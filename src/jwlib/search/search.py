from __future__ import annotations

import logging
from typing import Optional, List, Dict
from urllib.parse import quote
from urllib.request import urlopen

from ..common import _get_json, _DictWrapper
from .const import FILTER_ALL

__all__ = (
    'PageLink',
    'Result',
    'ResultGroup',
    'ResultPage',
    'search',
    'SearchInsight',
)

logger = logging.getLogger(__name__)

_API_BASE = 'https://b.jw-cdn.org/apis/search'
_TOKEN_URL = 'https://b.jw-cdn.org/tokens/jworg.jwt'


def search(query: str, *, filter_type=FILTER_ALL, language='E', sort='') -> ResultPage:
    """Perform a search and return a :class:`ResultPage`.

    :param query: search term
    :param filter_type: see ``FILTER_*`` in :mod:`~jwlib.search.const`
    :param language: language code
    :param sort: see ``SORT_*`` in :mod:`~jwlib.search.const`
    """
    assert query
    assert filter_type
    assert language

    token = urlopen(_TOKEN_URL).read().decode('utf-8')
    response = _get_json(
        url=f'{_API_BASE}/results/{language}/{filter_type}',
        query={'sort': sort, 'q': query},
        headers={'Authorization': 'Bearer ' + token}
    )

    return ResultPage(response, token)


class ResultPage(_DictWrapper):
    """Page of search results, navigation and statistics."""

    def __init__(self, data: dict, token: str):
        super().__init__(data)
        self._token = token

    @classmethod
    def _from_link(cls, link: PageLink):
        """Loads page data from a URL."""
        response = _get_json(_API_BASE + link.path, headers={'Authorization': 'Bearer ' + link._token})
        return ResultPage(response, token=link._token)

    def _generate_links(self, link_data_list: List[dict]) -> List[PageLink]:
        """Generates PageLinks from link data."""
        query = quote(self.insight.query)
        links = []

        for link_data in link_data_list:
            # We must add the query to Filter and Sort links
            if link_data.get('link', '').endswith('q='):
                link_data['link'] += query
            links.append(PageLink(link_data, self._token))

        return links

    @property
    def filters(self) -> List[PageLink]:
        """List of links that will apply different search filters."""
        return self._generate_links(self.data.get('filters', []))

    @property
    def first(self) -> Optional[PageLink]:
        """Link to the first page, or `None` if there are no results."""
        for link in self.pagination:
            if link.type == 'first':
                return link
        return None

    @property
    def insight(self) -> SearchInsight:
        """Information about the results."""
        return SearchInsight(self.data['insight'])

    @property
    def last(self) -> Optional[PageLink]:
        """Link to the last page, or `None` if there's just one page."""
        for link in self.pagination:
            if link.type == 'last':
                return link
        return None

    @property
    def layout(self) -> List[str]:
        """Tags that control the webpage layout.

        Known values:

        - ``flat`` - results are shown as rows
        - ``grid`` - results are shown as a grid
        - ``audio``
        - ``videos``
        - ``publications``
        """
        return self.data['layout']

    @property
    def messages(self) -> List[str]:
        """List of error messages, etc."""
        return [
            m['message']
            for m in self.data['messages']
            if 'message' in m
        ]

    @property
    def next(self) -> Optional[PageLink]:
        """Link to the next page, or `None` if this is the last page."""
        for link in self.pagination:
            if link.type == 'next':
                return link
        return None

    @property
    def pagination(self) -> List[PageLink]:
        """List of navigation links."""
        return [
            PageLink(link, self._token)
            for link in self.data.get('pagination', {}).get('links', [])
            # Some items in this list are just {"type": "spacer"}
            if link.get('link')
        ]

    @property
    def pagination_label(self) -> str:
        """Human-readable navigation info.

        For example "Showing 1 - 12 of 341".
        """
        return self.data.get('pagination', {}).get('label', '')

    @property
    def previous(self) -> Optional[PageLink]:
        """Link to the previous page, or `None` if this is the first page."""
        for link in self.pagination:
            if link.type == 'previous':
                return link
        return None

    @property
    def results(self) -> List[Result]:
        """List of search results.

        If you're using :const:`FILTER_ALL`, this will flatten all groups into a single list of results.
        """
        return [r for g in self.result_groups
                for r in g.results]

    @property
    def result_groups(self) -> List[ResultGroup]:
        """List of search result groups.

        When using :const:`FILTER_ALL`, the search result may contain videos, music and publications.
        These will be grouped in separate sections on the search page, just like this function returns them.

        When using any other filter, the webpage doesn't put results in groups (since there's only one).
        In that case, this property will still return a single unnamed group containing the results.
        To make life easier, the `result` property will flatten all groups into a single list of results.
        """

        groups = []
        default_group = ResultGroup({}, self._token)

        for r in self.data.get('results', []):
            if r.get('type') == 'group':
                groups.append(ResultGroup(r, self._token))
            else:
                default_group.data.setdefault('results', []).append(r)

        if default_group.data:
            groups.append(default_group)

        return groups

    @property
    def sorts(self) -> List[PageLink]:
        """Links to pages where the results are sorted in some other order."""
        return self._generate_links(self.data.get('sorts', []))


class ResultGroup(_DictWrapper):
    """Group of :class:`Result` s of similar type."""

    def __init__(self, data: dict, token: str):
        super().__init__(data)
        self._token = token

    def __repr__(self):
        try:
            return f'<{self.__class__.__name__} {self.label!r}>'
        except (TypeError, LookupError, ValueError):
            return super().__repr__()

    @property
    def label(self) -> str:
        """Group header.

        For example "Audio", "Videos", or an empty string (for publications).
        """
        return self.data.get('label', '')

    @property
    def layout(self) -> List[str]:
        """Tags that control the webpage layout.

        Known values:

        - ``flat`` - results are shown as rows
        - ``carousel`` - results are shown horizontally
        - ``audio``
        - ``videos``
        """
        return self.data.get('layout', [])

    @property
    def links(self) -> List[PageLink]:
        """Links found in the group header."""
        return [PageLink(link, self._token)
                for link in self.data.get('links', [])]

    @property
    def results(self) -> List[Result]:
        """List of results in the group."""

        result_list = []
        for result in self.data.get('results', []):
            if result.get('type') == 'item':
                result_list.append(Result(result))
            else:
                logger.debug(f"skipping item with unexpected type {result.get('type')}")
        return result_list


class Result(_DictWrapper):
    """Search result, including title, image and URL"""

    def __repr__(self):
        try:
            return f'<{self.__class__.__name__} {self.title!r}>'
        except (TypeError, LookupError, ValueError):
            return super().__repr__()

    @property
    def context(self) -> str:
        """Item category, like "BOOKS", used as a header text."""
        return self._get_string('context', '')

    @property
    def deep_links(self) -> List[DeepLink]:
        """List of links to specific points in time"""
        return [DeepLink(link) for link in self.data.get('deepLinks', [])]

    @property
    def duration(self) -> int:
        """Duration in seconds"""

        if 'duration' not in self.data:
            return 0

        t = self._get_string('duration').split(':')
        if len(t) == 3:
            return int(t[0]) * 60 * 60 + int(t[1]) * 60 + int(t[2])
        elif len(t) == 2:
            return int(t[0]) * 60 + int(t[1])
        elif len(t) == 1:
            return int(t[0])
        else:
            raise ValueError(f'Expected a duration like HH:MM:SS, not {t!r}')

    @property
    def image(self) -> Optional[str]:
        """Image URL."""
        return self.data.get('image', {}).get('url')

    @property
    def key(self) -> str:
        """Code name, excluding language code."""
        return self._get_string('lank')

    @property
    def snippet(self) -> str:
        """Matching text, with the matching text enclosed in ``<strong></strong>``."""
        return self._get_string('snippet', '')

    @property
    def title(self) -> str:
        """Display name."""
        return self._get_string('title')

    @property
    def type(self) -> str:
        """Item type.

        See ``RESULT_*`` in :mod:`~jwlib.search.const`.
        """
        return self._get_string('subtype')

    @property
    def urls(self) -> Dict[str, str]:
        """Dictionary of links to this item.

        Example:

        .. code-block::

            {'jw.org': 'https://www.jw.org/...',
             'wol': 'https://wol.jw.org/...'}
        """
        return self.data.get('links', {})

    @property
    def url_jw(self) -> Optional[str]:
        """URL to this item at jw.org."""
        return self.urls.get('jw.org')

    @property
    def url_wol(self) -> Optional[str]:
        """URL to this item at wol.jw.org."""
        return self.urls.get('wol')


class PageLink(_DictWrapper):
    """Link to a :class:`ResultPage`."""

    def __init__(self, data: dict, token: str):
        super().__init__(data)
        self._token = token

    def __repr__(self):
        try:
            return f'<{self.__class__.__name__} {self.label!r}>'
        except (TypeError, LookupError, ValueError):
            return super().__repr__()

    @property
    def label(self) -> str:
        """Link text."""
        return self._get_string('label', '')

    def open(self) -> ResultPage:
        """Fetch and return the :class:`ResultPage`."""
        return ResultPage._from_link(self)

    @property
    def path(self) -> str:
        """Relative link destination, use :meth:`PageLink.open` to open it."""
        return self._get_string('link')

    @property
    def selected(self) -> bool:
        """`True` if the link is currently selected (used to indicate active filter, etc.)."""
        return self._get_bool('selected', False)

    @property
    def type(self) -> Optional[str]:
        """Optional link type.

        Known values:

        - ``first`` - first page
        - ``next`` - next page
        - ``last`` - last page
        - ``more`` - more items of this type (video, audio, etc.)
        """
        return self.data.get('type')


class DeepLink(_DictWrapper):
    """Link to a specific part of a video"""

    def __repr__(self):
        try:
            return f'<{self.__class__.__name__} {self.label!r}>'
        except (TypeError, LookupError, ValueError):
            return super().__repr__()

    @property
    def title(self) -> str:
        """Use-case unknown."""
        return self.data.get('title', '')

    @property
    def label(self) -> str:
        """Label like "Jump to 3:00"."""
        return self.data.get('jumpLabel', '')

    @property
    def lank(self) -> int:
        """Media code name, similar to :meth:`Result.key`."""
        return self.data.get('insight', {}).get('lank', '')

    @property
    def rank(self) -> int:
        """Use-case unknown."""
        return self.data.get('insight', {}).get('rank', 0)

    @property
    def snippet(self) -> str:
        """Blurb, similar to :meth:`Result.snippet`"""
        return self.data.get('snippet', '')

    @property
    def urls(self) -> Dict[str, str]:
        """Dictionary of links, similar to :meth:`Result.urls`."""
        return self.data.get('urls', {})

    @property
    def url_jw(self) -> Optional[str]:
        """URL to this item at jw.org."""
        return self.urls.get('jw.org')


class SearchInsight(_DictWrapper):
    """Information about a search."""

    @property
    def filter(self) -> str:
        """Current search filter.

        See ``FILTER_*`` in :mod:`~jwlib.search.const` for valid values.
        """
        return self._get_string('filter', '')

    @property
    def offset(self) -> int:
        """Number of items skipped before the first item on this page (used for pagination)."""
        return self._get_int('offset')

    @property
    def page(self) -> int:
        """Page number, starting from 1."""
        return self._get_int('page')

    @property
    def query(self) -> str:
        """The search term."""
        return self._get_string('query')

    @property
    def sort(self) -> str:
        """Current sort method.

        See ``SORT_*`` in :mod:`~jwlib.search.const` for valid values.
        """
        return self._get_string('sort', '')

    @property
    def total(self) -> int:
        """Total number of items found (on all pages)."""
        return self.data.get('total', {}).get('value', 0)

    @property
    def total_relation(self) -> str:
        """Precision of the total value.

        Known values:

        - ``eq`` - there are exactly 'total' items
        - ``gte`` - there are more than 'total' items
        """
        return self.data.get('total', {}).get('relation', 'eq')
