# utils/config_loader.py
import json
from pathlib import Path

def load_config():
    config_path = Path("config/config.json")
    default = {
        "db_path": ".database",
        "default_prompt": "m¥⇒",
        "separator_char": "—",
        "history_file": ".history",
        "max_history_size": 1000,
        "default_admin": {"username": "root", "role": "admin"},
        "allowed_data_types": ["string", "number"],
        "allowed_constraints": {"not_null": "Not_null"},
        "permissions": ["SELECT", "INSERT"]
    }
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                # Fusion profonde
                for key, value in user_config.items():
                    if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                        default[key].update(value)
                    else:
                        default[key] = value
        except Exception as e:
            print(f"Error loading config: {e}")
    return default
