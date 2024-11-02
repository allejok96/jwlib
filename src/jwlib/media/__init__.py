"""
Wrappers for the "mediator" API used in the video section at `jw.org <http://jw.org>`_.

The common way to start is to create a :class:`Session` in your language
of choice, use :meth:`~Session.get_category` to get the root and
work your way from there using :meth:`~Category.get_subcategories` and
:meth:`~Category.get_media`:

.. doctest::

    >>> import jwlib.media as jw
    >>> english_session = jw.Session()
    >>> root = english_session.get_category()
    >>> for category in root.get_subcategories():
    >>>     for media in category.get_media():
    >>>         print(media.title)
"""

from ..common import NotFoundError
from .const import *
from .endpoints import request_translations
from .language import Language, request_languages
from .session import Category, File, Media, Session

__all__ = (
    'Session',
    'Category',
    'Media',
    'File',
    'Language',
    'request_languages',
    'request_translations',
    'NotFoundError'
)
