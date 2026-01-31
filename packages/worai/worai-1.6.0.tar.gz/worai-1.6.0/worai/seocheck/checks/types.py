from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class CheckResult:
    name: str
    status: str
    details: str | None = None
    data: Dict[str, Any] = field(default_factory=dict)


class PageCheck:
    name: str = ""

    def run(self, *, page, response, elapsed_ms: float, resources: list[dict]) -> CheckResult:  # pragma: no cover - interface
        raise NotImplementedError
