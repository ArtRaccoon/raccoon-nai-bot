"""Telegram Stars Ink package registry and payload helpers."""

import json

INK_PER_GENERATION = 20
FAL_INK_PER_GENERATION = 20

PAYMENT_PACKAGES = {
    "ink_1000": {"id": "ink_1000", "title": "1000 ✒️ Чернил", "ink_amount": 1000, "generations": 50, "stars_price": 75, "description": "Пакет на 1000 ✒️ Чернил (примерно 50 генераций)"},
    "ink_3000": {"id": "ink_3000", "title": "3000 ✒️ Чернил", "ink_amount": 3000, "generations": 150, "stars_price": 199, "description": "Пакет на 3000 ✒️ Чернил (примерно 150 генераций)"},
    "ink_7000": {"id": "ink_7000", "title": "7000 ✒️ Чернил", "ink_amount": 7000, "generations": 350, "stars_price": 399, "description": "Пакет на 7000 ✒️ Чернил (примерно 350 генераций)"},
    "ink_16000": {"id": "ink_16000", "title": "16000 ✒️ Чернил", "ink_amount": 16000, "generations": 800, "stars_price": 799, "description": "Пакет на 16000 ✒️ Чернил (примерно 800 генераций)"},
}


def make_payment_payload(user_id: int, package_id: str) -> str:
    return json.dumps({"user_id": int(user_id), "package_id": str(package_id)}, separators=(",", ":"), ensure_ascii=False)


def parse_payment_payload(payload: str) -> tuple[int, str]:
    data = json.loads(payload or "{}")
    return int(data.get("user_id", 0)), str(data.get("package_id", ""))
