import pytest

from jwlib.media import const
from jwlib.media._api_requests import get_inferred_media_limit, set_inferred_media_limit
from jwlib.media._category import Category
from jwlib.media._media import Media

from .session_double import FakeSession


def make_media(n: int, session=None):
    session = session or object()
    return [Media.create(
        session=session,  # type: ignore[arg-type]
        key=f'm{i}'
    ) for i in range(n)]


def make_category(session=None, **kwargs):
    session = session or FakeSession()
    kwargs.setdefault('key', 'Bottom')
    kwargs.setdefault('type', const.CATEGORY_ONDEMAND)
    kwargs.setdefault('session', session)
    return Category.create(**kwargs)


# ----------------
# _has_all_media()
# ----------------

def test_has_all_media_true_for_container_categories():
    cat = make_category(type=const.CATEGORY_CONTAINER, media=make_media(0), media_count=None)
    assert cat._has_all_media() is True


def test_has_all_media_true_when_media_count_reached():
    cat = make_category(media=make_media(3), media_count=3)
    assert cat._has_all_media() is True


def test_has_all_media_false_when_below_media_count():
    cat = make_category(media=make_media(2), media_count=3)
    assert cat._has_all_media() is False


def test_has_all_media_false_when_empty_and_media_count_unknown():
    cat = make_category(media=make_media(0), media_count=None)
    assert cat._has_all_media() is False


def test_has_all_media_true_when_nonempty_below_inferred_limit_and_count_unknown():
    cat = make_category(media=make_media(5), media_count=None)
    assert cat._has_all_media() is True


def test_has_all_media_false_when_at_inferred_limit_and_count_unknown_and_no_tags():
    limit = get_inferred_media_limit()
    cat = make_category(media=make_media(limit), media_count=None)
    assert cat._has_all_media() is False


def test_has_all_media_respects_inferred_limit_setting():
    set_inferred_media_limit(2)
    cat = make_category(media=make_media(2), media_count=None)
    assert cat._has_all_media() is False
    cat = make_category(media=make_media(1), media_count=None)
    assert cat._has_all_media() is True


@pytest.mark.parametrize('tag, limit', [
    ('LimitToZero', 0),
    ('LimitToOne', 1),
    ('LimitToFive', 5),
    ('LimitToTen', 10),
])
def test_has_all_media_tag_limit_overrides_media_count(tag, limit):
    # media_count is a large real total from the server, but the tag caps the list
    cat = make_category(media=make_media(limit), media_count=1000, tags=[tag])
    assert cat._has_all_media() is True


@pytest.mark.parametrize('tag, limit', [
    ('LimitToOne', 1),
    ('LimitToFive', 5),
])
def test_has_all_media_tag_limit_not_yet_reached(tag, limit):
    cat = make_category(media=make_media(limit - 1), media_count=1000, tags=[tag])
    assert cat._has_all_media() is False


def test_has_all_media_false_when_no_tag_matches_and_over_inferred_limit():
    limit = get_inferred_media_limit()
    cat = make_category(media=make_media(limit), media_count=None, tags=['SomeUnrelatedTag'])
    assert cat._has_all_media() is False


# -----------------------------------
# get_media() - pagination/refetching
# -----------------------------------

def test_get_media_no_request_for_container_category():
    session = FakeSession()
    cat = make_category(session, type=const.CATEGORY_CONTAINER, media=[])
    assert cat.get_media() == []
    assert session.request_category_media_calls == []


def test_get_media_single_page():
    class Session(FakeSession):
        def request_category_media(self, key, *, offset):
            self.request_category_media_calls.append((key, offset))
            return chunk, 3

    session = Session()
    chunk = make_media(3, session)
    cat = make_category(session, media=[], media_count=None)

    result = cat.get_media()

    assert result == chunk
    assert session.request_category_media_calls == [('Bottom', 0)]
    assert cat.media_count == 3


def test_get_media_multiple_pages_uses_growing_offset():
    class Session(FakeSession):
        def request_category_media(self, key, *, offset):
            self.request_category_media_calls.append((key, offset))
            return pages.pop(0), 5

    session = Session()
    pages = [make_media(2, session), make_media(2, session), make_media(1, session)]
    cat = make_category(session, media=[], media_count=None)

    result = cat.get_media()

    assert len(result) == 5
    assert session.request_category_media_calls == [('Bottom', 0), ('Bottom', 2), ('Bottom', 4)]
    assert cat.media_count == 5


def test_get_media_stops_early_on_empty_chunk_even_if_count_says_more():
    # Returns one chunk, then claims a much larger total but delivers nothing more
    class Session(FakeSession):
        def request_category_media(self, key, *, offset):
            self.request_category_media_calls.append((key, offset))
            if offset == 0:
                return first_chunk, 100
            return [], 100

    session = Session()
    first_chunk = make_media(2, session)
    cat = make_category(session, media=[], media_count=None)

    result = cat.get_media()

    assert len(result) == 2
    assert [offset for _, offset in session.request_category_media_calls] == [0, 2]
    # media_count is forced to reflect reality, not the server's claimed total
    assert cat.media_count == 2


def test_get_media_does_not_refetch_once_fully_loaded():
    session = FakeSession()
    cat = make_category(session, media=make_media(3, session), media_count=3)

    first = cat.get_media()
    second = cat.get_media()

    assert first == second
    assert session.request_category_media_calls == []


def test_get_media_gives_up_after_20_requests():
    # Always returns one more item and claims a huge total, so
    # _has_all_media() would never naturally return True.
    class Session(FakeSession):
        def request_category_media(self, key, *, offset):
            self.request_category_media_calls.append((key, offset))
            return make_media(1, self), 10_000

    session = Session()
    cat = make_category(session, media=[], media_count=None)

    result = cat.get_media()

    assert len(result) == 20
    assert len(session.request_category_media_calls) == 20
    # The safety valve forces media_count to match what was actually collected
    assert cat.media_count == 20
