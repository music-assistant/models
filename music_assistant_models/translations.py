"""Translation resolution hook used during outbound API serialization."""

from __future__ import annotations

from collections.abc import Callable
from contextvars import ContextVar

# ContextVar set by the Music Assistant server during outbound API serialization.
# When set, model __post_serialize__ hooks use the resolver to replace human-readable
# fields (label/name/title/description/...) with strings localized for the connection's
# locale. The resolver receives a (relative or fully-qualified) translation key plus an
# optional owner hint and positional params, and returns the localized string, or None
# when nothing matches so the model keeps its existing value rather than a raw key.
TRANSLATION_RESOLVER: ContextVar[Callable[..., str | None] | None] = ContextVar(
    "translation_resolver", default=None
)


def translations_active() -> bool:
    """
    Return True when an outbound API serialization is in progress (a resolver is bound).

    Models use this to strip internal translation machinery (translation_key/params) from the
    localized API output while keeping it in plain ``to_dict()`` calls used for internal
    round-tripping (caching, item mappings, config storage).
    """
    return TRANSLATION_RESOLVER.get() is not None


def resolve_translation(
    key: str, owner: str | None = None, params: list[str] | None = None
) -> str | None:
    """
    Resolve a translation key via the resolver set on the current context.

    Returns None when no resolver is set (e.g. non-API serialization) or when the key
    cannot be resolved, so callers keep any existing (English) value. Never raises.

    :param key: Translation key, relative (e.g. "config_entries.username.label") or
        fully-qualified (e.g. "provider.ytmusic.manifest.name").
    :param owner: Optional owner hint (provider domain/instance) for relative keys.
    :param params: Optional positional arguments for ``{0}``/``{1}`` placeholders.
    """
    resolver = TRANSLATION_RESOLVER.get()
    if resolver is None:
        return None
    try:
        return resolver(key, owner=owner, params=params)
    except Exception:  # noqa: BLE001 - resolution must never break serialization
        return None
