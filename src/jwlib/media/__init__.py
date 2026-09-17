"""
Wrappers for the "mediator" API used in the video section at `jw.org <http://jw.org>`_.

The common way to start is to create a :class:`Session` in your language
of choice, use :meth:`~Session.get_category` to get the root and
work your way from there using :meth:`~Category.get_subcategories` and
:meth:`~Category.get_media`:

.. doctest::

    >>> from jwlib.media import get_session
    >>> session = get_session(language='E')
    >>> broadcasting = session.get_category('VODStudio')
    >>> for subcategory in broadcasting.get_subcategories():
    >>>     for media in subcategory.get_media():
    >>>         file = media.get_file()
    >>>         print(media.title, file.url)
"""
from typing import List, Dict

from . import const
from ._api_requests import NotFoundError
from ._category import Category
from ._file import File
from ._language import Language
from ._media import Media
from ._session_base import BaseSession
from ._session_impl import Session
from .._deprecated import deprecated as _deprecated

# TODO this should not be here, but is kept for backwards compatibility
from .const import *

__all__ = (
    'const',

    'BaseSession',
    'Category',
    'File',
    'Language',
    'Media',
    'NotFoundError',
    'Session',

    'get_session',
    'request_languages',
    'request_translations',
)


def get_session(language='E', client_type=const.CLIENT_FIRETV) -> BaseSession:
    """Set up a session used to fetch :class:`Category` and :class:`Media`.

    :param language: JW language code.
    :param client_type: To get as much data as possible (slower) use :const:`CLIENT_NONE`.
    """
    return Session(language, client_type)


# ---------------------------
# For backwards compatibility
# ---------------------------


@_deprecated("Use get_session().get_languages() instead")
def request_languages(language='E') -> List[Language]:
    return get_session(language=language).get_languages()


@_deprecated("Use get_session().get_translations() instead")
def request_translations(language='E') -> Dict[str, str]:
    return get_session(language=language).get_translations()
