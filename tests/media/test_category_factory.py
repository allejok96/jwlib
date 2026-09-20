from jwlib.media import const
from jwlib.media._category_factory import create_basic, create_partial, create_root


def test_create_basic_full():
    session = object()
    cat = create_basic(
        {
            'description': 'a description',
            'images': {'wss': {'lg': 'https://example.org/image.jpg'}},
            'key': 'SomeKey',
            'name': 'Some Name',
            'tags': ['SomeTag'],
            'type': const.CATEGORY_CONTAINER,
        },
        parent='ParentKey',
        session=session,  # type: ignore[arg-type]
    )

    assert cat.description == 'a description'
    assert cat.images == {'wss': {'lg': 'https://example.org/image.jpg'}}
    assert cat.key == 'SomeKey'
    assert cat.media == []
    assert cat.media_count is None
    assert cat.name == 'Some Name'
    assert cat.parent == 'ParentKey'
    assert cat.session is session
    assert cat.subcategories is None
    assert cat.tags == ['SomeTag']
    assert cat.type == const.CATEGORY_CONTAINER


def test_create_basic_minimal_defaults():
    session = object()
    cat = create_basic(
        {'key': 'SomeKey', 'type': const.CATEGORY_ONDEMAND},  # type: ignore[typeddict-item]
        parent=None,
        session=session,  # type: ignore[arg-type]
    )

    assert cat.description == ''
    assert cat.images == {}
    assert cat.name == ''
    assert cat.parent is None
    assert cat.tags == []


def test_create_partial_with_media_and_string_parent():
    session = object()

    cat = create_partial(
        {  # type: ignore[typeddict-item]
            'key': 'SomeKey',
            'type': const.CATEGORY_ONDEMAND,
            'media': [{  # type: ignore[typeddict-item]
                'languageAgnosticNaturalKey': 'pub-key',
                'naturalKey': 'pub-key-lang',
                'type': 'video',
            }],
        },
        media_count=1,
        parent='ParentKey',
        session=session  # type: ignore[arg-type]
    )

    assert len(cat.media) == 1
    assert cat.media[0].key == 'pub-key'
    # Media parent should be inferred from the category's own parent, since
    # it was fetched as part of "ParentKey"'s subcategory listing
    assert cat.media[0].parent == 'ParentKey'
    assert cat.media_count == 1


def test_create_partial_media_parent_is_none_for_non_string_parent():
    session = object()
    cat = create_partial(
        {  # type: ignore[typeddict-item]
            'key': 'SomeKey',
            'type': const.CATEGORY_ONDEMAND,
            'media': [{  # type: ignore[typeddict-item]
                'languageAgnosticNaturalKey': 'pub-key',
                'naturalKey': 'pub-key-lang',
                'type': 'video',
            }],
        },
        media_count=1,
        parent=None,
        session=session,  # type: ignore[arg-type]
    )

    assert cat.media[0].parent is None


def test_create_partial_no_media_key():
    session = object()
    cat = create_partial(
        {'key': 'SomeKey', 'type': const.CATEGORY_CONTAINER},  # type: ignore[typeddict-item]
        media_count=None,
        parent='ParentKey',
        session=session,  # type: ignore[arg-type]
    )

    assert cat.media == []
    assert cat.media_count is None


def test_create_root():
    session = object()
    root = create_root(session=session)  # type: ignore[arg-type]

    assert root.key == const.ROOT_CATEGORY
    assert root.media == []
    assert root.media_count == 0
    assert root.parent is None
    assert root.session is session
    assert root.subcategories is None
    assert root.type == const.CATEGORY_CONTAINER
