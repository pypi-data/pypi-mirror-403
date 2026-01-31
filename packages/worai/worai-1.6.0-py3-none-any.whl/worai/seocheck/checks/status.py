from __future__ import annotations

from .types import CheckResult, PageCheck


class StatusCheck(PageCheck):
    name = "status"

    def run(self, *, page, response, elapsed_ms: float, resources: list[dict]) -> CheckResult:
        if response is None:
            return CheckResult(
                name=self.name,
                status="fail",
                details="No response returned by browser",
            )
        status_code = response.status
        ok = 200 <= status_code < 400
        return CheckResult(
            name=self.name,
            status="ok" if ok else "warn",
            details=f"HTTP {status_code}",
            data={"status_code": status_code},
        )
