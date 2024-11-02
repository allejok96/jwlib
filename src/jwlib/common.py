"""
Utility functions shared across jwlib
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)


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
            raise TypeError(f'{self.__class__} cannot be initialized with {type(data)}')
        self.data = data

    def _get_int(self, key, default: int = 0):
        try:
            return int(self.data[key])
        except (KeyError, TypeError, ValueError):
            if default is not None:
                logger.debug('%s contains invalid data', self, exc_info=True)
                return default
            raise

    def _get_float(self, key, default: float = 0.0):
        try:
            return float(self.data[key])
        except (KeyError, TypeError, ValueError):
            if default is not None:
                logger.debug('%s contains invalid data', self, exc_info=True)
                return default
            raise

    def _get_string(self, key, default: str | None = None) -> str:
        """Return a non-zero string"""

        value = self.data.get(key)
        if not isinstance(value, str) or value == '':
            if default is not None:
                logger.debug(f'{self} contains invalid data', exc_info=True)
                return default
            raise

        return value


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
