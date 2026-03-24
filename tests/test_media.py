import io
import logging
import sys
import time

import jwlib.media as jw
import jwlib.media.imagetable


class Request:
    """Context manager that asserts that there is exactly ONE call to the API

    Since jwlib performs lazy-loading of categories and media, all test code
    should be wrapped in this context manager to make sure there are no unexpected
    or duplicate requests made to the API.
    """

    def __init__(self, caplog, expected_request_count=1):
        caplog.set_level(logging.DEBUG, 'jwlib')
        self.caplog = caplog
        self.expected_request_count = expected_request_count

    def __enter__(self):
        ...

    def __exit__(self, exc_type, exc_val, exc_tb):
        requests_made = self.caplog.text.count('opening')
        assert requests_made == self.expected_request_count, f'Expected {self.expected_request_count} request, got {requests_made}'
        self.caplog.clear()


ROOT = jw.ROOT_CATEGORY
TOP_LEVEL = 'VideoOnDemand'
MIDDLE_LEVEL = 'VODStudio'
BOTTOM_LEVEL = 'StudioFeatured'
LATEST_VIDEOS = 'LatestVideos'


def test_get_parent(caplog):
    with Request(caplog):
        bottom = jw.Session().get_category(BOTTOM_LEVEL)
        # Parent should be included when getting category
        middle = bottom.get_parent()
        assert middle is not None
    # Parent of parent needs to be fetched
    with Request(caplog):
        top = middle.get_parent()
        assert top is not None
    # Parent of top-level is virtual root (no request needed)
    with Request(caplog):
        root = top.get_parent()
        assert root is not None
        # Parent of root is always None
        assert root.get_parent() is None


def test_get_media(caplog):
    with Request(caplog):
        bottom = jw.Session().get_category(BOTTOM_LEVEL)
        # Bottom categories should include media
        assert all(bottom.get_media())
        # Container categories shouldn't contain media, and not try to request it either
        parent = bottom.get_parent()
        assert parent is not None
        assert not any(parent.get_media())


def test_get_media_toplevel(caplog):
    # Root has no media
    with Request(caplog, expected_request_count=0):
        root = jw.Session().get_category()
        assert not any(root.get_media())
    # The list of top-level categories doesn't include media
    with Request(caplog):
        top_level_list = list(root.get_subcategories())
    with Request(caplog):
        for subcategory in top_level_list:
            if subcategory.key == LATEST_VIDEOS:
                assert all(subcategory.get_media())


def test_hidden_categories(caplog):
    with Request(caplog):
        top_level_list = list(jw.Session().get_category().get_subcategories())
        assert not any(jw.TAG_EXCLUDE_FIRETV in subcategory.tags for subcategory in top_level_list)

    with Request(caplog):
        top_level_list = list(jw.Session(client_type=jw.CLIENT_NONE).get_category().get_subcategories())
        assert any(jw.TAG_EXCLUDE_FIRETV in subcategory.tags for subcategory in top_level_list)


def test_get_category_include_media(caplog):
    with Request(caplog):
        middle = jw.Session().get_category(MIDDLE_LEVEL)
        for bottom in middle.get_subcategories():
            assert all(bottom.get_media())


def test_get_subcategories_include_media(caplog):
    with Request(caplog):
        bottom = jw.Session().get_category(BOTTOM_LEVEL)
        middle = bottom.get_parent()
        assert middle is not None
    with Request(caplog):
        for sibling in middle.get_subcategories():
            assert all(sibling.get_media())


def test_get_category_exclude_media(caplog):
    with Request(caplog):
        bottom = jw.Session().get_category(BOTTOM_LEVEL, include_media=False)
    with Request(caplog):
        assert all(bottom.get_media())

    with Request(caplog):
        middle = jw.Session().get_category(MIDDLE_LEVEL, include_media=False)
        bottom = next(middle.get_subcategories())
    with Request(caplog):
        assert all(bottom.get_media())


def test_get_subcategories_exclude_media(caplog):
    with Request(caplog):
        bottom = jw.Session().get_category(BOTTOM_LEVEL)
        assert bottom is not None
        middle = bottom.get_parent()
        assert middle is not None
    with Request(caplog):
        sibling = next(s for s in middle.get_subcategories(include_media=False) if s is not bottom)
        assert sibling is not None
    with Request(caplog):
        assert all(sibling.get_media())


def test_get_subcategories(caplog):
    with Request(caplog, expected_request_count=0):
        root = jw.Session().get_category()
    with Request(caplog):
        top = next(c for c in root.get_subcategories() if c.key == 'VideoOnDemand')
        assert top is not None
    with Request(caplog):
        middle = next(top.get_subcategories())
        assert middle is not None
    with Request(caplog):
        bottom = next(middle.get_subcategories())
        assert bottom is not None
        assert not any(bottom.get_subcategories())


