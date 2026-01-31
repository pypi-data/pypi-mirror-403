from __future__ import annotations

import os
from pathlib import Path

from worai.config import load_config


def test_load_config_profile(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "worai.toml"
    config_path.write_text(
        """
        [defaults]
        timeout = 10

        [profile.dev]
        timeout = 20
        """
    )

    cfg = load_config(str(config_path), "dev", env={})
    assert cfg.get("defaults.timeout") == 10
    assert cfg.get("timeout") == 20


def test_env_config_override(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "worai.toml"
    config_path.write_text("[defaults]\nlog_level = 'info'\n")

    env = {"WORAI_CONFIG": str(config_path)}
    cfg = load_config(None, None, env=env)
    assert cfg.get("defaults.log_level") == "info"
