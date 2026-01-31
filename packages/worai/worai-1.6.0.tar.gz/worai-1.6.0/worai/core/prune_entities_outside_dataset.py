"""List WordLift entities outside the account dataset."""

from __future__ import annotations

from dataclasses import dataclass
import asyncio
from typing import List

import wordlift_client
from wordlift_client import ApiClient, Configuration

from worai.core.wordlift import DEFAULT_GRAPHQL_ENDPOINT, graphql_request

DEFAULT_BASE_URL = "https://api.wordlift.io"

DEFAULT_QUERY_TEMPLATE = """
query {
  entities {
    iri
  }
}
"""


@dataclass
class ListOptions:
    api_key: str
    graphql_endpoint: str = DEFAULT_GRAPHQL_ENDPOINT
    base_url: str = DEFAULT_BASE_URL
    query_template: str = DEFAULT_QUERY_TEMPLATE
    dataset_uri: str | None = None
    limit: int = 0


def _build_client(api_key: str, base_url: str) -> ApiClient:
    config = Configuration(host=base_url)
    config.api_key["ApiKey"] = api_key
    config.api_key_prefix["ApiKey"] = "Key"
    return ApiClient(config)


async def _get_dataset_uri_async(api_key: str, base_url: str) -> str:
    async with _build_client(api_key, base_url) as api_client:
        api = wordlift_client.AccountApi(api_client)
        account = await api.get_me()
    dataset_uri = getattr(account, "dataset_uri", None)
    if not dataset_uri:
        raise RuntimeError("Failed to resolve dataset_uri from account get_me.")
    return dataset_uri


def _normalize_dataset_prefixes(dataset_uri: str) -> List[str]:
    base = dataset_uri.rstrip("/")
    prefixes = {dataset_uri, base, f"{base}/"}
    return sorted(p for p in prefixes if p)


def fetch_outside_dataset_iris(
    endpoint: str, api_key: str, dataset_uri: str, query_template: str
) -> List[str]:
    if "{dataset_uri}" in query_template:
        query = query_template.replace("{dataset_uri}", dataset_uri)
    else:
        query = query_template
    data = graphql_request(endpoint, api_key, query)
    try:
        entities = data["data"]["entities"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError("Unexpected GraphQL response structure; 'data.entities' not found") from exc

    dataset_prefixes = _normalize_dataset_prefixes(dataset_uri)
    iris: List[str] = []
    for entry in entities or []:
        iri = entry.get("iri") if isinstance(entry, dict) else None
        if iri:
            iris.append(iri)

    outside: List[str] = []
    for iri in iris:
        if any(iri.startswith(prefix) for prefix in dataset_prefixes):
            continue
        outside.append(iri)
    return outside


def run(options: ListOptions) -> None:
    dataset_uri = options.dataset_uri or asyncio.run(
        _get_dataset_uri_async(options.api_key, options.base_url)
    )
    print(f"Dataset URI: {dataset_uri}")

    iris = fetch_outside_dataset_iris(
        options.graphql_endpoint, options.api_key, dataset_uri, options.query_template
    )
    if options.limit and options.limit > 0:
        iris = iris[: options.limit]

    print(f"Found {len(iris)} entities outside the dataset.")
    for iri in iris:
        print(iri)
