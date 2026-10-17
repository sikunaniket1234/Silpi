# -*- coding: utf-8 -*-
"""Configuration persistence for Silpi (%APPDATA%\\Silpi\\config.json)."""
from __future__ import annotations

import copy
import json
import os

APP_NAME = "Silpi"


def config_dir() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def config_path() -> str:
    return os.path.join(config_dir(), "config.json")


DEFAULTS = {
    "enabled": True,
    "language": "or",          # "or" = Odia, "en" = English (passthrough)
    "scheme": "phonetic",      # "phonetic" | "akruti"
    "tray_notifications": True,
    "commit_space": True,
    "commit_enter": True,
    "commit_tab": True,
    "commit_punct": True,
    "hotkeys": {
        "toggle":          {"vk": 0x4F, "ctrl": True, "alt": True, "shift": False, "win": False},
        "switch_language": {"vk": 0x4C, "ctrl": True, "alt": True, "shift": False, "win": False},
        "convert_now":     {"vk": 0x0D, "ctrl": True, "alt": True, "shift": False, "win": False},
        "settings":        {"vk": 0x53, "ctrl": True, "alt": True, "shift": False, "win": False},
        "keyboard":        {"vk": 0x4B, "ctrl": True, "alt": True, "shift": False, "win": False},
        "converter":       {"vk": 0x43, "ctrl": True, "alt": True, "shift": False, "win": False},
    },
}


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load(path: str | None = None) -> dict:
    path = path or config_path()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        data = {}
    return _merge(DEFAULTS, data)


def save(cfg: dict, path: str | None = None) -> None:
    path = path or config_path()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
