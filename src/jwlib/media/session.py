"""
Classes related to fetching Categories, Media and Files
"""
from __future__ import annotations

import logging as _logging
import os as _os
import urllib.parse as _urllib_parse
from typing import Iterable, Iterator

from ..common import _DictWrapper
from .const import (
    CATEGORY_CONTAINER,
    CATEGORY_ONDEMAND,
    CLIENT_FIRETV,
    RATIOS_16_9,
    RATIOS_SQUARE,
    ROOT_CATEGORY,
    SIZES_FROM_LARGEST,
    TAG_PREFER_SQUARE_IMAGES,
    TAGS_ITEM_LIMIT,
)
from .endpoints import _request_category_data, _request_media_data, _root_category_dict

__all__ = 'Session', 'Category', 'Media', 'File'

logger = _logging.getLogger(__name__)

# Maximum number of media items that the server will return in a single response.
# If a category has more than this many media items, we have to do some pagination to get them all.
# AFAIK this limit has never been reached, they've just kept increasing it.
# We'll see what happens as categories like VODPgmEvtMorningWorship continue to grow.
# This is the server reported limit as of 2024-07.
default_pagination_limit = 325


class Session:
    """Used to fetch :class:`Category` and :class:`Media` from the server."""

    #: Cached categories
    _category_cache: dict[str, Category]

    def __init__(self, language='E', client_type: str = CLIENT_FIRETV):
        """Set up a session used to fetch :class:`Category` and :class:`Media`.

        Fetched categories are cached within the session.

        :param language: JW language code.
        :param client_type: The default is :const:`CLIENT_FIRETV`.
                            To get as much data as possible use :const:`CLIENT_NONE`.
        """
        self.language = language
        self.client_type = client_type
        self._category_cache: dict[str, Category] = {}

    # ================
    # Cache management
    # ================

    def cached_categories(self) -> Iterable[Category]:
        """Read-only list of the cached categories.

        Clearing the cache is not supported. If you want to refresh single category you may call
        :meth:`Category.refresh`, or you can start a new :class:`Session` to refresh everything.

        Categories are intimately tied to their session. Removing them from the cache
        would create problems when retrieving child or parent classes.
        """
        return self._category_cache.values()

    def load_categories(self, cache: Iterable[dict]) -> None:
        """Load category data from a cache dump.

        This updates existing categories similar to :meth:`dict.update`.
        """
        for category_data in cache:
            self.create_category(category_data)

    def dump_categories(self) -> list[dict]:
        """Dump category cache to a format that may be serialized to JSON etc."""

        return [cat.data for cat in self._category_cache.values()]

    # ================
    # Category methods
    # ================

    def get_category(self, key=ROOT_CATEGORY, *, include_media=True) -> Category:
        """Get a :class:`Category` from cache or from the server.

        :param key: Code name.
        :param include_media: Setting this to False may speed up JSON parsing significantly
            for some categories, but will result in extra requests if :meth:`get_media` is called later.
        """
        if key in self._category_cache:
            return self._category_cache[key]
        else:
            # The ROOT_CATEGORY is just made up by me.
            # Don't bother fetching its subcategories right now,
            # that will happen once :meth:`get_subcategories` is called, if ever.
            if key == ROOT_CATEGORY:
                return self.create_category(_root_category_dict())

            return self.request_category(key, include_media=include_media)

    def request_category(self, key: str, *, include_media=True) -> Category:
        """Same as :meth:`get_category` but always requests new data from the server."""

        return self.create_category(_request_category_data(
            self.language,
            key,
            client=self.client_type,
            include_media=include_media
        ))

    def create_category(self, category_data: dict, *, parent_key: str | None = None) -> Category:
        """Create or update a cached :class:`Category` using the given data."""

        # Create a new category instance, this is cheap and verifies 'key' for us
        new_cat = Category(self, category_data, parent_key=parent_key)

        if new_cat.key in self._category_cache:
            old_cat = self._category_cache[new_cat.key]
            old_cat.data.update(new_cat.data)
            return old_cat
        else:
            self._category_cache[new_cat.key] = new_cat
            return new_cat

    # =============
    # Media methods
    # =============

    def request_media(self, key: str) -> Media:
        """Request a :class:`Media` object from the server.

        Unlike :meth:`get_category` this returns a new instance each time.
        """
        media_data = _request_media_data(language=self.language, key=key, client=self.client_type)
        return Media(self, media_data, parent=None)


