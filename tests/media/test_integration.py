import io
import json
import logging
import sys
import time
from contextlib import contextmanager
from typing import List, Optional

import pytest

import jwlib.media as jw
import jwlib.media.imagetable


class LogHook(logging.Handler):
    """Hooks into logger and assert that certain strings are logged"""

    def __init__(self, *, prefix: str):
        super().__init__()
        self.enabled = True
        self.prefix = prefix
        self.expectations: List[str] = []

    @contextmanager
    def expect(self, *, cat='', client='firetv', include_media=True, mediaid='', lang='E', offset=0,
               raw: Optional[List[str]] = None):
        """Use in a with statement to add an expected string"""

        if cat or mediaid:
            if cat == ROOT:
                path = f'categories/{lang}'
            elif cat:
                path = f'categories/{lang}/{cat}'
            elif mediaid:
                path = f'media-items/{lang}/{mediaid}'
            else:
                raise RuntimeError
            args = []
            if client:
                args.append(f'clientType={client}')
            if cat and cat != ROOT:
                args.append('detailed=1')
            if not include_media:
                args.append('limit=0&mediaLimit=0')
            if offset:
                args.append('offset=' + str(offset))
            if args:
                path += '?' + '&'.join(args)
            self.expectations.append(path)

        elif raw:
            self.expectations.extend(raw)

        yield

        assert not self.expectations, f'Expected: {self.expectations}, got nothing.'

    def emit(self, record: logging.LogRecord):
        if self.enabled and record.msg.startswith(self.prefix):
            msg = record.msg[len(self.prefix):]
            assert self.expectations, f'Unexpected: {msg}'
            expected = self.expectations.pop()
            assert msg == expected, f'Expected: {expected}, got: {msg}'


# Auto-use so all unexpected requests get caught
@pytest.fixture(autouse=True)
def rex(caplog):
    """Request Expectation"""

    # Set log level through pytest's caplog
    caplog.set_level(logging.DEBUG, 'jwlib')

    # Grep for log entries starting like this
    hook = LogHook(prefix="opening: https://b.jw-cdn.org/apis/mediator/v1/")
    logger = logging.getLogger('jwlib')
    logger.addHandler(hook)

    # Return the hook so the test can call hook.expect() to add expectations
    yield hook

    # Cleanup the logger
    logger.removeHandler(hook)


ROOT = jw.ROOT_CATEGORY
TOP_LEVEL = 'VideoOnDemand'
MIDDLE_LEVEL = 'VODStudio'
BOTTOM_LEVEL = 'StudioFeatured'
LATEST_VIDEOS = 'LatestVideos'


def test_get_parent(rex):
    with rex.expect(cat=BOTTOM_LEVEL):
        bottom = jw.Session().get_category(BOTTOM_LEVEL)

    # Parent should be included when getting category
    middle = bottom.get_parent()
    assert middle is not None

    # Needs to fetch middle level to know its parent
    with rex.expect(cat=MIDDLE_LEVEL, include_media=False):
        top = middle.get_parent()
    assert top is not None

    # Needs to fetch top-level to know its parent
    with rex.expect(cat=TOP_LEVEL, include_media=False):
        root = top.get_parent()

    # Parent of top-level is virtual root
    assert root is not None

    # Parent of root is always None
    assert root.get_parent() is None


def test_get_media(rex):
    with rex.expect(cat=BOTTOM_LEVEL):
        bottom = jw.Session().get_category(BOTTOM_LEVEL)

    # Bottom categories should include media
    assert all(bottom.get_media())

    # Container categories shouldn't contain media, and not try to request it either
    parent = bottom.get_parent()
    assert parent is not None
    assert not any(parent.get_media())


def test_get_media_toplevel(rex):
    # Root has no media
    root = jw.Session().get_category()
    assert not any(root.get_media())

    # The list of top-level categories doesn't include media
    with rex.expect(cat=ROOT):
        top_level_list = list(root.get_subcategories())

    with rex.expect(cat=LATEST_VIDEOS):
        for subcategory in top_level_list:
            if subcategory.key == LATEST_VIDEOS:
                assert all(subcategory.get_media())


def test_hidden_categories(rex):
    with rex.expect(cat=ROOT):
        top_level_list = list(jw.Session().get_category().get_subcategories())
    assert not any(jw.TAG_EXCLUDE_FIRETV in subcategory.tags for subcategory in top_level_list)

    with rex.expect(cat=ROOT, client=''):
        top_level_list = list(jw.Session(client_type=jw.CLIENT_NONE).get_category().get_subcategories())
    assert any(jw.TAG_EXCLUDE_FIRETV in subcategory.tags for subcategory in top_level_list)


