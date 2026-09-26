"""Tests for the SetupFlowStep model and the FlowStepType enum."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from music_assistant_models.config_entries import ConfigEntry
from music_assistant_models.enums import ConfigEntryType, FlowStepType
from music_assistant_models.setup_flow import SetupFlowStep, TranslationRef
from music_assistant_models.translations import TRANSLATION_RESOLVER


@contextmanager
def _resolver_active(catalog: dict[str, str]) -> Iterator[None]:
    """Bind a fake catalog resolver for the duration of the block."""

    def resolve(key: str, owner: str | None = None, params: list[Any] | None = None) -> str | None:
        for candidate in [f"{owner}.{key}", key] if owner else [key]:
            if (value := catalog.get(candidate)) is not None:
                return value.format(*params) if params else value
        return None

    token = TRANSLATION_RESOLVER.set(resolve)
    try:
        yield
    finally:
        TRANSLATION_RESOLVER.reset(token)


def test_flow_step_type_unknown_fallback() -> None:
    """A known FlowStepType value resolves; an unknown value falls back to UNKNOWN."""
    assert FlowStepType("form") is FlowStepType.FORM
    assert FlowStepType("does-not-exist") is FlowStepType.UNKNOWN


def test_translation_ref_is_data_only_with_independent_args_defaults() -> None:
    """TranslationRef groups metadata and does not share its default argument list."""
    first = TranslationRef(key="first")
    second = TranslationRef(key="second")
    first.args.append("value")

    assert first.to_dict() == {"key": "first", "args": ["value"], "owner": None}
    assert second.args == []
    assert second.owner is None


def test_form_step_shape() -> None:
    """A FORM step serializes its entries, errors and submit hint; machinery is omitted."""
    step = SetupFlowStep(
        flow_id="flow-1",
        step_id="credentials",
        type=FlowStepType.FORM,
        title="Credentials",
        entries=[ConfigEntry(key="username", type=ConfigEntryType.STRING)],
        errors={"base": "invalid_auth"},
        last_step=True,
        translation_owner="provider.demo",
        translation_params=["x"],
    )
    d = step.to_dict()
    assert d["flow_id"] == "flow-1"
    assert d["step_id"] == "credentials"
    assert d["type"] == "form"
    assert d["title"] == "Credentials"
    assert d["entries"][0]["key"] == "username"
    assert d["errors"] == {"base": "invalid_auth"}
    assert d["last_step"] is True
    # translation machinery is never serialized
    assert "translation_owner" not in d
    assert "translation_params" not in d


def test_external_step_shape() -> None:
    """An EXTERNAL step carries the url to open, copyable text and an optional deadline."""
    step = SetupFlowStep(
        flow_id="f",
        step_id="oauth",
        type=FlowStepType.EXTERNAL,
        url="https://example.test/authorize",
        copy_text="123456",
        expires_at=1234.5,
    )
    d = step.to_dict()
    assert d["type"] == "external"
    assert d["url"] == "https://example.test/authorize"
    assert d["copy_text"] == "123456"
    assert d["expires_at"] == 1234.5


def test_progress_step_shape() -> None:
    """A PROGRESS step carries status text, an optional fraction and an optional image."""
    step = SetupFlowStep(
        flow_id="f",
        step_id="working",
        type=FlowStepType.PROGRESS,
        progress_text="Working...",
        progress=0.25,
        image="data:image/png;base64,AAAA",
    )
    d = step.to_dict()
    assert d["type"] == "progress"
    assert d["progress_text"] == "Working..."
    assert d["progress"] == 0.25
    assert d["image"] == "data:image/png;base64,AAAA"


def test_finish_step_shape() -> None:
    """A FINISH step references the created/updated object via result."""
    step = SetupFlowStep(
        flow_id="f", step_id="done", type=FlowStepType.FINISH, result={"instance_id": "demo--1"}
    )
    d = step.to_dict()
    assert d["type"] == "finish"
    assert d["result"] == {"instance_id": "demo--1"}


def test_abort_step_shape() -> None:
    """An ABORT step carries a reason slug."""
    step = SetupFlowStep(
        flow_id="f", step_id="failed", type=FlowStepType.ABORT, reason="already_configured"
    )
    d = step.to_dict()
    assert d["type"] == "abort"
    assert d["reason"] == "already_configured"


def test_title_and_description_resolve_owner_first() -> None:
    """title/description resolve under setup_flow.<step_id>.*, owner-first then common."""
    catalog = {
        "setup_flow.credentials.title": "Inloggegevens",
        "provider.demo.setup_flow.credentials.title": "Demo-inloggegevens",
        "setup_flow.credentials.description": "Voer je gegevens in.",
    }
    owned = SetupFlowStep(
        flow_id="f",
        step_id="credentials",
        type=FlowStepType.FORM,
        title="Credentials",
        description="Enter your details.",
        translation_owner="provider.demo",
    )
    with _resolver_active(catalog):
        d = owned.to_dict()
    # owner-specific title wins; the description has no owner key and falls back to common
    assert d["title"] == "Demo-inloggegevens"
    assert d["description"] == "Voer je gegevens in."
    # the same step without an owner hits the common title
    common = SetupFlowStep(
        flow_id="f", step_id="credentials", type=FlowStepType.FORM, title="Credentials"
    )
    with _resolver_active(catalog):
        assert common.to_dict()["title"] == "Inloggegevens"


def test_unresolved_title_keeps_in_code_value() -> None:
    """When nothing matches, the in-code title is kept (no-op resolution)."""
    step = SetupFlowStep(
        flow_id="f", step_id="credentials", type=FlowStepType.FORM, title="Credentials"
    )
    # no resolver bound
    assert step.to_dict()["title"] == "Credentials"
    # resolver bound but nothing matches for this step
    with _resolver_active({"setup_flow.other.title": "x"}):
        assert step.to_dict()["title"] == "Credentials"


def test_title_interpolates_translation_params() -> None:
    """translation_params fill positional placeholders in the resolved title."""
    catalog = {"setup_flow.pairing.title": "Koppel met {0}"}
    step = SetupFlowStep(
        flow_id="f",
        step_id="pairing",
        type=FlowStepType.FORM,
        title="Pair with Speaker",
        translation_params=["Speaker"],
    )
    with _resolver_active(catalog):
        assert step.to_dict()["title"] == "Koppel met Speaker"


def test_progress_text_resolves() -> None:
    """progress_text resolves under setup_flow.<step_id>.progress_text."""
    catalog = {"setup_flow.working.progress_text": "Bezig met verbinden..."}
    step = SetupFlowStep(
        flow_id="f", step_id="working", type=FlowStepType.PROGRESS, progress_text="Connecting..."
    )
    with _resolver_active(catalog):
        assert step.to_dict()["progress_text"] == "Bezig met verbinden..."


def test_progress_text_not_injected_when_unset() -> None:
    """A step without progress_text never gains one, even when a translation key exists."""
    catalog = {"provider.demo.setup_flow.credentials.progress_text": "Bezig..."}
    step = SetupFlowStep(
        flow_id="f",
        step_id="credentials",
        type=FlowStepType.FORM,
        translation_owner="provider.demo",
    )
    with _resolver_active(catalog):
        assert step.to_dict()["progress_text"] is None


def test_abort_reason_resolves_by_value_and_keeps_slug_when_unresolved() -> None:
    """The abort reason resolves setup_flow.abort.<reason> owner-first; an unknown slug is kept."""
    catalog = {
        "setup_flow.abort.already_configured": "Al geconfigureerd.",
        "provider.demo.setup_flow.abort.already_configured": "Demo: al geconfigureerd.",
    }
    # a provider that owns the reason string resolves its own before common
    owned = SetupFlowStep(
        flow_id="f",
        step_id="x",
        type=FlowStepType.ABORT,
        reason="already_configured",
        translation_owner="provider.demo",
    )
    with _resolver_active(catalog):
        assert owned.to_dict()["reason"] == "Demo: al geconfigureerd."
    # without an owner the common string is used
    common = SetupFlowStep(
        flow_id="f", step_id="x", type=FlowStepType.ABORT, reason="already_configured"
    )
    with _resolver_active(catalog):
        assert common.to_dict()["reason"] == "Al geconfigureerd."
    # an unknown reason keeps its slug verbatim
    unknown = SetupFlowStep(flow_id="f", step_id="x", type=FlowStepType.ABORT, reason="mystery")
    with _resolver_active(catalog):
        assert unknown.to_dict()["reason"] == "mystery"


def test_errors_resolve_owner_first_and_keep_slug_when_unresolved() -> None:
    """Each error value resolves errors.<slug> owner-first; an unknown slug is kept as-is."""
    catalog = {
        "errors.invalid_auth": "Ongeldige login.",
        "provider.demo.errors.invalid_auth": "Demo: ongeldige login.",
    }
    owned = SetupFlowStep(
        flow_id="f",
        step_id="credentials",
        type=FlowStepType.FORM,
        errors={"base": "invalid_auth", "pin": "too_short"},
        translation_owner="provider.demo",
    )
    with _resolver_active(catalog):
        errors = owned.to_dict()["errors"]
    # provider-owned string wins for the resolvable slug
    assert errors["base"] == "Demo: ongeldige login."
    # the unresolved slug is kept verbatim
    assert errors["pin"] == "too_short"
    # without an owner the common string is used
    common = SetupFlowStep(
        flow_id="f",
        step_id="credentials",
        type=FlowStepType.FORM,
        errors={"base": "invalid_auth"},
    )
    with _resolver_active(catalog):
        assert common.to_dict()["errors"]["base"] == "Ongeldige login."


def test_error_translation_metadata_is_field_specific_and_omitted() -> None:
    """Each error can use its own key, owner and arguments without changing stored errors."""
    errors = {
        "username": "raw_username_error",
        "password": "raw_password_error",
        "base": "raw_base_error",
    }
    step = SetupFlowStep(
        flow_id="f",
        step_id="credentials",
        type=FlowStepType.FORM,
        errors=errors,
        translation_owner="provider.default",
        error_translations={
            "username": TranslationRef(key="username_required", args=["Alice"]),
            "password": TranslationRef(
                key="password_invalid", args=["Bob", 3], owner="provider.special"
            ),
        },
    )
    catalog = {
        "provider.default.errors.username_required": "Username for {0} is required",
        "provider.special.errors.password_invalid": "Password for {0} has {1} errors",
        "provider.default.errors.raw_base_error": "Base error",
    }

    with _resolver_active(catalog):
        serialized = step.to_dict()

    assert serialized["errors"] == {
        "username": "Username for Alice is required",
        "password": "Password for Bob has 3 errors",
        "base": "Base error",
    }
    assert step.errors == errors
    assert "error_translations" not in serialized


def test_error_translation_resolver_binding_can_change_for_the_same_step() -> None:
    """The same step resolves errors using whichever locale resolver is currently bound."""
    step = SetupFlowStep(
        flow_id="f",
        step_id="credentials",
        type=FlowStepType.FORM,
        errors={"base": "invalid_auth"},
        error_translations={"base": TranslationRef(key="login_failed")},
    )

    with _resolver_active({"errors.login_failed": "Invalid login."}):
        assert step.to_dict()["errors"]["base"] == "Invalid login."
    with _resolver_active({"errors.login_failed": "Ongeldige login."}):
        assert step.to_dict()["errors"]["base"] == "Ongeldige login."


def test_error_translation_missing_key_keeps_original_slug() -> None:
    """An unknown per-field translation key leaves the original stored error value intact."""
    errors = {"base": "raw_error"}
    step = SetupFlowStep(
        flow_id="f",
        step_id="credentials",
        type=FlowStepType.FORM,
        errors=errors,
        error_translations={"base": TranslationRef(key="missing_translation")},
    )

    with _resolver_active({}):
        serialized = step.to_dict()

    assert serialized["errors"] == errors
    assert step.errors == errors


def test_abort_reason_translation_metadata_localizes_without_mutation() -> None:
    """An ABORT resolves an error key per locale without changing the step."""
    step = SetupFlowStep(
        flow_id="f",
        step_id="failed",
        type=FlowStepType.ABORT,
        reason="raw_reason",
        translation_owner="provider.default",
        reason_translation=TranslationRef(key="connection_failed", args=["Speaker", 2]),
    )

    with _resolver_active(
        {"provider.default.errors.connection_failed": "Verbinding met {0} mislukte ({1})."}
    ):
        dutch = step.to_dict()
    with _resolver_active(
        {"provider.default.errors.connection_failed": "Connection to {0} failed ({1})."}
    ):
        english = step.to_dict()

    assert dutch["reason"] == "Verbinding met Speaker mislukte (2)."
    assert english["reason"] == "Connection to Speaker failed (2)."
    assert step.reason == "raw_reason"
    assert step.reason_translation == TranslationRef(key="connection_failed", args=["Speaker", 2])


def test_abort_reason_translation_owner_overrides_step_owner() -> None:
    """An ABORT reason can use an owner different from the step's translation owner."""
    step = SetupFlowStep(
        flow_id="f",
        step_id="failed",
        type=FlowStepType.ABORT,
        reason="raw_reason",
        translation_owner="provider.step",
        reason_translation=TranslationRef(key="connection_failed", owner="provider.reason"),
    )
    catalog = {
        "provider.reason.errors.connection_failed": "Reason owner",
        "provider.step.errors.connection_failed": "Step owner",
    }

    with _resolver_active(catalog):
        assert step.to_dict()["reason"] == "Reason owner"


