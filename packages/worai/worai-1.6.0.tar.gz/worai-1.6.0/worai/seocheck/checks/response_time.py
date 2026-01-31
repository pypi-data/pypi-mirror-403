from __future__ import annotations

from .types import CheckResult, PageCheck


class ResponseTimeCheck(PageCheck):
    name = "response_time"

    def __init__(self, warning_ms: float = 2000.0, fail_ms: float = 5000.0) -> None:
        self.warning_ms = warning_ms
        self.fail_ms = fail_ms

    def run(self, *, page, response, elapsed_ms: float, resources: list[dict]) -> CheckResult:
        if elapsed_ms >= self.fail_ms:
            status = "fail"
        elif elapsed_ms >= self.warning_ms:
            status = "warn"
        else:
            status = "ok"
        return CheckResult(
            name=self.name,
            status=status,
            details=f"{elapsed_ms:.0f} ms",
            data={"elapsed_ms": elapsed_ms},
        )