def test_get_category_include_media(rex):
    with rex.expect(cat=MIDDLE_LEVEL):
        middle = jw.Session().get_category(MIDDLE_LEVEL)

    middle_subcats = middle.get_subcategories()

    # Real world example of subcatmedialimit (grep that for more info).
    # As of 2026-09 "StudioMonthlyPrograms" exceeds the default value of inferred subcategory media limit (100+)
    # thus triggering a second request to make sure all media is there. To make the test more flexible, we don't
    # hardcode the key and amount, but derive it from whatever category is the biggest.
    # Note that "rex" statement below will fail if no category has more than 100 items.
    subcat_with_most_media = max((sc for sc in middle_subcats), key=lambda sc: len(sc.media))
    with rex.expect(cat=subcat_with_most_media.key, offset=len(subcat_with_most_media.media)):

        for bottom in middle_subcats:
            assert all(bottom.get_media())


def test_get_subcategories_include_media(rex):
    with rex.expect(cat=BOTTOM_LEVEL):
        bottom = jw.Session().get_category(BOTTOM_LEVEL)
    middle = bottom.get_parent()
    assert middle is not None

    with rex.expect(cat=MIDDLE_LEVEL):
        middle_subcats = middle.get_subcategories()

    # See comment above
    subcat_with_most_media = max((sc for sc in middle_subcats), key=lambda sc: len(sc.media))
    with rex.expect(cat=subcat_with_most_media.key, offset=len(subcat_with_most_media.media)):

        for sibling in middle_subcats:
            assert all(sibling.get_media())


def test_get_category_exclude_media(rex):
    with rex.expect(cat=BOTTOM_LEVEL, include_media=False):
        bottom = jw.Session().get_category(BOTTOM_LEVEL, include_media=False)
    with rex.expect(cat=BOTTOM_LEVEL):
        assert all(bottom.get_media())

    with rex.expect(cat=MIDDLE_LEVEL, include_media=False):
        middle = jw.Session().get_category(MIDDLE_LEVEL, include_media=False)
    bottom = middle.get_subcategories()[0]
    with rex.expect(cat=BOTTOM_LEVEL):
        assert all(bottom.get_media())


def test_get_subcategories_exclude_media(rex):
    with rex.expect(cat=BOTTOM_LEVEL):
        bottom = jw.Session().get_category(BOTTOM_LEVEL)
    assert bottom is not None
    middle = bottom.get_parent()
    assert middle is not None

    with rex.expect(cat=MIDDLE_LEVEL, include_media=False):
        sibling = next(s for s in middle.get_subcategories(include_media=False) if s is not bottom)
    assert sibling is not None

    with rex.expect(cat=sibling.key):
        assert all(sibling.get_media())


def test_get_subcategories(rex):
    root = jw.Session().get_category()

    with rex.expect(cat=ROOT):
        top = next(c for c in root.get_subcategories() if c.key == TOP_LEVEL)
    assert top is not None

    with rex.expect(cat=TOP_LEVEL):
        middle = top.get_subcategories()[0]
    assert middle is not None

    with rex.expect(cat=MIDDLE_LEVEL):
        bottom = middle.get_subcategories()[0]
    assert bottom is not None
    assert not any(bottom.get_subcategories())


def test_get_siblings(rex):
    with rex.expect(cat=BOTTOM_LEVEL):
        bottom = jw.Session().get_category(BOTTOM_LEVEL)
    assert bottom is not None
    middle = bottom.get_parent()
    assert middle is not None

    with rex.expect(cat=MIDDLE_LEVEL):
        assert all(middle.get_subcategories())


