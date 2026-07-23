"""Model for a step of a running setup flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mashumaro import DataClassDictMixin, field_options

from .config_entries import ConfigEntry
from .enums import FlowStepType
from .translations import resolve_translation


@dataclass(kw_only=True)
class SetupFlowStep(DataClassDictMixin):
    """
    Model for a single step of a running setup flow.

    A setup flow is the interactive, multi-step process (credentials, OAuth, pairing, ...) that
    creates or reconfigures a provider or player. Each step is serialized to the API client, which
    renders it based on its type and posts the user input back to advance the flow.
    """

    # flow_id: identifier of the running flow this step belongs to
    flow_id: str
    # step_id: stable slug identifying this step; also the i18n key segment
    step_id: str
    type: FlowStepType
    # title: display title for the step, resolved from the translations at serialization
    title: str | None = None
    # description: extended description for the step, resolved from the translations
    # at serialization
    description: str | None = None
    # entries [FORM]: the config entries that make up the form fields
    entries: list[ConfigEntry] = field(default_factory=list)
    # errors [FORM]: field-key (or "base") -> error slug/message, resolved from the translations
    errors: dict[str, str] = field(default_factory=dict)
    # last_step [FORM]: hint for the submit button label (final step vs. continue)
    last_step: bool | None = None
    # url [EXTERNAL]: url the user must open (e.g. an OAuth authorize url)
    url: str | None = None
    # progress_text [PROGRESS]: status slug/message, resolved from the translations at serialization
    progress_text: str | None = None
    # progress [PROGRESS]: optional completion fraction between 0 and 1
    progress: float | None = None
    # image [PROGRESS]: optional data-URI illustration (e.g. a pairing QR code)
    image: str | None = None
    # expires_at [FORM/EXTERNAL/PROGRESS]: UTC epoch deadline for this step; the client countdown
    # is cosmetic, the server enforces the deadline
    expires_at: float | None = None
    # result [FINISH]: reference to the created/updated object (e.g. {"instance_id": ...})
    result: dict[str, str] | None = None
    # reason [ABORT]: reason slug/message, resolved from the translations at serialization
    reason: str | None = None
    # translation_owner: the namespace ("provider.<domain>") this step's strings are resolved
    # under; stamped by the server when the step is served. Not serialized.
    translation_owner: str | None = field(
        default=None, metadata=field_options(serialize="omit"), repr=False
    )
    # translation_params: optional positional arguments for the {0}/{1} placeholders in this
    # step's title/description translation, provided by the implementer. Not serialized.
    translation_params: list[str] | None = field(
        default=None, metadata=field_options(serialize="omit"), repr=False
    )

    def __post_serialize__(self, d: dict[str, Any]) -> dict[str, Any]:
        """
        Localize human-readable fields from the translations for the connection locale.

        Resolves title/description (setup_flow.<step_id>.*), progress_text, the abort reason
        (setup_flow.abort.<reason>) and each error value (errors.<slug>) under this step's owner
        namespace. No-op when nothing matches, so the in-code values/slugs are kept. The
        translation machinery fields are not serialized.
        """
        owner = self.translation_owner
        title = resolve_translation(
            f"setup_flow.{self.step_id}.title", owner=owner, params=self.translation_params
        )
        if title is not None:
            d["title"] = title
        description = resolve_translation(
            f"setup_flow.{self.step_id}.description", owner=owner, params=self.translation_params
        )
        if description is not None:
            d["description"] = description
        if self.progress_text is not None:
            progress_text = resolve_translation(
                f"setup_flow.{self.step_id}.progress_text", owner=owner
            )
            if progress_text is not None:
                d["progress_text"] = progress_text
        if self.reason is not None:
            reason = resolve_translation(f"setup_flow.abort.{self.reason}", owner=owner)
            if reason is not None:
                d["reason"] = reason
        for field_key, slug in self.errors.items():
            localized = resolve_translation(f"errors.{slug}", owner=owner)
            if localized is not None:
                d["errors"][field_key] = localized
        return d
