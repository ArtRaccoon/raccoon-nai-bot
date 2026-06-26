"""NovelAI metadata parsing and presentation helpers."""

import html
import json
import re
import struct
import zlib

from app.nai.settings_registry import COMPARE_FIELDS, NAI_SETTINGS_REGISTRY, metadata_value, nested_get


def _png_text_chunks(data: bytes) -> list[str]:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return []
    texts: list[str] = []
    pos = 8
    while pos + 12 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        chunk_start = pos + 8
        chunk_end = chunk_start + length
        crc_end = chunk_end + 4
        if chunk_end > len(data) or crc_end > len(data):
            break
        chunk = data[chunk_start:chunk_end]
        if kind == b"tEXt":
            try:
                texts.append(chunk.decode("latin-1"))
            except UnicodeDecodeError:
                pass
        elif kind == b"iTXt":
            parts = chunk.split(b"\x00", 5)
            if len(parts) == 6:
                compressed_flag = parts[1]
                text_bytes = parts[5]
                if compressed_flag == b"\x01":
                    try:
                        text_bytes = zlib.decompress(text_bytes)
                    except zlib.error:
                        text_bytes = b""
                if text_bytes:
                    try:
                        texts.append(text_bytes.decode("utf-8"))
                    except UnicodeDecodeError:
                        pass
        elif kind == b"zTXt":
            parts = chunk.split(b"\x00", 1)
            if len(parts) == 2:
                try:
                    texts.append(zlib.decompress(parts[1][1:]).decode("latin-1"))
                except (zlib.error, UnicodeDecodeError):
                    pass
        pos = crc_end
        if kind == b"IEND":
            break
    return texts


def parse_nai_metadata(data: bytes) -> dict:
    texts = _png_text_chunks(data)
    blob = "\n".join(t for t in texts if t)
    found = {}
    candidates = []
    for start, ch in enumerate(blob):
        if ch != "{":
            continue
        depth = 0
        for pos in range(start, min(len(blob), start + 200_000)):
            if blob[pos] == "{":
                depth += 1
            elif blob[pos] == "}":
                depth -= 1
                if depth == 0:
                    candidate = blob[start:pos + 1]
                    if re.search(r"prompt|uc|sampler|seed|steps|scale|width|height", candidate, re.I):
                        candidates.append(candidate)
                    break
    for candidate in candidates:
        try:
            obj = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            found.update(obj)
            params = obj.get("parameters")
            if isinstance(params, dict):
                found.update(params)
    aliases = {
        "prompt": ["prompt", "Description"],
    }
    for field in NAI_SETTINGS_REGISTRY:
        aliases.setdefault(field.key, list(field.metadata_keys))
    meta = {}
    for target, keys in aliases.items():
        for key in keys:
            if key in found and found[key] not in ("", None):
                meta[target] = found[key]
                break
    for target, pattern in {
        "prompt": r"(?:prompt|description)[:=]\s*([^\n\r]+)",
        "negative_prompt": r"(?:negative prompt|uc|undesired content)[:=]\s*([^\n\r]+)",
        "model": r"model[:=]\s*([^\n\r,]+)",
        "sampler": r"sampler[:=]\s*([^\n\r,]+)",
    }.items():
        if target not in meta:
            m = re.search(pattern, blob, re.I)
            if m:
                meta[target] = m.group(1).strip()
    for target, pattern in {
        "width": r"width[:=]\s*(\d+)",
        "height": r"height[:=]\s*(\d+)",
        "steps": r"steps[:=]\s*(\d+)",
        "scale": r"(?:scale|guidance)[:=]\s*([0-9.]+)",
        "cfg_rescale": r"(?:cfg_rescale|cfg rescale)[:=]\s*([0-9.]+)",
        "seed": r"seed[:=]\s*(\d+)",
    }.items():
        if target not in meta:
            m = re.search(pattern, blob, re.I)
            if m:
                meta[target] = m.group(1)
    return meta


def metadata_summary(meta: dict) -> str:
    if not meta:
        return "📭 NovelAI metadata не найдена. Можно попробовать отправить оригинальный PNG/WebP/JPEG как файл."
    labels = {"prompt": "Prompt", **{field.key: field.label for field in NAI_SETTINGS_REGISTRY}}
    lines = ["📦 <b>Нашла metadata</b>"]
    for key, label in labels.items():
        if key in meta:
            lines.append(f"<b>{label}:</b> <code>{html.escape(str(meta[key])[:900])}</code>")
    return "\n".join(lines)


def metadata_settings_summary(meta: dict) -> str:
    if not meta:
        return "📭 Metadata settings не найдены."
    keys = [field.key for field in NAI_SETTINGS_REGISTRY] + ["params_version"]
    lines = ["📋 <b>Настройки metadata</b>"]
    for key in keys:
        if key in meta:
            lines.append(f"<b>{html.escape(key)}:</b> <code>{html.escape(str(meta[key])[:900])}</code>")
    return "\n".join(lines)


_METADATA_ALIASES = {field.key: field.metadata_keys for field in NAI_SETTINGS_REGISTRY}


def _payload_compare_value(payload: dict, field: str):
    if field == "model":
        return payload.get("model")
    if field == "action":
        return payload.get("action")
    parameters = payload.get("parameters", {}) if isinstance(payload, dict) else {}
    return nested_get(parameters, field)


def _metadata_compare_value(meta: dict, field: str):
    for registry_field in NAI_SETTINGS_REGISTRY:
        compare_path = registry_field.payload_path.removeprefix("parameters.")
        if field in {registry_field.key, compare_path}:
            return metadata_value(meta, registry_field)
    value = nested_get(meta, field) if "." in field else meta.get(field)
    return value


def _norm_compare_value(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value)
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    try:
        return float(text)
    except ValueError:
        return text


def _compare_status(site_value, bot_value) -> str:
    if site_value is None and bot_value is None:
        return "—"
    if site_value is None:
        return "⚠️ missing on website"
    if bot_value is None:
        return "❌ missing in bot"
    return "✅" if _norm_compare_value(site_value) == _norm_compare_value(bot_value) else "❌"


def _format_compare_value(value) -> str:
    if value is None:
        return "—"
    text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
    return text[:77] + "…" if len(text) > 80 else text

def nai_compare_summary_text(meta: dict, payload: dict) -> str:
    rows = ["field | website metadata | bot payload | status"]
    for field in COMPARE_FIELDS:
        rows.append(f"{field} | {_format_compare_value(_metadata_compare_value(meta, field))} | {_format_compare_value(_payload_compare_value(payload, field))} | {_compare_status(_metadata_compare_value(meta, field), _payload_compare_value(payload, field))}")
    return "⚖️ <b>NovelAI website-vs-bot payload compare</b>\n<pre>" + html.escape("\n".join(rows)) + "</pre>"
