from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG = {
    "WAN_IF": "wlan0",
    "LAN_IF": "eth0",
    "PING_IP": "8.8.8.8",
    "PING_DNS": "google.com",
    "PORT": 5000,
    "REFRESH": 5,
}


def _coerce_int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def load_config(config_path: str | None = None) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    path = (
        Path(config_path)
        if config_path
        else Path(os.environ.get("OBSERVER_CONFIG", Path(__file__).with_name("config.yaml")))
    )

    try:
        if path.exists():
            loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if isinstance(loaded, dict):
                config.update(loaded)
    except Exception:
        # Keep defaults when config is broken.
        pass

    config["PORT"] = _coerce_int(config.get("PORT"), DEFAULT_CONFIG["PORT"])
    config["REFRESH"] = _coerce_int(config.get("REFRESH"), DEFAULT_CONFIG["REFRESH"])
    return config

