"""Reusable Telegram text builders."""

import html
from app.services.nai_client import payload_summary
from config_defaults import QUICK_PRESETS


PAID_PLACEHOLDER_TEXT = "✒️ Пополнить запас Чернил можно за Telegram Stars."
DAILY_LIMIT_TEXT = "🕯️ Бесплатные генерации на сегодня закончились.\n\nМожно дождаться завтрашнего сброса или пополнить запас Чернил."
GENERATION_STARTED_TEXT = "✨ Генерирую. Енот смешивает пиксели..."
PROMPT_EMPTY_TEXT = "🖼️ Черновик пока пуст. Пришли идею картинки обычным сообщением."
CANCEL_TEXT = "❌ Черновик очищен. Возвращаю в главное меню."
CLEAR_TEXT = "🧹 Черновик очищен. Можно прислать новую идею."
EDIT_PROMPT_TEXT = "✏️ Пришли новый текст — я обновлю черновик."


def cooldown_text(seconds: int) -> str:
    return f"⏳ Дай еноту пару секунд отдышаться.\nОсталось: {seconds}s"


def start_text(remaining: int | None = None, daily_limit: int = 0, is_admin: bool = False) -> str:
    return (
        "🦝 <b>Добро пожаловать в Raccoon NAI!</b>\n\n"
        "Создавайте изображения с помощью NovelAI.\n\n"
        "✍️ <b>Опишите желаемое изображение только на английском языке.</b>\n\n"
        "Например:\n\n"
        "<blockquote expandable>1girl, raccoon ears, fluffy striped tail, long messy black hair, "
        "glowing pink eyes with vertical pupils, pale skin, oversized black hoodie with violet accents, "
        "fingerless gloves, constellation tattoo on arm, ancient magical library, glowing books, "
        "floating runes, warm candlelight, cinematic lighting, masterpiece, best quality, highly detailed</blockquote>\n\n"
        "Не знаете, как писать промпты? Загляните в <b>📖 Обучение</b>. "
        "Там собраны основы промптинга, полезные теги и готовые примеры для NovelAI."
    )


def learning_text(section: str = "open") -> str:
    texts = {
        "open": "📖 <b>Обучение Raccoon NAI</b>\n\nВыберите раздел:",
        "first_steps": (
            "🌱 <b>Первые шаги</b>\n\n"
            "1. Опишите изображение на английском языке.\n"
            "2. Разделяйте теги запятыми.\n"
            "3. Сначала укажите персонажа, затем внешность, одежду, позу, фон, свет и стиль.\n"
            "4. Не делайте первый промпт слишком длинным.\n"
            "5. После генерации постепенно добавляйте или убирайте детали.\n\n"
            "Example:\n\n"
            "<blockquote>1girl, raccoon ears, black hair, pink eyes, dark hoodie, night city, cinematic lighting</blockquote>"
        ),
        "prompts": (
            "✍️ <b>Как писать промпты</b>\n\n"
            "Удобная структура:\n\n"
            "<blockquote>персонаж, внешность, одежда, поза, окружение, освещение, стиль, качество</blockquote>\n\n"
            "Example:\n\n"
            "<blockquote>1girl, raccoon ears, long black hair, glowing pink eyes, oversized hoodie, standing in an ancient library, warm candlelight, cinematic lighting, highly detailed</blockquote>\n\n"
            "• более важные теги обычно лучше ставить раньше\n"
            "• теги разделяются запятыми\n"
            "• избегайте противоречивых описаний"
        ),
        "character": (
            "👤 <b>Описание персонажа</b>\n\n"
            "Полезный порядок:\n\n"
            "- количество персонажей\n- пол и возрастная категория\n- волосы\n- глаза\n- особенности\n- одежда\n- эмоция\n- поза\n\n"
            "Example:\n\n"
            "<blockquote>1girl, adult, raccoon ears, fluffy striped tail, long messy black hair, glowing pink eyes, pale skin, black oversized hoodie, gentle mysterious expression</blockquote>"
        ),
        "style": (
            "🎨 <b>Стиль и атмосфера</b>\n\n"
            "Добавляйте:\n\n- место\n- время суток\n- источник света\n- настроение\n- художественную подачу\n\n"
            "Examples:\n\n"
            "<blockquote>ancient library, floating runes, warm candlelight, magical atmosphere</blockquote>\n\n"
            "<blockquote>neon city at night, rain, reflections, cinematic lighting, moody atmosphere</blockquote>"
        ),
        "mistakes": (
            "🚫 <b>Частые ошибки</b>\n\n"
            "- промпт написан на русском\n- слишком много противоречивых тегов\n- одновременно указаны разные цвета волос или глаз\n"
            "- смешаны несовместимые стили\n- важная деталь спрятана в самом конце длинного промпта\n"
            "- промпт состоит только из слов “masterpiece, best quality”\n\n"
            "Качество промпта определяет результат сильнее, чем количество красивых слов."
        ),
        "examples": (
            "🦝 <b>Готовые примеры</b>\n\n"
            "1. Aelita in library\n<blockquote expandable>1girl, raccoon ears, fluffy striped tail, long messy black hair, glowing pink eyes with vertical pupils, pale skin, oversized black hoodie with violet accents, fingerless gloves, constellation tattoo on arm, ancient magical library, glowing books, floating runes, warm candlelight, cinematic lighting, masterpiece, best quality, highly detailed</blockquote>\n\n"
            "2. Neon city\n<blockquote expandable>1girl, raccoon ears, long black hair, pink eyes, black streetwear, standing in a neon city at night, rain, glowing signs, wet asphalt reflections, cinematic composition, detailed anime illustration</blockquote>\n\n"
            "3. Cozy workshop\n<blockquote expandable>1girl, raccoon ears, fluffy striped tail, messy black hair, oversized hoodie, sitting in a cozy fantasy workshop, sketches, crystals, old books, warm lamp light, atmospheric, highly detailed</blockquote>\n\n"
            "4. Cosmic ruins\n<blockquote expandable>1girl, raccoon ears, glowing pink eyes, black cloak, standing among ancient cosmic ruins, floating stones, stars, purple nebula, mysterious atmosphere, cinematic lighting, detailed anime art</blockquote>"
        ),
    }
    return texts.get(section, texts["open"])


