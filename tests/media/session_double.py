"""Test double for BaseSession.

Used by tests that exercise Category/Media lazy-loading logic (get_parent,
get_subcategories, get_media, get_primary_category) without any network access.

Subclass `FakeSession` per test and override `request_category()` /
`request_category_media()` to supply exactly the behavior that test needs,
appending to `self.request_category_calls` / `self.request_category_media_calls`
as you go so assertions on call args keep working.

To stub `get_category()`, prefer populating `self.categories` directly instead
of overriding the method - that's the real cache `BaseSession.get_category()`
already reads from, so it's the more realistic double.

Methods that are not overridden fail loudly instead of silently returning a
mock, mirroring the "unexpected request" spirit of the integration tests'
`rex` fixture.
"""
from __future__ import annotations

from typing import List, Tuple

from jwlib.media._category import Category
from jwlib.media._media import Media
from jwlib.media._session_base import BaseSession


class FakeSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.request_category_calls: List[tuple] = []
        self.request_category_media_calls: List[tuple] = []

    def get_languages(self):
        raise NotImplementedError('not needed by these tests')

    def get_media(self, key):
        raise NotImplementedError('not needed by these tests')

    def get_translations(self):
        raise NotImplementedError('not needed by these tests')

    def request_category(self, key: str, *, include_media=True) -> Category:
        raise AssertionError(f'Unexpected call: request_category({key!r}, include_media={include_media!r})')

    def request_category_media(self, key: str, *, offset: int) -> Tuple[List[Media], int]:
        raise AssertionError(f'Unexpected call: request_category_media({key!r}, offset={offset!r})')
