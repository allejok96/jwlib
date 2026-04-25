"""
Utility functions shared across jwlib
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import TypeVar, Callable, Optional

logger = logging.getLogger(__name__)

_T = TypeVar('_T')


class NotFoundError(Exception):
    """Raised when the server returns HTTP 404"""


class _DictWrapper:
    """Wraps server response data"""

    data: dict
    """Object data as returned by the server.

    If you need access to information that has no getter method, you can get it here.

    .. note::
        Editing this directory is an untested feature.
    """

    def __init__(self, data: dict):
        if not isinstance(data, dict):
            raise TypeError(f'Argument must be a dict, not {type(data)}')
        self.data = data

    def _safe_get(self, key: str, default: Optional[_T], getter: Callable[[], _T]) -> _T:
        try:
            return getter()

        except KeyError as e:
            if default is None:
                raise KeyError(f'{self!r}.data[{key!r}] is missing') from e

        except (ValueError, TypeError) as e:
            if default is None:
                raise type(e)(f'{self!r}.data[{key!r}] cannot be {self.data[key]!r}') from e
            logger.debug(f'{self!r}.data[{key!r}] should not be {self.data[key]!r}, replacing with {default!r}')

        return default

    def _get_bool(self, key: str, default: Optional[bool] = None) -> bool:
        return self._safe_get(key, default, lambda: bool(self.data[key]))

    def _get_int(self, key: str, default: Optional[int] = None) -> int:
        return self._safe_get(key, default, lambda: int(self.data[key]))

    def _get_float(self, key: str, default: Optional[float] = None) -> float:
        return self._safe_get(key, default, lambda: float(self.data[key]))

    def _get_string(self, key: str, default: Optional[str] = None) -> str:
        """Return a non-zero string"""

        value = self._safe_get(key, default, lambda: self.data[key])

        if not isinstance(value, str):
            if default is None:
                raise TypeError(f'{self!r}.data[{key!r}] cannot be {value!r}')
            logger.debug(f'{self!r}.data[{key!r}] should not be {value!r}, replacing with {default!r}')

        elif value == '':
            if default is None:
                raise ValueError(f'{self!r}.data[{key!r}] cannot be an empty string')

        else:
            return value

        return default


def _get_json(url: str, query: dict | None = None, *, headers: dict | None = None):
    """Send a query to the server and return loaded JSON"""

    if query:
        # Remove None, convert bool to int
        query = {k: (int(v) if isinstance(v, bool) else v)
                 for k, v in query.items()
                 if v is not None}
        url += '?' + urllib.parse.urlencode(query)

    logger.debug(f'opening: {url}')

    r = urllib.request.Request(url, headers=headers or {})
    try:
        return json.load(urllib.request.urlopen(r))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise NotFoundError from e
        raise
