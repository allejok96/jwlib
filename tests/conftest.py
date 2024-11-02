import pytest

# Apply this to all unmarked items:
# @pytest.mark.vcr
# @pytest.mark.default_cassette('cassette.yaml')

def pytest_collection_modifyitems(session, config, items):
    for item in items:
        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.vcr(allow_playback_repeats=True))
            item.add_marker(pytest.mark.default_cassette('cassette.yaml'))


