"""Find entities with mainEntity but missing FAQPage type."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

import rdflib
import requests


@dataclass
class FaqFixOptions:
    file_path: str
    mode: str = "find"  # find, dry-run, patch
    replace_type: bool = False
    api_key: str | None = None


def generate_curl_command(entity_id: str, api_key_placeholder: str = "<YOUR_API_KEY>", replace_type: bool = False) -> str:
    value_payload = {
        "@id": entity_id,
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#type": {
            "@id": "http://schema.org/FAQPage"
        },
    }

    add_operation = {
        "op": "add",
        "path": "/http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        "value": json.dumps(value_payload),
    }

    if replace_type:
        remove_operation = {
            "op": "remove",
            "path": "/http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        }
        patch_payload = [remove_operation, add_operation]
    else:
        patch_payload = [add_operation]

    curl_command = (
        f"curl -L -X PATCH 'https://api.wordlift.io/entities?id={entity_id}' \\\n"
        f" -H 'Content-Type: application/json-patch+json' \\\n"
        f" -H 'Accept: application/ld+json' \\\n"
        f" -H 'Authorization: Key {api_key_placeholder}' \\\n"
        f" --data-raw '{json.dumps(patch_payload, indent=2)}'"
    )
    return curl_command


def _build_patch_payload(entity_id: str, replace_type: bool) -> list[dict]:
    value_payload = {
        "@id": entity_id,
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#type": {
            "@id": "http://schema.org/FAQPage"
        },
    }

    add_operation = {
        "op": "add",
        "path": "/http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        "value": json.dumps(value_payload),
    }

    if replace_type:
        remove_operation = {
            "op": "remove",
            "path": "/http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        }
        return [remove_operation, add_operation]

    return [add_operation]


def patch_entity(entity_id: str, api_key: str, replace_type: bool = False) -> None:
    api_url = f"https://api.wordlift.io/entities?id={entity_id}"

    headers = {
        "Content-Type": "application/json-patch+json",
        "Accept": "application/ld+json",
        "Authorization": f"Key {api_key}",
    }

    patch_payload = _build_patch_payload(entity_id, replace_type)

    max_retries = 3
    delay_seconds = 2

    for attempt in range(max_retries):
        try:
            response = requests.patch(api_url, headers=headers, json=patch_payload, timeout=15)
            response.raise_for_status()
            print(f"  SUCCESS: Patched entity {entity_id} (Status: {response.status_code})")
            return
        except requests.exceptions.RequestException as exc:
            print(
                f"  WARNING: Attempt {attempt + 1} of {max_retries} failed for {entity_id}. Reason: {exc}"
            )
            if attempt < max_retries - 1:
                print(f"  Retrying in {delay_seconds} seconds...")
                time.sleep(delay_seconds)
            else:
                print(
                    f"  ERROR: All {max_retries} attempts failed for {entity_id}. Giving up."
                )


def find_entities(file_path: str) -> list[str]:
    g = rdflib.Graph()
    g.parse(file_path, format="turtle")

    query = """
        PREFIX schema: <http://schema.org/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT DISTINCT ?entity
        WHERE {
          ?entity schema:mainEntity ?anyObject .
          FILTER NOT EXISTS { ?entity rdf:type schema:FAQPage . }
        }
    """

    results = g.query(query)
    return [str(row.entity) for row in results]


def run(options: FaqFixOptions) -> list[str]:
    entities = find_entities(options.file_path)

    if not entities:
        print("No entities were found matching the criteria.")
        return []

    print(
        f"Found {len(entities)} entities with 'schema:mainEntity' that are not of type 'schema:FAQPage'."
    )

    for entity_uri in entities:
        if options.mode == "patch":
            if not options.api_key:
                raise RuntimeError("API key required for patch mode.")
            print(f"Patching: {entity_uri}")
            patch_entity(entity_uri, options.api_key, replace_type=options.replace_type)
        elif options.mode == "dry-run":
            print(f"[DRY RUN] Would patch entity: {entity_uri}")
            print("--- Sample cURL command ---")
            print(generate_curl_command(entity_uri, replace_type=options.replace_type))
            print("---------------------------\n")
        else:
            print(f"Found: {entity_uri}")

    return entities
