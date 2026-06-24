"""Custom errors and exceptions."""

from typing import Any


class MusicAssistantError(Exception):
    """Custom Exception for all errors."""

    error_code = 0
    # Default translation key for this error type: a bare slug (e.g. ``media_not_found``). During
    # outbound API serialization the error model derives the ``errors.<slug>`` group and resolves
    # it owner-first then against the server's ``common.errors.*`` strings to localize the message
    # shown to clients. Subclasses set their own default; callers may override the key (and provide
    # an owning provider/controller and positional args for {0}/{1} placeholders) per-instance.
    translation_key: str | None = None
    # Owning namespace ("provider.<domain>"/"core.<domain>") whose strings.json is consulted before
    # falling back to common — set when a provider/controller defines its own message for the key.
    translation_owner: str | None = None

    def __init__(
        self,
        *args: object,
        translation_key: str | None = None,
        translation_args: list[Any] | None = None,
        translation_owner: str | None = None,
    ) -> None:
        """
        Initialize the error.

        :param translation_key: Optional per-instance override of the error type's default
            translation key (a bare slug), used to localize the message shown to API clients.
        :param translation_args: Optional positional arguments for {0}/{1} placeholders in the
            translated message.
        :param translation_owner: Optional owning namespace ("provider.<domain>"/"core.<domain>")
            consulted before common when resolving the key.
        """
        super().__init__(*args)
        if translation_key is not None:
            self.translation_key = translation_key
        self.translation_args: list[Any] = translation_args or []
        if translation_owner is not None:
            self.translation_owner = translation_owner

    def __init_subclass__(cls, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        """Register a subclass."""
        super().__init_subclass__(*args, **kwargs)
        ERROR_MAP[cls.error_code] = cls


# mapping from error_code to Exception class
ERROR_MAP: dict[int, type] = {0: MusicAssistantError, 999: MusicAssistantError}


class ProviderUnavailableError(MusicAssistantError):
    """Error raised when trying to access mediaitem of unavailable provider."""

    error_code = 1
    translation_key = "provider_unavailable"


class MediaNotFoundError(MusicAssistantError):
    """Error raised when trying to access non existing media item."""

    error_code = 2
    translation_key = "media_not_found"


class InvalidDataError(MusicAssistantError):
    """Error raised when an object has invalid data."""

    error_code = 3
    translation_key = "invalid_data"


class AlreadyRegisteredError(MusicAssistantError):
    """Error raised when a duplicate music provider or player is registered."""

    error_code = 4
    translation_key = "already_registered"


class SetupFailedError(MusicAssistantError):
    """Error raised when setup of a provider or player failed."""

    error_code = 5
    translation_key = "setup_failed"


class LoginFailed(MusicAssistantError):
    """Error raised when a login failed."""

    error_code = 6
    translation_key = "login_failed"


class AudioError(MusicAssistantError):
    """Error raised when an issue arose when processing audio."""

    error_code = 7
    translation_key = "audio_error"


class QueueEmpty(MusicAssistantError):
    """Error raised when trying to start queue stream while queue is empty."""

    error_code = 8
    translation_key = "queue_empty"


class UnsupportedFeaturedException(MusicAssistantError):
    """Error raised when a feature is not supported."""

    error_code = 9
    translation_key = "unsupported_feature"


class PlayerUnavailableError(MusicAssistantError):
    """Error raised when trying to access non-existing or unavailable player."""

    error_code = 10
    translation_key = "player_unavailable"


class PlayerCommandFailed(MusicAssistantError):
    """Error raised when a command to a player failed execution."""

    error_code = 11
    translation_key = "player_command_failed"


class InvalidCommand(MusicAssistantError):
    """Error raised when an unknown command is requested on the API."""

    error_code = 12
    translation_key = "invalid_command"


class UnplayableMediaError(MusicAssistantError):
    """Error thrown when a MediaItem cannot be played properly."""

    error_code = 13
    translation_key = "unplayable_media"


class InvalidProviderURI(MusicAssistantError):
    """Error thrown when a provider URI does not match a known format."""

    error_code = 14
    translation_key = "invalid_provider_uri"


class InvalidProviderID(MusicAssistantError):
    """Error thrown when a provider media item identifier does not match a known format."""

    error_code = 15
    translation_key = "invalid_provider_id"


class RetriesExhausted(MusicAssistantError):
    """Error thrown when a retries to a given provider URI have been exhausted."""

    error_code = 16
    translation_key = "retries_exhausted"


class ResourceTemporarilyUnavailable(MusicAssistantError):
    """Error thrown when a resource is temporarily unavailable."""

    error_code = 17
    translation_key = "resource_temporarily_unavailable"

    def __init__(self, *args: object, backoff_time: int = 0, **kwargs: Any) -> None:
        """Initialize."""
        super().__init__(*args, **kwargs)
        self.backoff_time = backoff_time


class ProviderPermissionDenied(MusicAssistantError):
    """Error thrown when a provider action is denied because of permissions."""

    error_code = 18
    translation_key = "provider_permission_denied"


class ActionUnavailable(MusicAssistantError):
    """Error thrown when a action is denied because is is (temporary) unavailable/not possible."""

    error_code = 19
    translation_key = "action_unavailable"


class AuthenticationRequired(MusicAssistantError):
    """Error raised when authentication is required but not provided."""

    error_code = 20
    translation_key = "authentication_required"


class AuthenticationFailed(MusicAssistantError):
    """Error raised when authentication credentials are invalid."""

    error_code = 21
    translation_key = "authentication_failed"


class InsufficientPermissions(MusicAssistantError):
    """Error raised when user lacks required permissions for an action."""

    error_code = 22
    translation_key = "insufficient_permissions"


class InvalidToken(MusicAssistantError):
    """Error raised when an access token is invalid or expired."""

    error_code = 23
    translation_key = "invalid_token"


class ResourceBusyError(MusicAssistantError):
    """
    Raised when an exclusive resource is already in use.

    Used by providers when a resource that only allows a single
    concurrent consumer (e.g. an exclusive AudioSource, a hardware
    bridge, or any other single-stream media item) is requested
    while it is already in use elsewhere.
    """

    error_code = 24
    translation_key = "resource_busy"


class RateLimited(ResourceTemporarilyUnavailable):
    """
    Error thrown when a provider is rate-limiting us (HTTP 429).

    Unlike the base class, ``backoff_time`` (a server ``Retry-After``) is treated
    as a floor rather than a target: the retry helper backs off exponentially above it.
    """

    error_code = 25
    translation_key = "rate_limited"


class UnsupportedSystemError(SetupFailedError):
    """
    Raised when the host does not meet a provider's minimum requirements.

    Subclass of SetupFailedError so existing setup handling still applies, but it
    marks a permanent condition (RAM, CPU cores, CPU capability) that will not
    resolve at runtime, so the provider load must not be retried.
    """

    error_code = 26
    translation_key = "unsupported_system"
