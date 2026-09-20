from jwlib.media import const
from jwlib.media._category import Category

from .session_double import FakeSession


def make_category(session, **kwargs):
    kwargs.setdefault('key', 'Middle')
    kwargs.setdefault('type', const.CATEGORY_CONTAINER)
    kwargs.setdefault('session', session)
    return Category.create(**kwargs)


def test_returns_cached_subcategories_without_refresh():
    session = FakeSession()
    sub_a = make_category(session, key='A')
    sub_b = make_category(session, key='B')
    session.categories['A'] = sub_a
    session.categories['B'] = sub_b
    cat = make_category(session, subcategories=['A', 'B'])

    result = cat.get_subcategories()

    assert result == [sub_a, sub_b]
    assert session.request_category_calls == []


def test_ondemand_category_with_unset_subcategories_gets_empty_list_without_refresh():
    session = FakeSession()
    cat = make_category(session, type=const.CATEGORY_ONDEMAND)
    cat.subcategories = None

    assert cat.get_subcategories() == []
    assert session.request_category_calls == []
    # The Category itself should now remember it has no subcategories
    assert cat.subcategories == []


def test_container_category_with_unset_subcategories_refreshes():
    class Session(FakeSession):
        def request_category(self, key, *, include_media=True):
            self.request_category_calls.append((key, include_media))
            return make_category(self, key=key, subcategories=['A'])

    session = Session()
    sub_a = make_category(session, key='A')
    session.categories['A'] = sub_a
    cat = make_category(session, key='Middle')
    cat.subcategories = None

    result = cat.get_subcategories(include_media=False)

    assert result == [sub_a]
    assert session.request_category_calls == [('Middle', False)]
    assert cat.subcategories == ['A']


def test_include_media_defaults_to_true_when_refreshing():
    class Session(FakeSession):
        def request_category(self, key, *, include_media=True):
            self.request_category_calls.append((key, include_media))
            return make_category(self, key=key, subcategories=[])

    session = Session()
    cat = make_category(session)
    cat.subcategories = None

    cat.get_subcategories()

    assert session.request_category_calls == [('Middle', True)]


def test_returned_list_is_a_disconnected_copy():
    session = FakeSession()
    sub_a = make_category(session, key='A')
    session.categories['A'] = sub_a
    cat = make_category(session, subcategories=['A'])

    result = cat.get_subcategories()
    result.append(make_category(session, key='Extra'))

    assert cat.subcategories == ['A']
