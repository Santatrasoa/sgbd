# utils/config_loader.py
import json
from pathlib import Path

def load_config():
    config_path = Path("config.json")
    default = {"db_path": ".database", "default_prompt": "m¥⇒", "separator_char": "—"}
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                default.update(user_config)
        except:
            pass
    return default
