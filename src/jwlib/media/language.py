"""
Module kept for compatibility
"""
import warnings

from jwlib.media import Language, request_languages

__all__ = 'request_languages', 'Language'


warnings.warn(
    "Importing jwlib.media.language is deprecated, see jwlib.media.",
    category=DeprecationWarning,
)

