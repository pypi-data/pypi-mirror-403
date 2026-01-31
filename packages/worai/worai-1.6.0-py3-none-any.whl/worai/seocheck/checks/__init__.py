from __future__ import annotations

from .canonical import CanonicalCheck
from .page_meta import PageMetaCheck
from .resource_404 import Resource404Check
from .response_time import ResponseTimeCheck
from .status import StatusCheck
from .ttfb import TtfbCheck
from .types import CheckResult, PageCheck
from .wordlift_bootstrap import WordLiftBootstrapCheck


def get_page_checks(*, ttfb_ok_ms: float = 200.0, ttfb_warn_ms: float = 500.0) -> list[PageCheck]:
    return [
        StatusCheck(),
        TtfbCheck(ok_ms=ttfb_ok_ms, warn_ms=ttfb_warn_ms),
        ResponseTimeCheck(),
        PageMetaCheck(),
        CanonicalCheck(),
        Resource404Check(),
        WordLiftBootstrapCheck(),
    ]


__all__ = [
    "CheckResult",
    "PageCheck",
    "get_page_checks",
]
