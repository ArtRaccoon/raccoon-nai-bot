#!/usr/bin/env python3
"""Focused verification for /start and learning data safety."""
from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import storage
from keyboards import learning_lesson_menu, learning_menu, main_menu, start_menu
from ui.texts import learning_text, start_text


def _button_callbacks(markup):
    return [button.callback_data for row in markup.inline_keyboard for button in row]


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        storage.DATA_DIR = data_dir
        storage.USERS_FILE = data_dir / "users.json"
        storage.CONFIG_FILE = data_dir / "config.json"

        user_id = 424242
        original = {
            "id": user_id,
            "username": "old_name",
            "first_name": "Old",
            "last_name": "User",
            "full_name": "Old User",
            "paid_generations_balance": 777,
            "history": [{"prompt": "old prompt", "path": "data/generated/a.png"}],
            "favorites": [{"prompt": "favorite prompt", "path": "data/generated/f.png"}],
            "width": 832,
            "height": 1216,
            "steps": 27,
            "scale": 5.5,
            "sampler": "k_euler_ancestral",
            "seed": 123456,
            "negative_prompt": "low quality",
            "legacy_custom_field": {"keep": ["this", 1]},
            "pro_access_until": "2099-01-01T00:00:00+00:00",
            "advanced_generation_mode": True,
            "hq_balance": 55,
            "payment_fields": {"telegram_charge_id": "abc"},
            "last_prompt": "1girl, raccoon ears",
        }
        storage.save_all({str(user_id): copy.deepcopy(original)})

        before = storage.load_all()[str(user_id)]
        storage.update_user_identity(SimpleNamespace(id=user_id, username="new_name", first_name="New", last_name="User", full_name="New User"))
        storage.get_settings(user_id)
        after = storage.load_all()[str(user_id)]

        allowed_identity = {"username", "first_name", "last_name", "full_name", "last_seen_at"}
        for key, value in before.items():
            if key not in allowed_identity:
                assert after.get(key) == value, f"field changed after /start simulation: {key}"
        assert after["legacy_custom_field"] == original["legacy_custom_field"]
        assert after["history"] == original["history"]
        assert after["favorites"] == original["favorites"]
        assert after["paid_generations_balance"] == original["paid_generations_balance"]
        assert after["hq_balance"] == original["hq_balance"]

        new_user_id = 515151
        storage.update_user_identity(SimpleNamespace(id=new_user_id, username="newbie", first_name="New", last_name="", full_name="New"))
        storage.get_settings(new_user_id)
        assert str(new_user_id) in storage.load_all(), "new user was not created through identity/storage flow"

        os.environ.pop("WELCOME_IMAGE_FILE_ID", None)
        assert "Добро пожаловать" in start_text()
        assert _button_callbacks(start_menu()) == ["learning:open", "menu:gen", "menu:main"]

        settings_before_learning = storage.load_all()[str(user_id)]
        for section in ("open", "first_steps", "prompts", "character", "style", "mistakes", "examples"):
            assert learning_text(section)
        learning_menu()
        learning_lesson_menu()
        assert storage.load_all()[str(user_id)] == settings_before_learning, "learning UI modified user data"

        moderator_callbacks = _button_callbacks(main_menu(moderator=True))
        assert "admin:menu" in moderator_callbacks, "moderator main menu is unavailable"

    print("start data safety verification passed")


if __name__ == "__main__":
    main()
