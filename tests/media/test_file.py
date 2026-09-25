from datetime import datetime

import pytest

from jwlib.media._file import File, Subtitles


def test_file_create_defaults():
    file = File.create(url='https://example.org/video.mp4')
    assert file.bitrate == 0.0
    assert file.checksum is None
    assert file.duration == 0.0
    assert file.frame_rate == 0.0
    assert file.height == 0
    assert file.mimetype == 'application/octet-stream'
    assert file.modified == ''
    assert file.resolution == 0
    assert file.size == 0
    assert file.subtitles is None
    assert file.subtitled_hard is False
    assert file.width == 0


def test_file_create_with_subtitle_dict():
    file = File.create(url='https://example.org/video.mp4',
                       subtitles={'url': 'https://example.org/sub.vtt', 'checksum': 'abc'})
    assert isinstance(file.subtitles, Subtitles)
    assert file.subtitles.url == 'https://example.org/sub.vtt'
    assert file.subtitles.checksum == 'abc'


def test_file_create_with_subtitle_instance_passthrough():
    subtitle = Subtitles.create(url='https://example.org/sub.vtt')
    file = File.create(url='https://example.org/video.mp4', subtitles=subtitle)
    assert file.subtitles is subtitle


def test_file_filename_from_url():
    file = File.create(url='https://example.org/path/to/video_720P.mp4?query=1')
    assert file.filename == 'video_720P.mp4'


def test_file_get_modified():
    file = File.create(url='x', modified='2020-03-01T12:30:00')
    assert file.get_modified() == datetime(2020, 3, 1, 12, 30, 0)


def test_file_repr_uses_filename():
    file = File.create(url='https://example.org/video.mp4')
    assert repr(file) == "<File 'video.mp4'>"


def test_file_repr_falls_back_on_error():
    # url=None cannot be parsed by urlparse -> filename raises -> repr should not blow up
    file = File.create(url=None)  # type: ignore[arg-type]
    assert 'File' in repr(file)


def test_file_deprecated_subtitle_shims_delegate_to_subtitles():
    file = File.create(url='x', subtitles={'url': 'https://example.org/sub.vtt',
                                           'checksum': 'abc',
                                           'date': '2020-01-01T00:00:00'})
    with pytest.deprecated_call():
        assert file.subtitle_checksum == 'abc'
    with pytest.deprecated_call():
        assert file.subtitle_date == '2020-01-01T00:00:00'
    with pytest.deprecated_call():
        assert file.subtitle_url == 'https://example.org/sub.vtt'
    with pytest.deprecated_call():
        assert file.subtitled_soft is True


def test_file_deprecated_subtitle_shims_none_when_no_subtitles():
    file = File.create(url='x')
    with pytest.deprecated_call():
        assert file.subtitle_checksum is None
    with pytest.deprecated_call():
        assert file.subtitle_date is None
    with pytest.deprecated_call():
        assert file.subtitle_url is None
    with pytest.deprecated_call():
        assert file.subtitled_soft is False


def test_subtitle_create_defaults():
    subtitle = Subtitles.create(url='https://example.org/sub.vtt')
    assert subtitle.checksum is None
    assert subtitle.date == ''
    assert subtitle.url == 'https://example.org/sub.vtt'


def test_subtitle_get_date():
    subtitle = Subtitles.create(url='x', date='2020-03-01T12:30:00')
    assert subtitle.get_date() == datetime(2020, 3, 1, 12, 30, 0)
