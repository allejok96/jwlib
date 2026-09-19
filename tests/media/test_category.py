from __future__ import annotations

from jwlib.media import const
from jwlib.media._category import Category, ROOT_PARENT, UNKNOWN_PARENT, update_category
from jwlib.media._media import Media


def make_category(**kwargs):
    kwargs.setdefault('session', object())
    kwargs.setdefault('key', 'SomeKey')
    kwargs.setdefault('type', const.CATEGORY_CONTAINER)
    return Category.create(**kwargs)


def test_category_create_wraps_media_dicts():
    session = object()
    cat = Category.create(
        key='k',
        type=const.CATEGORY_ONDEMAND,
        session=session, # type: ignore[arg-type]
        media=[{'key': 'pub-key', 'type': 'video'}]
    )
    assert len(cat.media) == 1
    assert isinstance(cat.media[0], Media)


def test_category_create_passes_through_media_instances():
    session = object()
    media = Media.create(session=session)  # type: ignore[arg-type]
    cat = Category.create(
        key='k',
        type=const.CATEGORY_ONDEMAND,
        session=session,  # type: ignore[arg-type]
        media=[media]
    )
    assert cat.media[0] is media


def test_category_create_defaults():
    cat = make_category()
    assert cat.description == ''
    assert cat.images == {}
    assert cat.media == []
    assert cat.media_count is None
    assert cat.name == ''
    assert cat.parent is UNKNOWN_PARENT
    assert cat.subcategories is None
    assert cat.tags == []


class FakeSession:
    def __init__(self, language='E'):
        self.language = language


def test_category_repr():
    cat = Category.create(
        key='SomeKey',
        type=const.CATEGORY_CONTAINER,
        session=FakeSession(),  # type: ignore[arg-type]
    )
    assert repr(cat) == "<Category 'E/SomeKey'>"


# ---------------
# update_category
# ---------------

def test_update_category_fills_missing_parent():
    cat = make_category(parent=UNKNOWN_PARENT)
    other = make_category(parent='ParentKey')
    update_category(cat, other)
    assert cat.parent == 'ParentKey'


def test_update_category_does_not_overwrite_known_parent():
    cat = make_category(parent='OriginalParent')
    other = make_category(parent='OtherParent')
    update_category(cat, other)
    assert cat.parent == 'OriginalParent'


def test_update_category_fills_missing_subcategories():
    cat = make_category(subcategories=None)
    other = make_category(subcategories=['Sub1', 'Sub2'])
    update_category(cat, other)
    assert cat.subcategories == ['Sub1', 'Sub2']


def test_update_category_does_not_overwrite_known_subcategories():
    cat = make_category(subcategories=['Original'])
    other = make_category(subcategories=['Other'])
    update_category(cat, other)
    assert cat.subcategories == ['Original']


def test_update_category_fills_missing_media_count():
    cat = make_category(media_count=None)
    other = make_category(media_count=5)
    update_category(cat, other)
    assert cat.media_count == 5


def test_update_category_does_not_overwrite_known_media_count():
    cat = make_category(media_count=3)
    other = make_category(media_count=5)
    update_category(cat, other)
    assert cat.media_count == 3


def test_update_category_fills_media_when_empty():
    session = object()
    other_media = [Media.create(session=session, key='a'),  # type: ignore[arg-type]
                   Media.create(session=session, key='b')]  # type: ignore[arg-type]
    cat = make_category(media=[])
    other = make_category(media=other_media)
    update_category(cat, other)
    assert cat.media == other_media


def test_update_category_keeps_existing_media_even_if_other_has_more():
    session = object()
    existing = [Media.create(session=session, key='a')]  # type: ignore[arg-type]
    other_media = [Media.create(session=session, key='a'),  # type: ignore[arg-type]
                   Media.create(session=session, key='b')]  # type: ignore[arg-type]
    cat = make_category(media=existing)
    other = make_category(media=other_media)
    update_category(cat, other)
    # cat.media is non-empty, so it wins even though other has more items
    assert cat.media == existing


def test_update_category_keeps_existing_media_when_other_is_empty():
    session = object()
    existing = [Media.create(session=session, key='a'),  # type: ignore[arg-type]
                Media.create(session=session, key='b')]  # type: ignore[arg-type]
    cat = make_category(media=existing)
    other = make_category(media=[])
    update_category(cat, other)
    assert cat.media == existing


def test_update_category_root_parent_is_not_overwritten():
    cat = make_category(parent=ROOT_PARENT)
    other = make_category(parent='SomeParent')
    update_category(cat, other)
    assert cat.parent is ROOT_PARENT
