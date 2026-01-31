"""Deduplicate WordLift entities by schema:url."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple
from urllib.parse import quote_plus

import requests

from worai.core.wordlift import DEFAULT_GRAPHQL_ENDPOINT

GRAPHQL_QUERY = """
query {
  entities {
    iri
    url: string(name: "schema:url")
  }
}
"""

DELETE_URL_TEMPLATE = "https://api.wordlift.io/entities?id={iri}&include_children=true"


@dataclass
class DedupeOptions:
    api_key: str
    endpoint: str = DEFAULT_GRAPHQL_ENDPOINT
    dry_run: bool = False
    rate_delay: float = 0.0
    auto: bool = False


def fetch_entities(endpoint: str, api_key: str, timeout: int = 60) -> List[Dict[str, str]]:
    headers = {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {"query": GRAPHQL_QUERY}
    resp = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"GraphQL HTTP {resp.status_code}: {resp.text[:500]}")

    try:
        data = resp.json()
    except ValueError as exc:
        raise RuntimeError("Failed to decode GraphQL JSON response") from exc

    if data.get("errors"):
        raise RuntimeError(f"GraphQL errors: {data['errors']}")

    try:
        entities = data["data"]["entities"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError("Unexpected GraphQL response structure; 'data.entities' not found") from exc

    out: List[Dict[str, str]] = []
    for entry in entities or []:
        iri = entry.get("iri")
        url = entry.get("url")
        if not iri or not url:
            continue
        out.append({"iri": iri, "url": url})
    return out


def group_by_url(entities: List[Dict[str, str]]) -> Dict[str, List[str]]:
    grouped: Dict[str, List[str]] = {}
    for entry in entities:
        url = entry["url"].strip()
        iri = entry["iri"].strip()
        grouped.setdefault(url, []).append(iri)
    return grouped


def prompt_choice(url: str, iris: List[str]) -> Tuple[int, bool]:
    print("\n================================================================")
    print(f"URL: {url}")
    print("Duplicate IRIs:")
    for i, iri in enumerate(iris, start=1):
        print(f"  {i}. {iri}")
    while True:
        choice = input("Choose which IRI to KEEP (1..{0}) or 'S' to skip: ".format(len(iris))).strip()
        if choice.lower() == "s":
            return -1, True
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(iris):
                return idx - 1, False
        print("Invalid choice. Please enter a valid number or 'S'.")


def delete_iri(iri: str, api_key: str, dry_run: bool, rate_delay: float = 0.0) -> bool:
    url = DELETE_URL_TEMPLATE.format(iri=quote_plus(iri))
    if dry_run:
        print(f"[DRY-RUN] Would DELETE {url}")
        return True

    headers = {"Authorization": f"Key {api_key}"}
    try:
        resp = requests.delete(url, headers=headers, timeout=60)
    except requests.RequestException as exc:
        print(f"Delete failed for {iri}: {exc}")
        return False

    if 200 <= resp.status_code < 300:
        print(f"Deleted {iri}")
        if rate_delay > 0:
            time.sleep(rate_delay)
        return True

    print(f"Delete FAILED for {iri} (HTTP {resp.status_code}): {resp.text[:500]}")
    return False


def run(options: DedupeOptions) -> None:
    print("Fetching entities...")
    entities = fetch_entities(options.endpoint, options.api_key)
    print(f"Fetched {len(entities)} entities with non-empty URLs.")

    grouped = group_by_url(entities)
    duplicates = {u: iris for u, iris in grouped.items() if len(iris) > 1}

    if not duplicates:
        print("No duplicated URLs found. You're all set!")
        return

    print(f"Found {len(duplicates)} duplicated URLs.")

    total_deleted = 0
    total_skipped = 0

    for url, iris in sorted(duplicates.items(), key=lambda kv: kv[0].lower()):
        if options.auto:
            keep_idx, skipped = len(iris) - 1, False
            print(f"Auto mode: keeping last IRI ({iris[keep_idx]}) for URL {url}")
        else:
            keep_idx, skipped = prompt_choice(url, iris)

        if skipped:
            print("Skipped.")
            total_skipped += 1
            continue

        to_delete = [iri for i, iri in enumerate(iris) if i != keep_idx]
        if not to_delete:
            print("Nothing to delete for this URL.")
            continue

        print("Will delete the following IRIs:")
        for iri in to_delete:
            print(f"  - {iri}")

        for iri in to_delete:
            if delete_iri(iri, options.api_key, options.dry_run, rate_delay=options.rate_delay):
                total_deleted += 1

    print("\n================================================================")
    print("Summary:")
    print(f"  Duplicated URLs processed: {len(duplicates)}")
    print(f"  Groups skipped: {total_skipped}")
    print(f"  IRIs deleted: {total_deleted}{' (dry-run)' if options.dry_run else ''}")
