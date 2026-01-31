from __future__ import annotations

from .types import CheckResult, PageCheck


class TtfbCheck(PageCheck):
    name = "ttfb"

    def __init__(self, ok_ms: float = 200.0, warn_ms: float = 500.0) -> None:
        self.ok_ms = ok_ms
        self.warn_ms = warn_ms

    def run(self, *, page, response, elapsed_ms: float, resources: list[dict]) -> CheckResult:
        if response is None:
            return CheckResult(
                name=self.name,
                status="fail",
                details="No response returned by browser",
            )

        try:
            timing = page.evaluate(
                """
                () => {
                  const nav = performance.getEntriesByType('navigation')[0];
                  if (nav) {
                    return { requestStart: nav.requestStart, responseStart: nav.responseStart };
                  }
                  if (performance.timing) {
                    return { requestStart: performance.timing.requestStart, responseStart: performance.timing.responseStart };
                  }
                  return null;
                }
                """
            )
        except Exception as exc:
            return CheckResult(
                name=self.name,
                status="fail",
                details=f"timing unavailable: {exc}",
            )

        if not timing:
            return CheckResult(
                name=self.name,
                status="fail",
                details="timing data missing",
            )

        request_start = timing.get("requestStart")
        response_start = timing.get("responseStart")
        if request_start is None or response_start is None:
            return CheckResult(
                name=self.name,
                status="fail",
                details="timing data missing",
            )

        ttfb_ms = max(0.0, response_start - request_start)
        if ttfb_ms <= self.ok_ms:
            status = "ok"
        elif ttfb_ms <= self.warn_ms:
            status = "warn"
        else:
            status = "fail"

        return CheckResult(
            name=self.name,
            status=status,
            details=f"{ttfb_ms:.0f} ms",
            data={"ttfb_ms": ttfb_ms, "ok_ms": self.ok_ms, "warn_ms": self.warn_ms},
        )