def test_abort_reason_translation_missing_key_keeps_reason() -> None:
    """An unresolved explicit ABORT translation key leaves the original reason intact."""
    step = SetupFlowStep(
        flow_id="f",
        step_id="failed",
        type=FlowStepType.ABORT,
        reason="raw_reason",
        reason_translation=TranslationRef(key="missing_reason"),
    )

    with _resolver_active({}):
        assert step.to_dict()["reason"] == "raw_reason"


def test_abort_reason_translation_metadata_is_omitted() -> None:
    """ABORT translation metadata is internal and never appears in serialized output."""
    step = SetupFlowStep(
        flow_id="f",
        step_id="failed",
        type=FlowStepType.ABORT,
        reason="raw_reason",
        reason_translation=TranslationRef(
            key="connection_failed", args=["Speaker"], owner="provider.demo"
        ),
    )

    serialized = step.to_dict()

    assert serialized["reason"] == "raw_reason"
    assert "reason_translation" not in serialized


def test_abort_reason_without_translation_key_keeps_legacy_slug_resolution() -> None:
    """Without explicit metadata, ABORT continues using setup_flow.abort.<reason>."""
    step = SetupFlowStep(
        flow_id="f",
        step_id="failed",
        type=FlowStepType.ABORT,
        reason="already_configured",
    )

    with _resolver_active({"setup_flow.abort.already_configured": "Already configured."}):
        assert step.to_dict()["reason"] == "Already configured."
