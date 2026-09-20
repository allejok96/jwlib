import pytest

from jwlib.media import const
from jwlib.media._session_impl import Session


def basic_dict(key, **overrides):
    d = {'description': '', 'images': {}, 'key': key, 'name': key, 'tags': [], 'type': const.CATEGORY_CONTAINER}
    d.update(overrides)
    return d


def partial_dict(key, **overrides):
    d = basic_dict(key)
    d['media'] = []
    d.update(overrides)
    return d


# ----------
# _add_basic
# ----------

def test_add_basic_adds_new_category():
    session = Session()
    cat = session._add_basic(basic_dict('K', name='Name'), parent='Parent')
    assert session.categories['K'] is cat
    assert cat.name == 'Name'
    assert cat.parent == 'Parent'
    assert cat.session is session


def test_add_basic_merging_fills_parent_but_keeps_existing_identifying_fields():
    session = Session()
    original = session._add_basic(basic_dict('K', name='Original Name'), parent=None)
    updated = session._add_basic(basic_dict('K', name='New Name'), parent='Parent')

    # update_category() only merges parent/subcategories/media/media_count,
    # so the originally cached name wins even though "New Name" was fetched later
    assert updated.name == 'Original Name'
    assert updated.parent == 'Parent'
    # Merging returns/updates the same cached instance, not a new one
    assert session.categories['K'] is original is updated


def test_add_basic_does_not_overwrite_already_known_parent():
    session = Session()
    session._add_basic(basic_dict('K'), parent='OriginalParent')
    updated = session._add_basic(basic_dict('K'), parent='OtherParent')
    assert updated.parent == 'OriginalParent'


# ---------
# _add_root
# ---------

def test_add_root_is_idempotent():
    session = Session()
    first = session._add_root()
    second = session._add_root()
    assert first is second
    assert session.categories[const.ROOT_CATEGORY] is first


# -------------
# _add_complete
# -------------

def test_add_complete_top_level_category_gets_root_as_parent():
    session = Session()
    d = partial_dict('Top', parentCategory=None, subcategories=[])
    cat = session._add_complete(d, media_count=0)
    assert cat.parent == const.ROOT_CATEGORY


def test_add_complete_registers_parent_and_subcategories():
    session = Session()
    d = partial_dict(
        'Middle',
        parentCategory=basic_dict('Top'),
        subcategories=[partial_dict('Bottom', media=[{
            'languageAgnosticNaturalKey': 'pub-key',
            'naturalKey': 'pub-key-lang',
            'type': 'video',
        }])],
    )

    cat = session._add_complete(d, media_count=5)

    assert cat.key == 'Middle'
    assert cat.parent == 'Top'
    assert cat.media_count == 5
    assert cat.subcategories == ['Bottom']

    # The parent was registered too, with an as-yet-unknown parent of its own
    assert 'Top' in session.categories
    assert session.categories['Top'].parent is None

    # The subcategory was registered with media, and its parent set to "Middle"
    bottom = session.categories['Bottom']
    assert bottom.parent == 'Middle'
    assert len(bottom.media) == 1
    assert bottom.media[0].parent == 'Middle'


def test_add_complete_merges_into_previously_partial_category():
    session = Session()
    # First seen as a bare parent reference (e.g. from another category's "parentCategory")
    session._add_basic(basic_dict('Middle'), parent=None)
    assert session.categories['Middle'].subcategories is None

    d = partial_dict('Middle', parentCategory=basic_dict('Top'), subcategories=[partial_dict('Bottom')])
    cat = session._add_complete(d, media_count=0)

    # Same cached instance, now filled in
    assert session.categories['Middle'] is cat
    assert cat.subcategories == ['Bottom']
    assert cat.parent == 'Top'


# -------------------------------------
# request_category() - root two-step fetch
# -------------------------------------

def test_request_category_root_first_call_does_not_fetch_top_level(monkeypatch):
    session = Session()

    def fail_fetch(*args, **kwargs):
        raise AssertionError('fetch_top_level should not be called on the first request for root')

    monkeypatch.setattr('jwlib.media._session_impl.fetch_top_level', fail_fetch)

    root = session.request_category(const.ROOT_CATEGORY)

    assert root.key == const.ROOT_CATEGORY
    assert root.subcategories is None


def test_request_category_root_second_call_fetches_and_populates_subcategories(monkeypatch):
    session = Session()
    session.request_category(const.ROOT_CATEGORY)  # first call: just creates the placeholder

    monkeypatch.setattr(
        'jwlib.media._session_impl.fetch_top_level',
        lambda language, client: [basic_dict('Top1'), basic_dict('Top2')],
    )

    root = session.request_category(const.ROOT_CATEGORY)

    assert root.subcategories == ['Top1', 'Top2']
    assert session.categories['Top1'].parent == const.ROOT_CATEGORY
    assert session.categories['Top2'].parent == const.ROOT_CATEGORY


def test_get_category_for_root_triggers_no_request_until_subcategories_are_needed(monkeypatch):
    """Mirrors the integration test's expectation that a bare get_category() is free."""
    session = Session()

    def fail_fetch(*args, **kwargs):
        raise AssertionError('fetch_top_level should not be called yet')

    monkeypatch.setattr('jwlib.media._session_impl.fetch_top_level', fail_fetch)

    root = session.get_category()  # default key is ROOT_CATEGORY
    assert root.key == const.ROOT_CATEGORY

    monkeypatch.setattr(
        'jwlib.media._session_impl.fetch_top_level',
        lambda language, client: [basic_dict('Top1')],
    )
    assert root.get_subcategories(include_media=False)[0].key == 'Top1'
