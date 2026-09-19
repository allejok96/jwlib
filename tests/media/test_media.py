from datetime import datetime

import pytest

from jwlib.media._file import File
from jwlib.media._media import Media


def make_media(**kwargs):
    kwargs.setdefault('session', object())
    return Media.create(**kwargs)


def test_media_create_wraps_file_dicts():
    media = make_media(files=[{'url': 'https://example.org/video.mp4'}])
    assert len(media.files) == 1
    assert isinstance(media.files[0], File)


def test_media_create_passes_through_file_instances():
    file = File.create(url='https://example.org/video.mp4')
    media = make_media(files=[file])
    assert media.files[0] is file


class FakeSession:
    def __init__(self, language='E'):
        self.language = language


def test_media_repr():
    media = Media.create(
        key='pub-key',
        session=FakeSession(),  # type: ignore[arg-type]
    )
    assert repr(media) == "<Media 'E/pub-key'>"


def test_media_get_published():
    media = make_media(published='2020-03-01T00:00:00')
    assert media.get_published() == datetime(2020, 3, 1, 0, 0, 0)


def test_media_subtitle_url_none_when_no_files_have_subtitles():
    media = make_media(files=[{'url': 'https://example.org/video.mp4'}])
    assert media.subtitle_url is None


def test_media_subtitle_url_returns_first_match():
    media = make_media(files=[
        {'url': 'https://example.org/audio.mp3'},
        {'url': 'https://example.org/video.mp4', 'subtitles': {'url': 'https://example.org/sub.vtt'}},
    ])
    assert media.subtitle_url == 'https://example.org/sub.vtt'


def test_media_get_primary_category_none_when_key_is_none():
    media = make_media(primary_category_key=None)
    assert media.get_primary_category() is None


def test_media_get_primary_category_delegates_to_session():
    class FakeSession:
        def get_category(self, key, *, include_media=False):
            self.called_with = (key, include_media)
            return 'the-category'

    session = FakeSession()
    media = Media.create(
        primary_category_key='SomeCategory',
        session=session,  # type: ignore[arg-type]
    )
    assert media.get_primary_category() == 'the-category'
    assert session.called_with == ('SomeCategory', False)

    assert media.get_primary_category(include_media=True) == 'the-category'
    assert session.called_with == ('SomeCategory', True)


# ------------------------------------------------
# get_file() - resolution/subtitle selection logic
# ------------------------------------------------

def make_file(resolution, subtitles=None, subtitled_hard=False):
    return File.create(url=f'https://example.org/{resolution}.mp4', resolution=resolution,
                       subtitles=subtitles, subtitled_hard=subtitled_hard)


def test_get_file_raises_on_empty_list():
    media = make_media(files=[])
    with pytest.raises(LookupError):
        media.get_file()


def test_get_file_picks_highest_resolution_by_default():
    low = make_file(240)
    mid = make_file(480)
    high = make_file(1080)
    extreme = make_file(4320)
    media = make_media(files=[low, high, extreme, mid])

    assert media.get_file() is extreme
    assert media.get_file(resolution=0) is extreme


def test_get_file_never_exceeds_requested_resolution_if_lower_option_exists():
    low = make_file(240)
    high = make_file(1080)
    media = make_media(files=[low, high])
    assert media.get_file(resolution=480) is low


def test_get_file_falls_back_to_lowest_when_all_exceed_resolution():
    only_option = make_file(1080)
    media = make_media(files=[only_option])
    assert media.get_file(resolution=240) is only_option


def test_get_file_prefers_subtitled_when_requested():
    plain = make_file(720)
    soft_subbed = make_file(720, subtitles={'url': 'https://example.org/sub.vtt'})
    media = make_media(files=[plain, soft_subbed])
    assert media.get_file(resolution=720, subtitles=True) is soft_subbed


def test_get_file_prefers_soft_subtitles_over_hard_when_both_available():
    hard_subbed = make_file(720, subtitled_hard=True)
    soft_subbed = make_file(720, subtitles={'url': 'https://example.org/sub.vtt'})
    media = make_media(files=[hard_subbed, soft_subbed])
    assert media.get_file(resolution=720, subtitles=True) is soft_subbed


def test_get_file_prefers_unsubtitled_when_not_requested():
    plain = make_file(720)
    soft_subbed = make_file(720, subtitles={'url': 'https://example.org/sub.vtt'})
    media = make_media(files=[plain, soft_subbed])
    assert media.get_file(resolution=720, subtitles=False) is plain
