import pytest

import jwlib.media._api_requests


@pytest.fixture(autouse=True)
def reset_inferred_media_limit(monkeypatch):
    """Reset inferred media limit to default value after each test."""
    original = jwlib.media._api_requests.get_inferred_media_limit()
    yield
    jwlib.media._api_requests.set_inferred_media_limit(original)


# Apply this to all unmarked items:
# @pytest.mark.vcr
# @pytest.mark.default_cassette('cassette.yaml')

def pytest_collection_modifyitems(session, config, items):
    for item in items:
        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.vcr(allow_playback_repeats=True))
            item.add_marker(pytest.mark.default_cassette('cassette.yaml'))


def pytest_recording_configure(config, vcr):
    assert vcr, 'pytest-recording is not installed!'
