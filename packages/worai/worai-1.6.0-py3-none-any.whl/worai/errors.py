"""Shared error types and exit codes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WoraError(Exception):
    message: str
    exit_code: int = 1

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message


class UsageError(WoraError):
    def __init__(self, message: str) -> None:
        super().__init__(message, exit_code=2)


class ConfigError(WoraError):
    def __init__(self, message: str) -> None:
        super().__init__(message, exit_code=3)


class ExternalServiceError(WoraError):
    def __init__(self, message: str) -> None:
        super().__init__(message, exit_code=4)