class _ItemWithImage(_DictWrapper):
    def get_image(self, ratios: Iterable[str] = (), sizes: Iterable[str] = ()) -> str | None:
        """Return URL to first matching image.

        :param ratios: list of image ratios.
        :param sizes: list of image sizes.

        To select the desired image use ``RATIOS_*`` and ``SIZES_*`` found in the :mod:`~jwlib.media.const` module.
        Alternatively hand pick ratios and sizes from the :mod:`~jwlib.media.imagetable`.

        By default return the largest 16:9 image, or 1:1 if the item is tagged :const:`TAG_PREFER_SQUARE_IMAGES`.

        .. note::
            The client type affects what images are available.
        """

        if not ratios:
            ratios = RATIOS_SQUARE if TAG_PREFER_SQUARE_IMAGES in self.tags else RATIOS_16_9
        if not sizes:
            sizes = SIZES_FROM_LARGEST

        for ratio in ratios:
            for size in sizes:
                try:
                    return self.data['images'][ratio][size]
                except (TypeError, KeyError):
                    pass
        return None

    @property
    def tags(self) -> list[str]:
        """Return list of tags, see :mod:`~const`."""

        return self.data.setdefault('tags', [])


class Category(_ItemWithImage):
    """Information about a category and its subcategories and media.

    You wouldn't normally initialize this yourself.
    Use :meth:`Session.get_category` instead.
    """

    def __init__(self, session: Session, data: dict, parent_key: str | None = None):
        super().__init__(data)
        self.session = session

        # Initialize parent and subcategories and add them to cache
        # We do that right now because otherwise :meth:`get_category` might request a category from the server
        # even if we have the data right here, just because it wasn't added to cache

        if 'parentCategory' in self.data:
            parent_data = self.data.pop('parentCategory')
            if parent_data is None:
                self.data['_parentKey'] = ROOT_CATEGORY
            else:
                parent = self.session.create_category(parent_data)
                self.data['_parentKey'] = parent.key

        elif parent_key:
            # For subcategories and top-level categories the API doesn't provide a parentCategory,
            # since it's implied by the context. So we must provide it manually.
            self.data['_parentKey'] = parent_key

        if 'subcategories' in self.data:
            subcat_list = self.data['subcategories']
            subcat_keys = self.data.setdefault('_subcategoryKeys', [])
            for subcat_data in subcat_list:
                subcat = self.session.create_category(subcat_data, parent_key=self.key)
                subcat_keys.append(subcat.key)
            subcat_list.clear()

    def __repr__(self):
        return f"<{self.__class__.__name__} '{self.session.language}/{self.key}'>"

    def get_media(self) -> Iterator[Media]:
        """Iterate over :class:`Media` items.

        More items will be requested from the server on-the-fly, if needed.

        .. note::
            The iterator returns new instances of :class:`Media` on each run, so they cannot be compared by identity,
            but their underlying dictionary :attr:`Media.data` *can* because it remains the same.
        """
        return _MediaIterator(self)

    def get_parent(self) -> Category | None:
        """Return parent :class:`Category`.

        If the parent is unknown, a request will be sent to the server.
        """

        # Possible values of 'parentCategory' returned by the server:
        # dict - brief category info
        # None - this is a top-level Category, the parent is ROOT_CATEGORY
        # undefined - this came from 'parentCategory', we must request more info
        # undefined - this came from 'subcategories', thus the parent was obvious
        # undefined - this came from the top-level list of categories, thus the parent is implicitly ROOT_CATEGORY

        if self.key == ROOT_CATEGORY:
            return None

        if '_parentKey' not in self.data:
            # Note to self:
            # If we called :meth:`get_parent` on a bottom-level category, this will be a middle-level category
            # without parent info. We will need to request THIS middle-level category to get it's parent.
            # If this happens to be huge like VODProgramsEvents, include_media=False is a good idea.
            # We assume the user is not interested in the subcategories media if he calls :meth:`get_parent`.
            self.refresh(include_media=False)

        # Parent is prepared by __init__
        return self.session.get_category(self.data['_parentKey'])

    def get_subcategories(self, *, include_media=True) -> Iterator[Category]:
        """Iterate over subcategories.

        If subcategories are unknown, a request will be sent to the server.

        :param include_media: see :meth:`Session.get_category`
        """

        # Possible values of 'subcategories' returned by the server:
        # list[dict] - subcategory info
        # undefined - this category is not type 'container', there are no subcategories
        # undefined - this came from 'subcategories' or 'parentCategory', we must request more info
        # undefined - this was requested with detailed=0 (we don't do that here)

        if '_subcategoryKeys' not in self.data and self.type == CATEGORY_CONTAINER:
            self.refresh(include_media=include_media)

        # Subcategories are prepared by __init__
        for key in self.data.setdefault('_subcategoryKeys', []):
            yield self.session.get_category(key)

    @property
    def description(self) -> str:
        return self._get_string('description', '')

    @property
    def key(self) -> str:
        """Code name."""
        return self._get_string('key')

    @property
    def name(self) -> str:
        """Display name."""
        return self._get_string('name', '')

    def refresh(self, *, include_media=True):
        """Requests new category data

        Calling this on a category that has been removed from :attr:`Session.cached_categories` raises a RuntimeError.
        """
        if self not in self.session.cached_categories():
            raise RuntimeError("calling refresh() on a Category after it's been removed "
                               "from the Session is not supported")

        # Note to self: if we try to be smart and use :meth:`data.update` here directly,
        # we must call __init__ to setup the parent and subcategories again.
        # If this Category has been removed from the cache that would add back the parent
        # and subcategories to the cache, but not self. Things will get messy, just don't
        # let people delete categories from the cache!

        # Let the session handle updating - we don't need to duplicate that code here.
        self.session.request_category(self.key, include_media=include_media)

    @property
    def type(self) -> str:
        """Category type.

        ``container`` if it has subcategories or ``ondemand`` if it has media.
        """
        return self._get_string('type')


