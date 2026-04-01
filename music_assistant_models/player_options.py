"""Pre-defined PlayerOptions."""

from dataclasses import dataclass

from .player import PlayerOption


@dataclass(kw_only=True)
class TranslatedPlayerOption(PlayerOption):
    """TranslatedPlayerOption."""

    _translation_key: str = ""

    def __post_init__(self) -> None:
        """Post Init."""
        if self.translation_key is not None:
            raise ValueError("Do not set the translation key on a translated player option.")

        if not self._translation_key:
            raise ValueError("_translation_key must be set.")

        self.translation_key = f"player_options.{self._translation_key}"

        super().__post_init__()


@dataclass(kw_only=True)
class PlayerOptionAdaptiveDrc(TranslatedPlayerOption):
    """PlayerOptionAdaptiveDrc."""

    _translation_key: str = "adaptive_drc"


@dataclass(kw_only=True)
class PlayerOptionBass(TranslatedPlayerOption):
    """PlayerOptionBass."""

    _translation_key: str = "bass"


@dataclass(kw_only=True)
class PlayerOptionBassExtension(TranslatedPlayerOption):
    """PlayerOptionBassExtension."""

    _translation_key: str = "bass_extension"


@dataclass(kw_only=True)
class PlayerOptionClearVoice(TranslatedPlayerOption):
    """PlayerOptionClearVoice."""

    _translation_key: str = "clear_voice"


@dataclass(kw_only=True)
class PlayerOptionDtsDialogueControl(TranslatedPlayerOption):
    """PlayerOptionDtsDialogueControl."""

    _translation_key: str = "dts_dialogue_control"


@dataclass(kw_only=True)
class PlayerOptionDialogueLevel(TranslatedPlayerOption):
    """PlayerOptionDialogueLevel."""

    _translation_key: str = "dialogue_level"


@dataclass(kw_only=True)
class PlayerOptionDialogueLift(TranslatedPlayerOption):
    """PlayerOptionDialogueLift."""

    _translation_key: str = "dialogue_lift"


@dataclass(kw_only=True)
class PlayerOptionDimmer(TranslatedPlayerOption):
    """PlayerOptionDimmer."""

    _translation_key: str = "dimmer"


@dataclass(kw_only=True)
class PlayerOptionEnhancer(TranslatedPlayerOption):
    """PlayerOptionEnhancer."""

    _translation_key: str = "enhancer"


@dataclass(kw_only=True)
class PlayerOptionEqualizerHigh(TranslatedPlayerOption):
    """PlayerOptionEqualizerHigh."""

    _translation_key: str = "equalizer_high"


@dataclass(kw_only=True)
class PlayerOptionEqualizerLow(TranslatedPlayerOption):
    """PlayerOptionEqualizerLow."""

    _translation_key: str = "equalizer_low"


@dataclass(kw_only=True)
class PlayerOptionEqualizerMid(TranslatedPlayerOption):
    """PlayerOptionEqualizerMid."""

    _translation_key: str = "equalizer_mid"


@dataclass(kw_only=True)
class PlayerOptionEqualizerMode(TranslatedPlayerOption):
    """PlayerOptionEqualizerMode."""

    _translation_key: str = "equalizer_mode"


@dataclass(kw_only=True)
class PlayerOptionExtraBass(TranslatedPlayerOption):
    """PlayerOptionExtraBass."""

    _translation_key: str = "extra_bass"


@dataclass(kw_only=True)
class PlayerOptionLinkAudioDelay(TranslatedPlayerOption):
    """PlayerOptionLinkAudioDelay."""

    _translation_key: str = "link_audio_delay"


@dataclass(kw_only=True)
class PlayerOptionLinkControl(TranslatedPlayerOption):
    """PlayerOptionLinkControl."""

    _translation_key: str = "link_control"


@dataclass(kw_only=True)
class PlayerOptionLinkAudioQuality(TranslatedPlayerOption):
    """PlayerOptionLinkAudioQuality."""

    _translation_key: str = "link_audio_quality"


@dataclass(kw_only=True)
class PlayerOptionPartyMode(TranslatedPlayerOption):
    """PlayerOptionPartyMode."""

    _translation_key: str = "party_mode"


@dataclass(kw_only=True)
class PlayerOptionPureDirect(TranslatedPlayerOption):
    """PlayerOptionPureDirect."""

    _translation_key: str = "pure_direct"


@dataclass(kw_only=True)
class PlayerOptionSleep(TranslatedPlayerOption):
    """PlayerOptionSleep."""

    _translation_key: str = "sleep"


@dataclass(kw_only=True)
class PlayerOptionSpeakerA(TranslatedPlayerOption):
    """PlayerOptionSpeakerA."""

    _translation_key: str = "speaker_a"


@dataclass(kw_only=True)
class PlayerOptionSpeakerB(TranslatedPlayerOption):
    """PlayerOptionSpeakerB."""

    _translation_key: str = "speaker_b"


@dataclass(kw_only=True)
class PlayerOptionSubwooferVolume(TranslatedPlayerOption):
    """PlayerOptionSubwooferVolume."""

    _translation_key: str = "subwoofer_volume"


@dataclass(kw_only=True)
class PlayerOptionSurround3D(TranslatedPlayerOption):
    """PlayerOptionSurround3D."""

    _translation_key: str = "surround_3d"


@dataclass(kw_only=True)
class PlayerOptionSurroundDecoderType(TranslatedPlayerOption):
    """PlayerOptionSurroundDecoderType."""

    _translation_key: str = "surround_decoder_type"


@dataclass(kw_only=True)
class PlayerOptionToneControlMode(TranslatedPlayerOption):
    """PlayerOptionToneControlMode."""

    _translation_key: str = "tone_control_mode"


@dataclass(kw_only=True)
class PlayerOptionTreble(TranslatedPlayerOption):
    """PlayerOptionTreble."""

    _translation_key: str = "treble"


TRANSLATED_PLAYER_OPTIONS = (
    PlayerOptionAdaptiveDrc,
    PlayerOptionBass,
    PlayerOptionBassExtension,
    PlayerOptionClearVoice,
    PlayerOptionDtsDialogueControl,
    PlayerOptionDialogueLevel,
    PlayerOptionDialogueLift,
    PlayerOptionDimmer,
    PlayerOptionEnhancer,
    PlayerOptionEqualizerHigh,
    PlayerOptionEqualizerLow,
    PlayerOptionEqualizerMid,
    PlayerOptionEqualizerMode,
    PlayerOptionExtraBass,
    PlayerOptionLinkAudioDelay,
    PlayerOptionLinkControl,
    PlayerOptionLinkAudioQuality,
    PlayerOptionPartyMode,
    PlayerOptionPureDirect,
    PlayerOptionSleep,
    PlayerOptionSpeakerA,
    PlayerOptionSpeakerB,
    PlayerOptionSubwooferVolume,
    PlayerOptionSurround3D,
    PlayerOptionSurroundDecoderType,
    PlayerOptionToneControlMode,
    PlayerOptionTreble,
)
