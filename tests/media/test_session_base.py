import json

from jwlib.media import const
from jwlib.media._category import Category
from jwlib.media._media import Media
from jwlib.media._session_impl import Session


def test_dump_categories_excludes_session_at_every_level():
    session = Session()
    media = Media.create(session=session, key='SomeMedia', files=[{'url': 'https://example.org/video.mp4'}])
    cat = Category.create(key='SomeKey', type=const.CATEGORY_ONDEMAND, session=session, media=[media])
    session.categories['SomeKey'] = cat

    dump = session.dump_categories()

    assert len(dump) == 1
    assert 'session' not in dump[0]
    assert 'session' not in dump[0]['media'][0]
    # Would raise TypeError if a Session (not JSON serializable) leaked into the dump
    json.dumps(dump)


def test_load_categories_reconstructs_full_object_graph():
    session = Session()
    media = Media.create(
        session=session,
        key='SomeMedia',
        title='A title',
        files=[{
            'url': 'https://example.org/video.mp4',
            'resolution': 720,
            'subtitles': {'url': 'https://example.org/sub.vtt', 'checksum': 'abc'},
        }],
    )
    original = Category.create(
        key='SomeKey',
        type=const.CATEGORY_ONDEMAND,
        session=session,
        name='Some Name',
        parent='ParentKey',
        media=[media],
        media_count=1,
    )
    session.categories['SomeKey'] = original

    dump = session.dump_categories()
    serialized = json.loads(json.dumps(dump))

    new_session = Session()
    new_session.load_categories(serialized)

    loaded = new_session.categories['SomeKey']
    assert loaded is not original
    assert loaded.key == 'SomeKey'
    assert loaded.name == 'Some Name'
    assert loaded.parent == 'ParentKey'
    assert loaded.media_count == 1
    assert loaded.session is new_session

    loaded_media = loaded.media[0]
    assert loaded_media.key == 'SomeMedia'
    assert loaded_media.title == 'A title'
    assert loaded_media.session is new_session

    loaded_file = loaded_media.files[0]
    assert loaded_file.url == 'https://example.org/video.mp4'
    assert loaded_file.resolution == 720
    assert loaded_file.subtitles is not None
    assert loaded_file.subtitles.checksum == 'abc'


def test_load_categories_keeps_multiple_entries_indexed_by_key():
    session = Session()
    session.categories['A'] = Category.create(key='A', type=const.CATEGORY_CONTAINER, session=session)
    session.categories['B'] = Category.create(key='B', type=const.CATEGORY_ONDEMAND, session=session)

    dump = session.dump_categories()

    new_session = Session()
    new_session.load_categories(dump)

    assert set(new_session.categories.keys()) == {'A', 'B'}