def test_category(rex):
    # Check all properties of Category
    with rex.expect(cat=TOP_LEVEL, lang='Z', client=jw.CLIENT_APPLETV):
        vod = jw.Session('Z', client_type=jw.CLIENT_APPLETV).get_category(TOP_LEVEL)

    assert vod.description
    image = vod.get_image(jw.RATIOS_3_1)
    assert image is not None and '_pnr_' in image
    assert vod.name
    assert isinstance(vod.tags, list)
    assert vod.type == jw.CATEGORY_CONTAINER

    session = jw.Session('Z', client_type=jw.CLIENT_APPLETV)
    with rex.expect(cat=BOTTOM_LEVEL, lang='Z', client=jw.CLIENT_APPLETV):
        cat = session.get_category(BOTTOM_LEVEL)

    with rex.expect(cat=BOTTOM_LEVEL):
        english_cat = jw.Session().get_category(BOTTOM_LEVEL)

    # Check that caching works
    assert cat is session.get_category(BOTTOM_LEVEL)

    # Make sure the test suit runs everything in swedish
    assert cat.session.language == 'Z'

    # Check that default language is English
    assert english_cat.session.language == 'E'

    # Check that languages are kept separate in the cache
    assert cat.key == english_cat.key
    assert cat is not english_cat

    # Check the ondemand property while we're at it
    assert cat.type == jw.CATEGORY_ONDEMAND


def test_media(rex):
    session = jw.Session('Z', client_type=jw.CLIENT_APPLETV)
    with rex.expect(mediaid='pub-mwbv_202003_4_VIDEO', client=jw.CLIENT_APPLETV, lang='Z'):
        media = session.get_media('pub-mwbv_202003_4_VIDEO')

    with rex.expect(cat='SeriesOrgAccomplishments', client=jw.CLIENT_APPLETV, lang='Z', include_media=False):
        primary_category = media.get_primary_category()

    time.strptime(media.published, jw.TIME_FORMAT)
    assert media.description == ''
    assert media.duration > 299
    assert media.duration_HHMM == '5:00'
    assert media.duration_min_sec == '5m 0s'
    assert media.guid
    image = media.get_image()
    assert image is not None and '_wss_' in image
    assert media.key == 'pub-mwbv_202003_4_VIDEO'
    assert media.key_with_language == 'pub-mwbv_Z_202003_4_VIDEO'
    assert 'Z' in media.languages
    assert primary_category is session.get_category(media.primary_category_key)
    assert media.primary_category_key == 'SeriesOrgAccomplishments'
    assert isinstance(media.print_references, list)
    assert media.session.language == 'Z'
    assert media.subtitle_url is not None and 'mwbv_Z_202003_04.vtt' in media.subtitle_url
    assert isinstance(media.tags, list)
    assert media.title == 'Vad organisationen uträttar: En uppdatering om våra webbplatser och appar'
    assert media.type == jw.MEDIA_VIDEO

    # Check all properties of a file object
    file = media.get_file()
    assert file.bitrate > 50
    assert file.checksum
    time.strptime(file.modified, jw.TIME_FORMAT)
    assert file.duration > 299
    assert file.filename == 'mwbv_Z_202003_04_r720P.mp4'
    assert round(file.frame_rate) == 24
    assert file.height == 720
    assert file.mimetype == 'video/mp4'
    assert file.resolution == 720
    assert file.size > 30000000
    assert file.subtitled_hard is False
    assert 'mwbv_Z_202003_04_r720P.mp4' in file.url
    assert file.width == 1280

    subtitles = file.subtitles
    assert subtitles is not None
    assert subtitles.url is not None and 'mwbv_Z_202003_04.vtt' in subtitles.url
    assert subtitles.checksum
    assert subtitles.date is not None and time.strptime(subtitles.date, jw.TIME_FORMAT)

    with rex.expect(mediaid='pub-osg_8_VIDEO', client=jw.CLIENT_APPLETV, lang='Z'):
        video = session.get_media('pub-osg_8_VIDEO')
    assert video.type == jw.MEDIA_VIDEO


def test_languages(rex):
    with rex.expect(raw=['languages/Z/web']):
        language = next(L for L in jw.get_session('Z').get_languages() if L.code == 'E')
    assert language.iso == 'en'
    assert language.name == 'Engelska'
    assert language.rtl is False
    assert language.script == 'ROMAN'
    assert language.vernacular == 'English'
    assert language.signed is False


def test_translations(rex):
    with rex.expect(raw=['translations/Z']):
        translations = jw.get_session('Z').get_translations()
    assert translations['btnPlay'] == 'Spela'


def test_invalid_requests(rex):
    with pytest.raises(jw.NotFoundError):
        with rex.expect(cat=ROOT, lang='jwlibInvalidLanguageTest'):
            # Needs to iterate with all() because of lazy-loading iterator
            assert all(jw.Session('jwlibInvalidLanguageTest').get_category().get_subcategories())

    with pytest.raises(jw.NotFoundError):
        with rex.expect(cat='jwlibInvalidCategoryTest'):
            jw.Session().get_category('jwlibInvalidCategoryTest')

    with pytest.raises(jw.NotFoundError):
        with rex.expect(mediaid='jwlibInvalidMediaTest'):
            jw.Session().get_media('jwlibInvalidMediaTest')


