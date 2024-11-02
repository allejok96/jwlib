import io
import logging
import sys
import time

import jwlib.media as jw
import jwlib.media.imagetable

# Need this for category posters
en = jw.Session(client_type=jw.CLIENT_APPLETV)
sv = jw.Session('Z', client_type=jw.CLIENT_APPLETV)


class CaplogProtocol:
    text = 'opening'

    def clear(self):
        ...

    def set_level(self, level: int, module: str):
        ...


class Request:
    def __init__(self, caplog: CaplogProtocol):
        caplog.set_level(logging.DEBUG, 'jwlib')
        self.caplog = caplog
        self.expected = 0
        self.detected = 0

    def __enter__(self):
        self.detected = 0
        self.expected = 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self.expected == self.caplog.text.count('opening')
        self.caplog.clear()


ROOT = jw.ROOT_CATEGORY
TOP_LEVEL = 'VideoOnDemand'
MIDDLE_LEVEL = 'VODStudio'
BOTTOM_LEVEL = 'StudioFeatured'


def test_get_parent(caplog):
    with Request(caplog):
        bottom = jw.Session().get_category(BOTTOM_LEVEL)
    # Parent should be included when getting category
    middle = bottom.get_parent()
    # Parent of parent needs to be fetched
    with Request(caplog):
        top = middle.get_parent()
    # Parent of top-level is virtual root (no request needed)
    with Request(caplog):
        root = top.get_parent()
    # Parent of root is always None
    assert root.get_parent() is None


def test_get_media(caplog):
    with Request(caplog):
        bottom = jw.Session().get_category(BOTTOM_LEVEL)
    # Bottom categories should include media
    assert all(bottom.get_media())
    # Container categories shouldn't contain media, and not try to request it either
    assert not any(bottom.get_parent().get_media())


def test_get_media_toplevel(caplog):
    # Root has no media
    root = jw.Session().get_category()
    assert not any(root.get_media())
    # The list of top-level categories doesn't include media
    with Request(caplog):
        top_level_list = list(root.get_subcategories())
    for subcategory in top_level_list:
        if subcategory.key == 'LatestVideos':
            with Request(caplog):
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
    middle = bottom.get_parent()
    with Request(caplog):
        sibling = next(s for s in middle.get_subcategories(include_media=False) if s is not bottom)
    with Request(caplog):
        assert all(sibling.get_media())


def test_get_subcategories(caplog):
    root = jw.Session().get_category()
    with Request(caplog):
        top = next(c for c in root.get_subcategories() if c.key == 'VideoOnDemand')
    with Request(caplog):
        middle = next(top.get_subcategories())
    with Request(caplog):
        bottom = next(middle.get_subcategories())
    assert not any(bottom.get_subcategories())


def test_get_siblings(caplog):
    with Request(caplog):
        bottom = jw.Session().get_category(BOTTOM_LEVEL)
    middle = bottom.get_parent()
    with Request(caplog):
        assert all(middle.get_subcategories())


def test_category(caplog):
    session = jw.Session('Z', client_type=jw.CLIENT_APPLETV)

    # Check all properties of Category
    with Request(caplog):
        vod = jw.Session('Z', client_type=jw.CLIENT_APPLETV).get_category(TOP_LEVEL)

    assert vod.description
    assert isinstance(vod.data, dict)
    assert '_pnr_' in vod.get_image(jw.RATIOS_3_1)
    assert vod.name
    assert isinstance(vod.tags, list)
    assert vod.type == jw.CATEGORY_CONTAINER

    with Request(caplog):
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
        media = sv.request_media('pub-mwbv_202003_4_VIDEO')
    with Request(caplog):
        primary_category = media.get_primary_category()

        time.strptime(media.published, jw.TIME_FORMAT)
        assert isinstance(media.data, dict)
        assert media.duration > 299
        assert media.duration_HHMM == '5:00'
        assert media.duration_min_sec == '5m 0s'
        assert media.guid
        assert '_wss_' in media.get_image()
        assert media.key == 'pub-mwbv_202003_4_VIDEO'
        assert media.key_with_language == 'pub-mwbv_Z_202003_4_VIDEO'
        assert 'Z' in media.languages
        assert primary_category is sv.get_category(media.primary_category_key)
        assert media.primary_category_key == 'SeriesOrgAccomplishments'
        assert media.session.language == 'Z'
        assert 'mwbv_Z_202003_04.vtt' in media.subtitle_url
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
        assert file.frame_rate == 23.976
        assert file.height == 720
        assert isinstance(file.print_references, list)
        assert file.resolution == 720
        assert file.size > 30000000
        assert file.subtitled_hard is False
        assert file.subtitled_soft is True
        assert 'mwbv_Z_202003_04.vtt' in file.subtitle_url
        assert file.subtitle_checksum
        time.strptime(file.subtitle_date, jw.TIME_FORMAT)
        assert 'mwbv_Z_202003_04_r720P.mp4' in file.url
        assert file.width == 1280

    with Request(caplog):
        video = sv.request_media('pub-osg_8_VIDEO')
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


if __name__ == '__main__':
    # For debugging
    test_get_category_exclude_media(CaplogProtocol())
