"""
Wrapper for the `jw.org <http://jw.org>`_ search API.

.. doctest::

    >>> import jwlib.search as jw
    >>> page = jw.search('Caleb')
    >>> for r in page.results:
    >>>     print(r.title, r.url_jw)
"""

from .const import *
from .search import DeepLink, Result, ResultGroup, SearchInsight, ResultPage, PageLink, search

__all__ = (
    'search',
    'ResultPage',
    'ResultGroup',
    'Result',
    'PageLink',
    'DeepLink',
    'SearchInsight',
)
