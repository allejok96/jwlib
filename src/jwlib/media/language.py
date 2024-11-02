"""
Language list and info
"""
from __future__ import annotations

from ..common import _DictWrapper
from .endpoints import _request_languages

__all__ = 'request_languages', 'Language'


def request_languages(language='E') -> list[Language]:
    """Return list of available Languages"""

    return [Language(L) for L in _request_languages(language)]


class Language(_DictWrapper):
    """Information about a language"""

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.code!r}>'

    @property
    def code(self) -> str:
        """JW language code

        The one that can be passed to :class:`Session` etc.
        """
        return self._get_string('code')

    @property
    def iso(self) -> str:
        """ISO 639 language code"""
        return self._get_string('locale')

    @property
    def name(self) -> str:
        """Display name"""
        return self._get_string('name', '')

    # This seems to always be False
    # @property
    # def pair(self) -> bool:
    #    return self.dict.get('isLangPair', False)

    @property
    def rtl(self) -> bool:
        """True if written right to left"""
        return self.data.get('isRTL', False)

    @property
    def script(self) -> str:
        """Type of script, like 'ROMAN' or 'CYRILLIC'"""
        return self._get_string('script', '')

    @property
    def signed(self) -> bool:
        """True if it's a sign language"""
        return self.data.get('isSignLanguage', False)

    @property
    def vernacular(self) -> str:
        """Display name in the language itself"""
        return self._get_string('vernacular', '')
