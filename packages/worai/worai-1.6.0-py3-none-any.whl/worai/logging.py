"""Logging setup for worai CLI."""

from __future__ import annotations

import logging
import sys
from typing import Literal


LogFormat = Literal["text", "json"]


def setup_logging(level: str = "info", fmt: LogFormat = "text", quiet: bool = False) -> None:
    if quiet:
        level = "warning"
    level_value = getattr(logging, level.upper(), logging.INFO)

    handlers: list[logging.Handler]
    if fmt == "json":
        handlers = [logging.StreamHandler(sys.stderr)]
        logging.basicConfig(level=level_value, handlers=handlers)
        return

    logging.basicConfig(
        level=level_value,
        stream=sys.stderr,
        format="%(levelname)s %(name)s: %(message)s",
    )
