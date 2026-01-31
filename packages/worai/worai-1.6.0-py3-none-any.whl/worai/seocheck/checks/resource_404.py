from __future__ import annotations

from .types import CheckResult, PageCheck


class Resource404Check(PageCheck):
    name = "resource_404"

    def __init__(self, max_samples: int = 5) -> None:
        self.max_samples = max_samples

    def run(self, *, page, response, elapsed_ms: float, resources: list[dict]) -> CheckResult:
        failing = []
        for item in resources:
            status = item.get("status")
            if status is None or status < 400:
                continue
            resource_type = item.get("resource_type")
            if resource_type in {"image", "script", "stylesheet", "font"}:
                failing.append(item)

        if not failing:
            return CheckResult(
                name=self.name,
                status="ok",
                details="no 4xx/5xx resources",
                data={"count": 0},
            )

        samples = failing[: self.max_samples]
        details = f"{len(failing)} resource(s) returned 4xx/5xx"
        return CheckResult(
            name=self.name,
            status="warn",
            details=details,
            data={
                "count": len(failing),
                "samples": samples,
            },
        )