class Media(_ItemWithImage):
    """Information about a media item.

    You wouldn't normally initialize this yourself.
    Use :meth:`Session.get_media` or :meth:`Category.get_media` instead.
    """

    def __init__(self, session: Session, data: dict, parent: Category | None):
        super().__init__(data)
        self.session = session
        self.parent = parent

    def __repr__(self):
        return f"<{self.__class__.__name__} '{self.session.language}/{self.key}'>"

    @property
    def description(self) -> str:
        return self._get_string('description', '')

    @property
    def duration(self) -> int:
        """Duration in seconds."""
        return self._get_int('duration', 0)

    @property
    def duration_HHMM(self) -> str:
        """Duration as a string, like ``2:16``."""
        return self._get_string('durationFormattedHHMM', '0:00')

    @property
    def duration_min_sec(self) -> str:
        """Duration as a string, like ``2m 16s``."""
        return self._get_string('durationFormattedMinSec', '0s')

    def get_file(self, *, resolution=1080, subtitles=False) -> File:
        """Return the :class:`File` that best matches these criteria.

        :param resolution: max resolution
        :param subtitles: whether file should have subtitles (soft is preferred over hard)

        Raises IndexError if no file is found.

        .. note::
            New instances of :class:`File` are returned on each run, so they cannot be compared by identity,
            but their underlying dictionary :attr:`File.data` *can* because it remains the same.
        """
        return max(self.get_files(), key=lambda f: (
            f.resolution <= resolution,
            f.subtitled_soft == subtitles,
            f.subtitled_hard == subtitles,
            f.resolution
        ))

    def get_files(self) -> Iterator[File]:
        """Iterate over Files.

        .. note::
            New instances of :class:`File` are returned on each run, so they cannot be compared by identity,
            but their underlying dictionary :attr:`File.data` *can* because it remains the same.

        """
        for f in self.data.get('files', []):
            yield File(f)

    @property
    def guid(self) -> str:
        """24 character long hexadecimal identifier."""
        return self._get_string('guid')

    @property
    def key(self) -> str:
        """Code name, language agnostic.

        This is the key you use to request media info from the server.
        """
        return self._get_string('languageAgnosticNaturalKey')

    @property
    def key_with_language(self) -> str:
        """Code name, including language code.

        Looks similar to the filename, but not the same. Use case unknown.
        """
        return self._get_string('naturalKey')

    @property
    def languages(self) -> list[str]:
        """List of languages in which this item is available."""
        return self.data.get('availableLanguages', [])

    def get_primary_category(self, *, include_media=False) -> Category:
        """Return the primary parent category.

        If the category is not in the cache, a request will be sent to the server.

        :param include_media: see :meth:`Session.get_category`
        """
        return self.session.get_category(self.primary_category_key, include_media=include_media)

    @property
    def primary_category_key(self) -> str:
        """Code name of the primary parent category."""

        # On rare occasions have the server returned "" for this.
        # Using self.parent we can fix that, unless the user called :meth:`Session.get_media` in which case
        # we don't have a parent and it will crash either way

        return self._get_string('primaryCategory', self.parent.key if self.parent else None)

    @property
    def published(self) -> str:
        """Date when first published, formatted according to :const:`TIME_FORMAT`."""
        return self._get_string('firstPublished')[:19]

    @property
    def subtitle_url(self) -> str | None:
        """Convenience method to get first available subtitle URL."""
        try:
            return next(f.subtitle_url for f in self.get_files() if f.subtitled_soft)
        except StopIteration:
            return None

    @property
    def title(self) -> str:
        """Display name."""
        return self._get_string('title', '')

    @property
    def type(self) -> str:
        """Media type, like ``audio`` or ``video``."""
        return self._get_string('type')


