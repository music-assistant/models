"""Tests for the SetupFlowStep model and the FlowStepType enum."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from music_assistant_models.config_entries import ConfigEntry
from music_assistant_models.enums import ConfigEntryType, FlowStepType
from music_assistant_models.setup_flow import SetupFlowStep
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
    """An EXTERNAL step carries the url to open and an optional deadline."""
    step = SetupFlowStep(
        flow_id="f",
        step_id="oauth",
        type=FlowStepType.EXTERNAL,
        url="https://example.test/authorize",
        expires_at=1234.5,
    )
    d = step.to_dict()
    assert d["type"] == "external"
    assert d["url"] == "https://example.test/authorize"
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
