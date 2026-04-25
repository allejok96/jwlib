"""
Wrappers for the "mediator" API used in the video section at `jw.org <http://jw.org>`_.

The common way to start is to create a :class:`Session` in your language
of choice, use :meth:`~Session.get_category` to get the root and
work your way from there using :meth:`~Category.get_subcategories` and
:meth:`~Category.get_media`:

.. doctest::

    >>> import jwlib.media as jw
    >>> session = jw.Session(language='E')
    >>> broadcasting = session.get_category('VODStudio')
    >>> for subcategory in broadcasting.get_subcategories():
    >>>     for media in subcategory.get_media():
    >>>         file = media.get_file()
    >>>         print(media.title, file.url)
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
