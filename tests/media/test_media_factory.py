import pytest

from jwlib.media._media_factory import create_file, create_media, create_subtitles, resolution_from_label


# ------------------------
# resolution_from_label()
# ------------------------

@pytest.mark.parametrize('label, expected', [
    ('360p', 360),
    ('720P', 720),
    ('0p', 0),
    ('4K', 4 * 540),
    ('4k', 4 * 540),
    ('1080', 1080),
    ('', 0),
    ('bogus', 0),
    (None, 0),
])
def test_resolution_from_label(label, expected):
    assert resolution_from_label(label) == expected


# ---------------
# create_subtitles
# ---------------

def test_create_subtitles_full():
    subtitle = create_subtitles({
        'checksum': 'abc123',
        'modifiedDatetime': '2020-01-02T03:04:05.000Z',
        'url': 'https://example.org/sub.vtt',
    })
    assert subtitle.checksum == 'abc123'
    assert subtitle.date == '2020-01-02T03:04:05'
    assert subtitle.url == 'https://example.org/sub.vtt'


def test_create_subtitles_minimal():
    subtitle = create_subtitles({'url': 'https://example.org/sub.vtt'})  # type: ignore[typeddict-item]
    assert subtitle.checksum is None
    assert subtitle.date == ''
    assert subtitle.url == 'https://example.org/sub.vtt'


# -----------
# create_file
# -----------

def test_create_file_full():
    file = create_file({
        'bitRate': 512.0,
        'checksum': 'deadbeef',
        'duration': 300.0,
        'frameHeight': 720,
        'frameRate': 23.976,
        'frameWidth': 1280,
        'label': '720p',
        'mimetype': 'video/mp4',
        'modifiedDatetime': '2020-03-01T00:00:00.000Z',
        'filesize': 12345,
        'subtitled': True,
        'subtitles': {'url': 'https://example.org/sub.vtt'},  # type: ignore[typeddict-item]
        'progressiveDownloadURL': 'https://example.org/video.mp4',
    })
    assert file.bitrate == 512.0
    assert file.checksum == 'deadbeef'
    assert file.duration == 300.0
    assert file.frame_rate == 23.976
    assert file.height == 720
    assert file.mimetype == 'video/mp4'
    assert file.modified == '2020-03-01T00:00:00'
    assert file.resolution == 720
    assert file.size == 12345
    assert file.subtitled_hard is True
    assert file.subtitles is not None
    assert file.subtitles.url == 'https://example.org/sub.vtt'
    assert file.url == 'https://example.org/video.mp4'
    assert file.width == 1280


def test_create_file_minimal_defaults():
    file = create_file({'progressiveDownloadURL': 'https://example.org/video.mp4'})  # type: ignore[typeddict-item]
    assert file.bitrate == 0.0
    assert file.checksum is None
    assert file.duration == 0.0
    assert file.frame_rate == 0.0
    assert file.height == 0
    assert file.mimetype == 'application/octet-stream'
    assert file.modified == ''
    assert file.resolution == 0
    assert file.size == 0
    assert file.subtitled_hard is False
    assert file.subtitles is None
    assert file.width == 0


def test_create_file_missing_subtitles_key_means_none():
    # 'subtitles' key entirely absent -> no subtitles (as opposed to an empty dict)
    file = create_file({'progressiveDownloadURL': 'https://example.org/video.mp4'})  # type: ignore[typeddict-item]
    assert file.subtitles is None


# ------------
# create_media
# ------------

def test_create_media_full():
    session = object()
    media = create_media(
        {
            'availableLanguages': ['E', 'Z'],
            'description': 'a description',
            'duration': 300.0,
            'durationFormattedHHMM': '5:00',
            'durationFormattedMinSec': '5m 0s',
            'files': [{'progressiveDownloadURL': 'https://example.org/video.mp4'}],  # type: ignore[typeddict-item]
            'firstPublished': '2020-03-01T00:00:00.000Z',
            'guid': 'abc123',
            'images': {'wss': {'lg': 'https://example.org/image.jpg'}},
            'languageAgnosticNaturalKey': 'pub-key',
            'naturalKey': 'pub-key-lang',
            'primaryCategory': 'SomeCategory',
            'printReferences': ['ref1'],
            'tags': ['SomeTag'],
            'title': 'Some title',
            'type': 'video',
        },
        parent='SomeParent',
        session=session,  # type: ignore[arg-type]
    )

    assert media.description == 'a description'
    assert media.duration == 300.0
    assert media.duration_HHMM == '5:00'
    assert media.duration_min_sec == '5m 0s'
    assert len(media.files) == 1
    assert media.guid == 'abc123'
    assert media.images == {'wss': {'lg': 'https://example.org/image.jpg'}}
    assert media.key == 'pub-key'
    assert media.key_with_language == 'pub-key-lang'
    assert media.languages == ['E', 'Z']
    assert media.parent == 'SomeParent'
    assert media.primary_category_key == 'SomeCategory'
    assert media.print_references == ['ref1']
    assert media.published == '2020-03-01T00:00:00'
    assert media.session is session
    assert media.tags == ['SomeTag']
    assert media.title == 'Some title'
    assert media.type == 'video'


def test_create_media_minimal_defaults():
    session = object()

    media = create_media(
        {  # type: ignore[typeddict-item]
            'languageAgnosticNaturalKey': 'pub-key',
            'naturalKey': 'pub-key-lang',
            'type': 'audio',
        },
        parent=None,
        session=session,  # type: ignore[arg-type]
    )

    assert media.description == ''
    assert media.duration == 0.0
    assert media.duration_HHMM == '0:00'
    assert media.duration_min_sec == '0s'
    assert media.files == []
    assert media.guid == ''
    assert media.images == {}
    assert media.languages == []
    assert media.parent is None
    assert media.primary_category_key is None
    assert media.print_references == []
    assert media.published == ''
    assert media.tags == []
    assert media.title == ''
    assert media.type == 'audio'
