from jwlib.media._language_factory import create_language


def test_create_language_full():
    language = create_language({
        'code': 'E',
        'locale': 'en',
        'name': 'English',
        'isRTL': True,
        'script': 'ROMAN',
        'isSignLanguage': True,
        'pair': False,
        'vernacular': 'English',
    })
    assert language.code == 'E'
    assert language.iso == 'en'
    assert language.name == 'English'
    assert language.rtl is True
    assert language.script == 'ROMAN'
    assert language.signed is True
    assert language.vernacular == 'English'


def test_create_language_minimal_defaults():
    language = create_language({'code': 'E'})  # type: ignore[typeddict-item]
    assert language.code == 'E'
    assert language.iso == ''
    assert language.name == ''
    assert language.rtl is False
    assert language.script == ''
    assert language.signed is False
    assert language.vernacular == ''
