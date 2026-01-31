"""Configuration loader for worai CLI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tomllib

from worai.errors import ConfigError


CONFIG_FILENAMES = [
    "./worai.toml",
    "~/.config/worai/config.toml",
    "~/.worai.toml",
]


@dataclass
class Config:
    raw: dict[str, Any]

    def get(self, path: str, default: Any = None) -> Any:
        value: Any = self.raw
        for part in path.split("."):
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]
        return value



def _expand_path(value: str) -> Path:
    return Path(os.path.expanduser(value)).resolve()


def _load_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        return {}
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML config: {path}: {exc}") from exc


def load_config(
    config_path: str | None,
    profile: str | None,
    env: dict[str, str] | None = None,
) -> Config:
    env = env or os.environ
    if config_path:
        path = _expand_path(config_path)
        data = _load_toml(path)
        return Config(raw=_apply_profile(data, profile))

    if env.get("WORAI_CONFIG"):
        path = _expand_path(env["WORAI_CONFIG"])
        data = _load_toml(path)
        return Config(raw=_apply_profile(data, profile))

    merged: dict[str, Any] = {}
    for filename in CONFIG_FILENAMES:
        data = _load_toml(_expand_path(filename))
        if data:
            merged.update(data)
    return Config(raw=_apply_profile(merged, profile))


def _apply_profile(data: dict[str, Any], profile: str | None) -> dict[str, Any]:
    if not profile:
        profile = os.environ.get("WORAI_PROFILE")
    if not profile:
        return data

    profile_data = data.get("profile", {}).get(profile, {})
    merged = dict(data)
    if "profile" in merged:
        merged.pop("profile", None)
    if isinstance(profile_data, dict):
        merged.update(profile_data)
    return merged
