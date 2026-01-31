from __future__ import annotations

from dataclasses import dataclass

import requests


@dataclass
class LlmsTxtResult:
    url: str
    status: str
    status_code: int | None
    details: str


def _fetch(url: str, *, session: requests.Session, timeout: float) -> tuple[int | None, str | None, str | None]:
    try:
        response = session.get(url, timeout=timeout)
    except requests.RequestException as exc:
        return None, None, f"request failed: {exc}"
    return response.status_code, response.text, None


def check_llms_txt(base_url: str, *, session: requests.Session, timeout: float) -> LlmsTxtResult:
    candidate_urls = [
        base_url.rstrip("/") + "/llms.txt",
        base_url.rstrip("/") + "/.well-known/llms.txt",
    ]

    for candidate in candidate_urls:
        status_code, text, error = _fetch(candidate, session=session, timeout=timeout)
        if error:
            return LlmsTxtResult(
                url=candidate,
                status="fail",
                status_code=None,
                details=error,
            )
        if status_code == 200:
            size = len(text or "")
            return LlmsTxtResult(
                url=candidate,
                status="ok",
                status_code=status_code,
                details=f"llms.txt available ({size} chars)",
            )

    return LlmsTxtResult(
        url=candidate_urls[0],
        status="warn",
        status_code=404,
        details="llms.txt not found",
    )
