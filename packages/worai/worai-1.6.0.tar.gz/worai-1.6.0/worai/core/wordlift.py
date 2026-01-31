"""WordLift API helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import quote_plus

import requests

DEFAULT_GRAPHQL_ENDPOINT = "https://api.wordlift.io/graphql"
DEFAULT_ENTITIES_ENDPOINT = "https://api.wordlift.io/entities"


@dataclass
class WordLiftConfig:
    api_key: str
    graphql_endpoint: str = DEFAULT_GRAPHQL_ENDPOINT
    entities_endpoint: str = DEFAULT_ENTITIES_ENDPOINT


def resolve_api_key(config: Any | None = None, env_key: str = "WORDLIFT_KEY") -> str | None:
    if env_key in os.environ:
        return os.environ[env_key]
    if config is not None:
        try:
            return config.get("wordlift.api_key")
        except Exception:
            return None
    return None


def graphql_request(
    endpoint: str,
    api_key: str,
    query: str,
    timeout: int = 60,
) -> dict:
    headers = {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {"query": query}
    resp = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"GraphQL HTTP {resp.status_code}: {resp.text[:500]}")
    try:
        data = resp.json()
    except ValueError as exc:
        raise RuntimeError("Failed to decode GraphQL JSON response") from exc
    if data.get("errors"):
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return data


def delete_entity(iri: str, api_key: str, include_children: bool = True, timeout: int = 60) -> bool:
    params = f"id={quote_plus(iri)}"
    if include_children:
        params = f"{params}&include_children=true"
    url = f"{DEFAULT_ENTITIES_ENDPOINT}?{params}"
    headers = {"Authorization": f"Key {api_key}"}
    resp = requests.delete(url, headers=headers, timeout=timeout)
    return 200 <= resp.status_code < 300


def delete_entities(
    iris: Iterable[str],
    api_key: str,
    include_children: bool = True,
    timeout: int = 60,
) -> dict[str, bool]:
    results: dict[str, bool] = {}
    for iri in iris:
        results[iri] = delete_entity(iri, api_key, include_children=include_children, timeout=timeout)
    return results
