import json
from pathlib import Path
from config_defaults import UserSettings

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"

def _ensure() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not USERS_FILE.exists():
        USERS_FILE.write_text("{}", encoding="utf-8")

def load_all() -> dict:
    _ensure()
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

def save_all(data: dict) -> None:
    _ensure()
    tmp = USERS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(USERS_FILE)

def get_settings(user_id: int) -> UserSettings:
    data = load_all()
    raw = data.get(str(user_id), {})
    defaults = UserSettings().to_dict()
    defaults.update(raw)
    return UserSettings(**defaults)

def save_settings(user_id: int, settings: UserSettings) -> None:
    data = load_all()
    data[str(user_id)] = settings.to_dict()
    save_all(data)

def patch_settings(user_id: int, **kwargs) -> UserSettings:
    settings = get_settings(user_id)
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    save_settings(user_id, settings)
    return settings
