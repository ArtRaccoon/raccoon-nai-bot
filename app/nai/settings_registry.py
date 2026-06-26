"""Registry of supported NovelAI website image settings.

The registry is the single place that knows how website metadata keys map to bot
settings and payload paths. It deliberately contains no credentials and must never
include NOVELAI_TOKEN or Authorization-like fields.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from config_defaults import MODELS, NOISE_SCHEDULES, SAMPLERS, UC_PRESETS

Caster = Callable[[Any], Any]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _int(value: Any) -> int:
    return int(float(str(value).strip()))


def _float(value: Any) -> float:
    return float(str(value).strip().replace(",", "."))


def _str(value: Any) -> str:
    return str(value)


def _model_name(value: Any) -> str:
    text = str(value)
    for name, model_id in MODELS.items():
        if text in {name, model_id}:
            return name
    raise ValueError(f"Unsupported NovelAI model: {text}")


def _choice(choices: list[str] | tuple[str, ...]) -> Caster:
    def cast(value: Any) -> str:
        text = str(value)
        if text not in choices:
            raise ValueError(f"Unsupported value: {text}")
        return text
    return cast


@dataclass(frozen=True)
class NaiSettingField:
    key: str
    label: str
    payload_path: str
    user_setting: str | None = None
    aliases: tuple[str, ...] = ()
    cast: Caster = _str
    basic_safe: bool = False
    admin_only: bool = True
    menu_section: str = "site_clone"

    @property
    def metadata_keys(self) -> tuple[str, ...]:
        return (self.key, *self.aliases)


NAI_SETTINGS_REGISTRY: tuple[NaiSettingField, ...] = (
    NaiSettingField("model", "Model", "model", "model_name", ("Model",), _model_name, basic_safe=True, admin_only=False, menu_section="basic"),
    NaiSettingField("width", "Width", "parameters.width", "width", (), _int, basic_safe=True, admin_only=False, menu_section="basic"),
    NaiSettingField("height", "Height", "parameters.height", "height", (), _int, basic_safe=True, admin_only=False, menu_section="basic"),
    NaiSettingField("steps", "Steps", "parameters.steps", "steps", (), _int, basic_safe=True, admin_only=False, menu_section="basic"),
    NaiSettingField("scale", "Guidance", "parameters.scale", "scale", ("guidance",), _float, basic_safe=True, admin_only=False, menu_section="basic"),
    NaiSettingField("cfg_rescale", "CFG rescale", "parameters.cfg_rescale", "cfg_rescale", ("cfgRescale",), _float),
    NaiSettingField("sampler", "Sampler", "parameters.sampler", "sampler", (), _choice(SAMPLERS)),
    NaiSettingField("noise_schedule", "Noise schedule", "parameters.noise_schedule", "noise_schedule", ("noiseSchedule",), _choice(NOISE_SCHEDULES)),
    NaiSettingField("seed", "Seed", "parameters.seed", "seed", (), _int, basic_safe=True, admin_only=False, menu_section="basic"),
    NaiSettingField("n_samples", "Samples", "parameters.n_samples", "n_samples", ("nSamples",), _int),
    NaiSettingField("ucPreset", "UC preset id", "parameters.ucPreset", "uc_preset_id", ("uc_preset_id",), _int),
    NaiSettingField("uc_preset", "UC preset", "parameters.ucPreset", "uc_preset", ("ucPresetName",), _choice(tuple(UC_PRESETS))),
    NaiSettingField("qualityToggle", "Quality toggle", "parameters.qualityToggle", "add_quality_tags", ("quality_toggle",), _bool),
    NaiSettingField("dynamic_thresholding", "Dynamic thresholding", "parameters.dynamic_thresholding", "dynamic_thresholding", ("dynamicThresholding",), _bool),
    NaiSettingField("variety_plus", "Variety+", "parameters.variety_plus", "variety_plus", ("varietyPlus",), _bool),
    NaiSettingField("negative_prompt", "Negative prompt", "parameters.negative_prompt", "negative_prompt", ("negative prompt", "uc", "Undesired Content"), _str, basic_safe=True, admin_only=False, menu_section="basic"),
    NaiSettingField("v4_prompt", "V4 prompt", "parameters.v4_prompt", "v4_prompt", (), lambda v: v),
    NaiSettingField("v4_negative_prompt", "V4 negative prompt", "parameters.v4_negative_prompt", "v4_negative_prompt", (), lambda v: v),
    NaiSettingField("use_coords", "V4 use coords", "parameters.v4_prompt.use_coords", "use_coords", ("v4_prompt.use_coords",), _bool),
    NaiSettingField("use_order", "V4 use order", "parameters.v4_prompt.use_order", "use_order", ("v4_prompt.use_order",), _bool),
    NaiSettingField("legacy_uc", "V4 legacy UC", "parameters.v4_negative_prompt.legacy_uc", "legacy_uc", ("v4_negative_prompt.legacy_uc",), _bool),
    NaiSettingField("character_captions", "Character captions", "parameters.v4_prompt.caption.char_captions", "character_captions", ("char_captions",), lambda v: v),
    NaiSettingField("negative_character_captions", "Negative character captions", "parameters.v4_negative_prompt.caption.char_captions", "negative_character_captions", (), lambda v: v),
    NaiSettingField("strength", "Img2Img strength", "parameters.strength", "img2img_strength", ("img2img_strength",), _float),
    NaiSettingField("noise", "Img2Img noise", "parameters.noise", "img2img_noise", ("img2img_noise",), _float),
    NaiSettingField("mask", "Infill mask", "parameters.mask", "infill_mask", ("infill_mask",), _str),
    NaiSettingField("action", "Action", "action", "nai_action", (), _str),
    NaiSettingField("upscale", "Upscale action", "action", "upscale_action", (), _bool),
    NaiSettingField("variation", "Variation action", "action", "variation_action", (), _bool),
)

REGISTRY_BY_KEY = {field.key: field for field in NAI_SETTINGS_REGISTRY}
COMPARE_FIELDS = tuple(dict.fromkeys(field.payload_path.removeprefix("parameters.") for field in NAI_SETTINGS_REGISTRY if field.key not in {"upscale", "variation"}))
BASIC_MENU_FIELDS = tuple(field for field in NAI_SETTINGS_REGISTRY if field.menu_section == "basic" and field.basic_safe)
ADMIN_SITE_CLONE_FIELDS = tuple(field for field in NAI_SETTINGS_REGISTRY if field.menu_section == "site_clone")


def nested_get(data: dict, dotted: str):
    current: Any = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def nested_set(data: dict, dotted: str, value: Any) -> None:
    current = data
    parts = dotted.split(".")
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value


def metadata_value(meta: dict, field: NaiSettingField):
    for key in field.metadata_keys:
        value = nested_get(meta, key) if "." in key else meta.get(key)
        if value not in (None, ""):
            return value
    return None


def settings_updates_from_metadata(meta: dict, *, include_admin: bool = True) -> dict:
    updates = {}
    for field in NAI_SETTINGS_REGISTRY:
        if not include_admin and not field.basic_safe:
            continue
        if not field.user_setting:
            continue
        value = metadata_value(meta, field)
        if value in (None, ""):
            continue
        try:
            updates[field.user_setting] = field.cast(value)
        except (TypeError, ValueError):
            continue
    return updates
