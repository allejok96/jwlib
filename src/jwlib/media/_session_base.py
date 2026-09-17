from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict
from typing import Iterable

from . import const
from ._category import Category
from ._language import Language
from ._media import Media


class BaseSession(ABC):
    """Used to fetch :class:`Category` and :class:`Media` from the server."""

    categories: dict[str, Category]
    """Cached categories.

    The categories are indexed by :attr:`Category.key`.

    See also: :meth:`get_category`.
    """

    def __init__(self, language: str = 'E', client_type: str = const.CLIENT_FIRETV):
        """Set up a session used to fetch :class:`Category` and :class:`Media`.

        Fetched categories are cached within the session.

        :param language: JW language code.
        :param client_type: The default is :const:`CLIENT_FIRETV`.
                            To get as much data as possible use :const:`CLIENT_NONE`.
        """
        self.language = language
        self.client_type = client_type
        self.categories: dict[str, Category] = {}


    # ================
    # Cache management
    # ================

    def load_categories(self, cache: Iterable[dict]) -> None:
        """Load category data from a cache dump.

        This updates existing categories similar to :meth:`dict.update`.
        """
        for category_data in cache:
            cat = Category.create(**category_data, session=self)
            self.categories[cat.key] = cat

    def dump_categories(self) -> list[dict]:
        """Dump category cache to a format that may be serialized to JSON etc."""

        dump = []
        for cat in self.categories.values():
            cat_dict = asdict(cat)
            del cat_dict['session']
            dump.append(cat_dict)
        return dump

    # ==============
    # Public getters
    # ==============

    def get_category(self, key=const.ROOT_CATEGORY, *, include_media=True) -> Category:
        """Get a :class:`Category` from cache or from the server.

        :param key: Code name.
        :param include_media: Setting this to False may speed up JSON parsing significantly
            for some categories, but will result in extra requests if :meth:`get_media` is called later.
        """
        if key not in self.categories:
            self.categories[key] = self.request_category(key, include_media=include_media)

        return self.categories[key]

    @abstractmethod
    def get_languages(self) -> list[Language]:
        """Return list of available Languages"""
        ...

    @abstractmethod
    def get_media(self, key: str) -> Media:
        """Request a :class:`Media` object from the server.

        Unlike :meth:`get_category` this returns a new instance each time.
        """
        ...

    @abstractmethod
    def get_translations(self) -> dict[str, str]:
        """Return a dict of string IDs and translated string used at the website"""
        ...

    # ============
    # Semi-private
    # ============

    @abstractmethod
    def request_category(self, key: str, *, include_media=True) -> Category:
        """Fetch and create a new :class:`Category` instance.

        Mainly for internal use, but may be overridden for unit testing, etc.

        Called by :meth:`get_category` when a category is missing from the cache.
        The main implementation fetches data from jw.org.
        """
        ...

    @abstractmethod
    def request_category_media(self, key: str, *, offset: int) -> tuple[list[Media], int]:
        """Fetch a (partial) list of :class:`Media` for the given category.

        Mainly for internal use, but may be overridden for unit testing, etc.

        Called by :meth:`Category.get_media` when the media list got truncated
        because it was too long, or because include_media=False was used.
        The main implementation fetches data from jw.org.

        :param:`offset` is used to get the next "page".
        :returns: a list of :class:`Media` together with the category's total media count.

        .. note::
            As of 2026-09, the server has not yet enforced an upper limit of the media list.
            "VODPgmEvtMorningWorship" delivers 380+ items in a single response.
        """
        ...


