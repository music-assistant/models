"""All (global/common) constants for Music Assistant."""

from typing import Final

SECURE_STRING_SUBSTITUTE = "this_value_is_encrypted"

# if duration is None (e.g. radio stream) = 48 hours
FALLBACK_DURATION: Final[int] = 172800