def howto_text(remaining: int | None = None, daily_limit: int = 10) -> str:
    remaining_line = f"\n\nСегодня осталось: {remaining}/{daily_limit}." if remaining is not None else ""
    return (
        "❓ <b>Помощь RaccoonNAI</b>\n\n"
        "• Напиши идею картинки одним сообщением.\n"
        "• Проверь черновик и нажми ✅ Генерировать.\n"
        "• ✏️ можно поправить, 🧹 очистить, ❌ отменить.\n"
        "• Бесплатно: 10 генераций в день. ✨"
        + remaining_line
    )


def main_menu_text() -> str:
    return "🦝 <b>Главное меню</b>\n\nЧто рисуем дальше?"


def prompt_request_text() -> str:
    return (
        "🎨 <b>Новый промпт</b>\n\n"
        "Опиши изображение.\n\n"
        "💡 NovelAI лучше понимает английские промпты.\n\n"
        "Например:\n"
        "<code>1girl, raccoon ears, pink eyes, ancient ruins, cinematic lighting, masterpiece</code>\n\n"
        "Можно писать и на русском, но английский обычно даёт лучший результат.\n\n"
        "Отмена: /cancel"
    )


def generation_result_caption(model: str, width: int, height: int, seed: int) -> str:
    seed_text = "random" if seed == -1 else str(seed)
    return (
        "✅ <b>Готово</b>\n"
        f"🧠 <code>{html.escape(str(model))}</code>\n"
        f"📐 <code>{width}x{height}</code>\n"
        f"🎲 Seed: <code>{html.escape(seed_text)}</code>"
    )


def nai_payload_summary_text(payload: dict, settings) -> str:
    summary = payload_summary(payload, settings)
    lines = ["🧪 <b>NovelAI payload summary</b>"]
    for key, value in summary.items():
        lines.append(f"<b>{html.escape(str(key))}:</b> <code>{html.escape(str(value))[:1200]}</code>")
    return "\n".join(lines)


def generation_settings_summary(s) -> str:
    negative = (s.negative_prompt or "").strip()
    negative = "empty" if not negative else html.escape(negative[:120])
    seed = "random" if s.seed == -1 else str(s.seed)
    return f"📐 Размер: <code>{s.width}x{s.height}</code>\n👣 Шаги: <code>{s.steps}</code>\n🧲 CFG: <code>{s.scale}</code>\n🎲 Seed: <code>{seed}</code>\n🚫 Негатив: <code>{negative}</code>\n🧠 Модель: <code>{html.escape(s.model_name)}</code>"


def prompt_preview_text(prompt: str, original: str = "", settings=None, remaining: int | None = None, daily_limit: int = 50) -> str:
    shown_prompt = prompt.strip()
    shown_original = original.strip() if original and original.strip() else ""
    remaining_line = f"\n\nСегодня осталось: {remaining}/{daily_limit}" if remaining is not None else ""
    if shown_original and shown_original != shown_prompt:
        body = (
            "<b>Ты написал:</b>\n"
            f"<code>{html.escape(shown_original[:1400])}</code>\n\n"
            "<b>Промпт для генерации:</b>\n"
            f"<code>{html.escape(shown_prompt[:3000])}</code>"
        )
    else:
        body = "<b>Промпт:</b>\n" f"<code>{html.escape(shown_prompt[:3000])}</code>"
    return "🦝 <b>Черновик готов</b>\n\n" + body + remaining_line


def presets_text() -> str:
    lines = ["⚡ <b>Быстрые пресеты</b>", "", "▶️ — сразу сгенерировать.", "✍️ — показать промт, чтобы скопировать или дописать.", "", "Доступные идеи:"]
    for preset in QUICK_PRESETS.values():
        lines.append(f"• <b>{preset['title']}</b>")
    return "\n".join(lines)
