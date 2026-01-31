from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import requests


@dataclass
class RobotsTxtResult:
    url: str
    status: str
    status_code: int | None
    disallow_all: bool
    details: str


def _extract_groups(lines: Iterable[str]) -> list[dict[str, list[str]]]:
    groups: list[dict[str, list[str]]] = []
    current: dict[str, list[str]] = {"user_agents": [], "disallow": []}
    for raw in lines:
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            continue
        key, value = [part.strip() for part in line.split(":", 1)]
        key_lower = key.lower()
        if key_lower == "user-agent":
            if current["user_agents"]:
                groups.append(current)
                current = {"user_agents": [], "disallow": []}
            current["user_agents"].append(value)
        elif key_lower == "disallow":
            current["disallow"].append(value)
    if current["user_agents"]:
        groups.append(current)
    return groups


def _disallow_all(text: str) -> bool:
    groups = _extract_groups(text.splitlines())
    for group in groups:
        if any(agent == "*" for agent in group["user_agents"]):
            if any(rule.strip() == "/" for rule in group["disallow"]):
                return True
    return False


def check_robots_txt(base_url: str, *, session: requests.Session, timeout: float) -> RobotsTxtResult:
    url = base_url.rstrip("/") + "/robots.txt"
    try:
        response = session.get(url, timeout=timeout)
    except requests.RequestException as exc:
        return RobotsTxtResult(
            url=url,
            status="fail",
            status_code=None,
            disallow_all=False,
            details=f"request failed: {exc}",
        )

    disallow_all = False
    details = ""
    if response.status_code == 200:
        disallow_all = _disallow_all(response.text)
        if disallow_all:
            details = "User-agent * is blocked (Disallow: /)"
        else:
            details = "robots.txt available"
        status = "warn" if disallow_all else "ok"
    else:
        status = "warn"
        details = f"robots.txt returned {response.status_code}"

    return RobotsTxtResult(
        url=url,
        status=status,
        status_code=response.status_code,
        disallow_all=disallow_all,
        details=details,
    )
