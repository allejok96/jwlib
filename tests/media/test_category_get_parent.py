import pytest

from jwlib.media import const
from jwlib.media._category import Category

from .session_double import FakeSession


def make_category(session, **kwargs):
    kwargs.setdefault('key', 'Bottom')
    kwargs.setdefault('type', const.CATEGORY_ONDEMAND)
    kwargs.setdefault('session', session)
    return Category.create(**kwargs)


def test_get_parent_uses_cached_string_parent_without_refresh():
    session = FakeSession()
    parent_cat = make_category(session, key='Middle')
    session.categories['Middle'] = parent_cat
    cat = make_category(session, parent='Middle')

    assert cat.get_parent() is parent_cat
    # No refresh was needed since the parent key was already known
    assert session.request_category_calls == []


def test_get_parent_returns_none_for_root():
    session = FakeSession()
    cat = make_category(session, parent=None, key=const.ROOT_CATEGORY)
    assert cat.get_parent() is None
    assert session.request_category_calls == []


def test_get_parent_refreshes_when_unknown_then_fetches_parent_without_media():
    class Session(FakeSession):
        """Reports, when refreshed, that the requested category's parent is 'Middle'."""

        def request_category(self, key, *, include_media=True):
            self.request_category_calls.append((key, include_media))
            return make_category(self, key=key, parent='Middle')

    session = Session()
    parent_cat = make_category(session, key='Middle')
    session.categories['Middle'] = parent_cat
    cat = make_category(session, parent=None)

    assert cat.get_parent() is parent_cat
    # get_parent() should skip fetching media when refreshing, since we're
    # traversing up and assume we won't need it
    assert session.request_category_calls == [('Bottom', False)]


def test_get_parent_raises_if_still_unknown_after_refresh():
    class Session(FakeSession):
        """Refreshing never actually reveals a parent, mimicking bad server data."""

        def request_category(self, key, *, include_media=True):
            self.request_category_calls.append((key, include_media))
            return make_category(self, key=key, parent=None)

    session = Session()
    cat = make_category(session, parent=None)

    with pytest.raises(RuntimeError):
        cat.get_parent()