def test_get_siblings(caplog):
    with Request(caplog):
        bottom = jw.Session().get_category(BOTTOM_LEVEL)
        assert bottom is not None
        middle = bottom.get_parent()
        assert middle is not None
    with Request(caplog):
        assert all(middle.get_subcategories())


def test_category(caplog):
    # Check all properties of Category
    with Request(caplog):
        vod = jw.Session('Z', client_type=jw.CLIENT_APPLETV).get_category(TOP_LEVEL)

        assert vod.description
        assert isinstance(vod.data, dict)
        image = vod.get_image(jw.RATIOS_3_1)
        assert image is not None and '_pnr_' in image
        assert vod.name
        assert isinstance(vod.tags, list)
        assert vod.type == jw.CATEGORY_CONTAINER

    with Request(caplog):
        session = jw.Session('Z', client_type=jw.CLIENT_APPLETV)
        cat = session.get_category(BOTTOM_LEVEL)

    with Request(caplog):
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


def test_media(caplog):
    with Request(caplog):
        session = jw.Session('Z', client_type=jw.CLIENT_APPLETV)
        media = session.request_media('pub-mwbv_202003_4_VIDEO')
    with Request(caplog):
        primary_category = media.get_primary_category()

        time.strptime(media.published, jw.TIME_FORMAT)
        assert isinstance(media.data, dict)
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
        assert isinstance(file.data, dict)
        assert file.duration > 299
        assert file.filename == 'mwbv_Z_202003_04_r720P.mp4'
        assert round(file.frame_rate) == 24
        assert file.height == 720
        assert file.mimetype == 'video/mp4'
        assert isinstance(file.print_references, list)
        assert file.resolution == 720
        assert file.size > 30000000
        assert file.subtitled_hard is False
        assert file.subtitled_soft is True
        assert file.subtitle_url is not None and 'mwbv_Z_202003_04.vtt' in file.subtitle_url
        assert file.subtitle_checksum
        assert file.subtitle_date is not None and time.strptime(file.subtitle_date, jw.TIME_FORMAT)
        assert 'mwbv_Z_202003_04_r720P.mp4' in file.url
        assert file.width == 1280

    with Request(caplog):
        video = session.request_media('pub-osg_8_VIDEO')
        assert video.type == jw.MEDIA_VIDEO


def test_languages(caplog):
    with Request(caplog):
        language = next(L for L in jw.request_languages('Z') if L.code == 'E')
        assert language.iso == 'en'
        assert language.name == 'Engelska'
        assert language.rtl is False
        assert language.script == 'ROMAN'
        assert language.vernacular == 'English'
        assert language.signed is False


def test_translations(caplog):
    with Request(caplog):
        translations = jw.request_translations('Z')
        assert translations['btnPlay'] == 'Spela'


def test_invalid_requests(caplog):
    with Request(caplog):
        try:
            # Needs to iterate with all() because of lazy-loading iterator
            assert all(jw.Session('jwlibInvalidLanguageTest').get_category().get_subcategories())
            assert False, 'Did not raise NotFoundError'
        except jw.NotFoundError:
            pass

    with Request(caplog):
        try:
            jw.Session().get_category('jwlibInvalidCategoryTest')
            assert False, 'Did not raise NotFoundError'
        except jw.NotFoundError:
            pass

    with Request(caplog):
        try:
            jw.Session().request_media('jwlibInvalidMediaTest')
            assert False, 'Did not raise NotFoundError'
        except jw.NotFoundError:
            pass



def test_cache_dump(caplog):
    with Request(caplog):
        session = jw.Session()
        cat = session.get_category(LATEST_VIDEOS)
        media_count = len(list(cat.get_media()))
        assert media_count > 0
        dump = session.dump_categories()

    with (Request(caplog, expected_request_count=0)):
        session = jw.Session()
        session.load_categories(dump)
        cat = session.get_category(LATEST_VIDEOS)
        assert len(list(cat.get_media())) == media_count


def test_generate_table():
    buffer = io.StringIO()
    stdout = sys.stdout
    try:
        sys.stdout = buffer
        jwlib.media.imagetable.generate_image_table()
    finally:
        sys.stdout = stdout
        print(buffer.getvalue())
    assert '| ratio   | dimensions   | ratio alias   | size alias   | available for client type' in buffer.getvalue()
    assert '| 16:9    | 640x360      | wss           | lg           | appletv, firetv, none, www' in buffer.getvalue()


# For debugging
if __name__ == '__main__':
    class DummyCaplog:
        text: str = 'opening'

        def clear(self):
            ...

        def set_level(self, level: int, module: str):
            ...


    test_get_category_exclude_media(DummyCaplog())  # type: ignore