def test_cache_dump(rex):
    session = jw.Session()
    with rex.expect(cat=LATEST_VIDEOS):
        cat = session.get_category(LATEST_VIDEOS)
    media_count = len(list(cat.get_media()))
    assert media_count > 0
    cat_list = session.dump_categories()

    serialized = json.dumps(cat_list)
    deserialized = json.loads(serialized)

    session = jw.Session()
    session.load_categories(deserialized)
    with rex.expect():  # Expect nothing, it should be cached
        cat = session.get_category(LATEST_VIDEOS)
    assert len(list(cat.get_media())) == media_count


def test_generate_table(rex):
    buffer = io.StringIO()
    stdout = sys.stdout
    try:
        sys.stdout = buffer
        rex.enabled = False
        jwlib.media.imagetable.generate_image_table()
    finally:
        sys.stdout = stdout
        print(buffer.getvalue())
    assert '| ratio   | dimensions   | ratio alias   | size alias   | available for client type' in buffer.getvalue()
    assert '| 16:9    | 640x360      | wss           | lg           | appletv, firetv, none, www' in buffer.getvalue()


def test_deprecated_dict(rex):
    """All items used to have a dict property where data was stored.

    Now that we use dataclasses this is no longer needed, and instead is more costly to generate.
    """

    with rex.expect(cat=BOTTOM_LEVEL):
        bottom = jw.get_session().get_category(BOTTOM_LEVEL)
    with pytest.deprecated_call():
        assert isinstance(bottom.data, dict)

    media = bottom.get_media()[0]
    with pytest.deprecated_call():
        assert isinstance(media.data, dict)

    file = media.get_file()
    with pytest.deprecated_call():
        assert isinstance(file.data, dict)


def test_deprecated_functions(rex):
    # request_media() was renamed get_media()
    session = jw.Session('Z', client_type=jw.CLIENT_APPLETV)
    with rex.expect(mediaid='pub-mwbv_202003_4_VIDEO', client=jw.CLIENT_APPLETV, lang='Z'):
        with pytest.deprecated_call():
            media = session.request_media('pub-mwbv_202003_4_VIDEO')

    # request_languages() was moved to session.get_languages()
    with rex.expect(raw=['languages/Z/web']):
        with pytest.deprecated_call():
            assert jw.request_languages('Z')

    # request_translations() was moved to session.get_translations()
    with rex.expect(raw=['translations/Z']):
        with pytest.deprecated_call():
            assert jw.request_translations('Z')

    file = media.get_file()

    # subtitle_checksum was replaced by subtitles.checksum
    with pytest.deprecated_call():
        assert file.subtitle_checksum

    # subtitle_date was replaced by subtitles.date
    with pytest.deprecated_call():
        assert file.subtitle_date

    # subtitle_url was replaced by subtitles.url
    with pytest.deprecated_call():
        assert file.subtitle_url

    # subtitled_soft was replaced by subtitles is not None
    with pytest.deprecated_call():
        assert file.subtitled_soft


def test_deprecated_supports_next(rex):
    """The getter methods used to return an iterator...

    This works the same as a list with regard to iteration, but if you want the first item you'd call next()
    but this doesn't work for a list. So a compatibility layer has been added in between.

    Check that next() works for the calls below.
    """
    with rex.expect(cat=MIDDLE_LEVEL):
        cat_list = jw.Session().get_category(MIDDLE_LEVEL).get_subcategories()

    bottom: jw.Category
    with pytest.deprecated_call():
        bottom = next(cat_list) # type: ignore[call-overload]
    assert bottom

    media_list = bottom.get_media()
    media: jw.Media
    with pytest.deprecated_call():
        media = next(media_list)  # type: ignore[call-overload]
    assert media

    # media.get_files() has been replaced by media.files
    with pytest.deprecated_call():
        file_list = media.get_files()

    file: jw.File
    with pytest.deprecated_call():
        file = next(file_list)   # type: ignore[call-overload]
    assert file


# For debugging
if __name__ == '__main__':
    class DummyCaplog:
        text: str = 'opening'

        def clear(self):
            ...

        def set_level(self, level: int, module: str):
            ...


    test_get_category_exclude_media(DummyCaplog())  # types: ignore