class _MediaIterator(Iterator):
    """An iterator for :class:`Media` objects.

    More objects will be requested form the server, if needed, until the reported total is reached.
    """

    def __init__(self, category: Category):
        self.__index = -1
        self.__category = category

    def __next__(self):
        self.__index += 1

        # Possible values of 'media' returned by the server:
        # list[dict] - media info
        # empty list - requested with limit=0 or mediaLimit=0, will be handled through pagination
        # undefined - this category is not type 'ondemand', there is no media
        # undefined - this comes from the top-level list, we need to request more info (could be LatestVideos etc)

        if 'media' not in self.__category.data:
            if self.__category.type == CATEGORY_ONDEMAND:
                self.__category.refresh()
            else:
                raise StopIteration

        media_list = self.__category.data.setdefault('media', [])

        if self.__index >= len(media_list):

            # Stop if we reached the reported total number of items
            total = self.__category.data.get('_paginationTotalCount')
            if total is not None and self.__index >= total:
                raise StopIteration

            # In some cases (like subcategories) we don't know the total, but we know the pagination limit,
            # and if we are below it we can assume there are no more items
            limit = self.__category.data.get('_paginationLimit', default_pagination_limit)
            if total is None and self.__index < limit:
                raise StopIteration

            # Tags like 'LimitToFive' govern how long the list should be.
            # In the case of FeaturedSetTopBoxes the list is actually longer, but to get all items
            # you have to send multiple request, so we obey the tag when it appears.
            for limit, item_limit_tag in enumerate(TAGS_ITEM_LIMIT):
                if item_limit_tag in self.__category.tags and self.__index >= limit:
                    raise StopIteration

            # If we get here, there may be more media items available online
            # Send a request with a pagination offset
            followup_data = _request_category_data(
                self.__category.session.language,
                self.__category.key,
                client=self.__category.session.client_type,
                include_media=True,
                media_list_offset=self.__index
            )
            # Append media to our existing list
            media_list += followup_data.get('media', [])
            # Update the reported total
            self.__category.data['_paginationTotalCount'] = followup_data.get('_paginationTotalCount')

        try:
            media_data = media_list[self.__index]
        except IndexError:
            raise StopIteration from None

        return Media(self.__category.session, media_data, parent=self.__category)


class File(_DictWrapper):
    """Information about a downloadable file."""

    def __repr__(self):
        return f"<{self.__class__.__name__} '{self.filename}'>"

    @property
    def bitrate(self) -> float:
        """Bitrate in kb/s."""
        return self._get_float('bitRate', 0.0)

    @property
    def checksum(self) -> str | None:
        """MD5 checksum."""
        return self.data.get('checksum')

    @property
    def duration(self) -> int:
        """Duration in seconds."""
        return self._get_int('duration', 0)

    @property
    def filename(self):
        """File name of downloadable file."""
        return _os.path.basename(_urllib_parse.urlparse(self.url).path)

    @property
    def frame_rate(self) -> float:
        return self._get_float('frameRate', 0.0)

    @property
    def height(self) -> int:
        """Frame height."""
        return self.data.get('frameHeight', 0)

    @property
    def mimetype(self) -> str:
        return self._get_string('mimetype', '')

    @property
    def modified(self) -> str:
        """Modification time, formatted according to :const:`TIME_FORMAT`."""
        return self._get_string('modifiedDatetime')[:19]

    @property
    def print_references(self) -> list[str]:
        """List of code names that may be found in the literature."""
        return self.data.setdefault('printReferences', [])

    @property
    def resolution(self) -> int:
        """Video resolution.

        This is the human readable value and not the actual video height.
        Common values are 240, 360, 480, 720, 1080, or 0 if it's an audio file.
        """
        try:
            # Example label: '360p'
            label: str = self.data['label']
            if label[-1] == 'p':
                label = label[:-1]
            return int(label)
        except (KeyError, TypeError, ValueError):
            return 0

    @property
    def size(self) -> int:
        """File size in bytes."""
        return self._get_int('filesize', 0)

    @property
    def subtitle_checksum(self) -> str | None:
        """MD5 checksum for the subtitle file."""
        try:
            return self.data['subtitles']['checksum']
        except (KeyError, TypeError):
            return None

    @property
    def subtitle_date(self) -> str | None:
        """Subtitle modification time, formatted according to :const:`TIME_FORMAT`."""
        try:
            return self.data['subtitles']['modifiedDatetime'][:19]
        except (KeyError, TypeError):
            return None

    @property
    def subtitle_url(self) -> str | None:
        try:
            return self.data['subtitles']['url']
        except (KeyError, TypeError):
            return None

    @property
    def subtitled_hard(self) -> bool:
        """Has subtitles hardcoded in the video frame."""
        return self.data.get('subtitled', False)

    @property
    def subtitled_soft(self) -> bool:
        """Has external subtitles."""
        return bool(self.data.get('subtitles'))

    @property
    def url(self) -> str:
        """URL for downloading."""
        return self._get_string('progressiveDownloadURL')

    @property
    def width(self) -> int:
        """Frame width."""
        return self.data.get('frameWidth', 0)
