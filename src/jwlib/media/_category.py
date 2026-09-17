from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Union, Optional, TYPE_CHECKING, Iterable

from . import const
from ._api_responses import get_inferred_media_limit
from ._image_item import ItemWithImages
from ._iterator_compat import IteratorCompatibleList
from ._media import Media
from .._deprecated import deprecated

if TYPE_CHECKING:
    from ._session_base import BaseSession

# For Category.parent
ParentType = Union[str, bool]
UNKNOWN_PARENT = False
ROOT_PARENT = True


@dataclass
class Category(ItemWithImages):
    """Information about a category and its subcategories and media.

    Do not initialize directly, since arguments may be subject to change.
    Use :meth:`Session.get_category` or :meth:`create` instead.
    """

    description: str

    key: str
    """Code name."""

    media: list[Media]
    """List of media items.

    Lazy loaded - use :meth:`get_media` instead.
    """

    media_count: Optional[int]
    """Total number of available media items.

    Used by :meth:`get_media` for lazy-loading.
    """

    name: str
    """Display name."""

    parent: Union[str, bool]
    """Parent category key.

    Lazy loaded - use :meth:`get_parent` instead.
    """

    session: BaseSession
    """Session, used to fetch subcategories, etc."""

    subcategories: Optional[list[str]]
    """List of subcategory keys.

    Lazy loaded - use :meth:`get_subcategories` instead.
    """

    type: const.CategoryType
    """Category type.

    - ``container`` if it has subcategories
    - ``ondemand`` if it has media
    """

    @staticmethod
    def create(*,
               description='',
               images: Optional[dict] = None,
               key: str,
               media: Optional[Iterable[Union[Media, dict]]] = None,
               media_count: Optional[int] = None,
               name='',
               parent: Union[str, bool] = UNKNOWN_PARENT,
               session: BaseSession,
               subcategories: Optional[Iterable[str]] = None,
               tags: Optional[Iterable[str]] = None,
               type: const.CategoryType
               ) -> Category:
        """Create a new category instance."""
        return Category(
            description=description,
            images=images if images is not None else {},
            key=key,
            media=[m if isinstance(m, Media) else Media.create(**m) for m in media or []],
            media_count=media_count,
            name=name,
            parent=parent,
            session=session,
            subcategories=list(subcategories) if subcategories is not None else [],
            tags=list(tags) if tags is not None else [],
            type=type,
        )

    def __repr__(self):
        try:
            return f"<{self.__class__.__name__} '{self.session.language}/{self.key}'>"
        except Exception:
            return super().__repr__()

    @property
    @deprecated("Use dataclass.asdict() instead.")
    def data(self) -> dict:
        return asdict(self)

    def get_media(self) -> list[Media]:
        """Return list of :class:`Media` items.

        If :attr:`media` is unset or truncated, it will be requested from the server.
        """
        if not isinstance(self.media, IteratorCompatibleList):
            self.media = IteratorCompatibleList(self.media)

        # If we have to do more than 20 requests, something is wrong
        for i in range(20):
            if self._has_all_media():
                break

            chunk, total = self.session.request_category_media(self.key, offset=len(self.media))
            self.media.extend(chunk)
            self.media_count = total

            # Stop when there is nothing more to get
            if len(chunk) == 0:
                break

        # Make sure this never runs again
        self.media_count = len(self.media)
        return self.media

    def get_parent(self) -> Optional[Category]:
        """Return parent :class:`Category`.

        If :attr:`parent` is unset, it will be requested from the server.
        """
        if self.parent is UNKNOWN_PARENT:
            # If we are traversing up, we assume we won't be traversing down again,
            # so skip media to save some time
            self._refresh(include_media=False)
        if self.parent is ROOT_PARENT:
            return None
        elif isinstance(self.parent, str):
            return self.session.get_category(self.parent)
        else:
            raise RuntimeError("Failed to fetch parent category")

    def get_subcategories(self, *, include_media=True) -> list[Category]:
        """Return list of subcategories.

        If :attr:`subcategories` is unset, it will be requested from the server.

        :param include_media: see :meth:`Session.get_category`

        .. note::
            The returned list is temporary, appending to or removing from it has no effect on the Category.
            To edit the Category's subcategory list, use :attr:`subcategories`.
        """
        if self.subcategories is None:
            if self.type == const.CATEGORY_CONTAINER:
                self._refresh(include_media=include_media)
            else:
                self.subcategories = []
        if self.subcategories is not None:
            return IteratorCompatibleList(self.session.get_category(key) for key in self.subcategories)
        else:
            raise RuntimeError("Failed to fetch subcategories")

    @deprecated("To truly refresh a Category, delete if from the session cache.")
    def refresh(self, *, include_media=True) -> None:
        self._refresh(include_media=include_media)

    # -------
    # Private
    # -------

    def _has_all_media(self):
        # Non-on-demand categories have no media
        if self.type != const.CATEGORY_ONDEMAND:
            return True

        # We reached the expected amount
        if self.media_count is not None and len(self.media) >= self.media_count:
            return True

        # We got the media from a subcategory, and it hasn't reached the observed limit
        # of how many media items a subcategory can have, so we can assume it's all.
        # (If we used include_media=False, it would be 0, thus continuing.)
        if self.media_count is None and 0 < len(self.media) < get_inferred_media_limit():
            return True

        # Tags like 'LimitToFive' govern how long the list should be.
        # In the case of FeaturedSetTopBoxes the list is actually longer, but to get all items
        # you have to send multiple request, so we obey the tag when it appears.
        for limit, tag in enumerate(const.TAGS_ITEM_LIMIT):
            if tag in self.tags and len(self.media) >= limit:
                return True

        return False

    def _refresh(self, *, include_media=True) -> None:
        new = self.session.request_category(self.key, include_media=include_media)
        update_category(self, new)


def update_category(cat: Category, other: Category) -> None:
    """Set the missing values in one category using another category"""

    if len(cat.media) < len(other.media):
        cat.media = other.media
    if cat.media_count is None:
        cat.media_count = other.media_count
    if cat.parent is UNKNOWN_PARENT:
        cat.parent = other.parent
    if cat.subcategories is None:
        cat.subcategories = other.subcategories
