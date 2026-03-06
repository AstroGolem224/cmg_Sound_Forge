import json
from pathlib import Path

CONFIG_FILE = Path.home() / ".sound-forge" / "config.json"

_DEFAULTS = {
    "api_keys": {"elevenlabs": "", "openai": "", "huggingface": ""},
    "output_folder": str(Path.home() / "Desktop"),
    "default_format": "mp3",
}


def load() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, encoding="utf-8") as f:
            cfg = json.load(f)
        for k, v in _DEFAULTS.items():
            if k not in cfg:
                cfg[k] = v
        return cfg
    return {k: (v.copy() if isinstance(v, dict) else v) for k, v in _DEFAULTS.items()}


def save(cfg: dict):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def get_key(provider: str) -> str:
    return load()["api_keys"].get(provider, "")


def set_key(provider: str, key: str):
    cfg = load()
    cfg["api_keys"][provider] = key
    save(cfg)
