"""Patch WordLift entities from RDF (Turtle or JSON-LD)."""

from __future__ import annotations

import json
import os
import sys
import time
import subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from urllib.parse import quote

from rdflib import BNode, Graph, Literal, URIRef
from tqdm import tqdm

API_ENDPOINT = "https://api.wordlift.io/entities"
RDF_TYPE = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")


@dataclass
class PatchOptions:
    input_file: str
    api_key: str
    dry_run: bool = False
    add_types: bool = False
    types_only: bool = False
    subjects_file: str | None = None
    workers: int = 2
    retries: int = 3


def format_json_ld_node(node):
    if isinstance(node, URIRef):
        return {"@id": str(node)}
    if isinstance(node, BNode):
        return {"@id": f"_:{node}"}
    if isinstance(node, Literal):
        if node.language:
            return {"@value": str(node), "@language": node.language}
        if node.datatype:
            return {"@value": str(node), "@type": str(node.datatype)}
        return str(node)
    return str(node)


def process_subject(subject_uri, predicates, api_key, dry_run, max_retries, add_types):
    patch_operations = []
    for predicate, objects in predicates.items():
        predicate_uri = str(predicate)
        should_replace = not (add_types and predicate == RDF_TYPE)

        if should_replace:
            patch_operations.append({"op": "remove", "path": f"/{predicate_uri}"})

        formatted_objects = [format_json_ld_node(obj) for obj in objects]
        objects_value = formatted_objects[0] if len(formatted_objects) == 1 else formatted_objects

        json_ld_graph = {"@id": subject_uri, predicate_uri: objects_value}
        stringified_add_value = json.dumps(json_ld_graph, separators=(",", ":"))

        patch_operations.append({"op": "add", "path": f"/{predicate_uri}", "value": stringified_add_value})

    encoded_subject = quote(subject_uri, safe="")
    target_url = f"{API_ENDPOINT}?id={encoded_subject}"
    json_payload = json.dumps(patch_operations, indent=2)

    if dry_run:
        command_str = (
            f"# DRY RUN: Full payload for <{subject_uri}>\n"
            f"curl -L -X PATCH '{target_url}' \\\n"
            f"  -H 'Content-Type: application/json-patch+json' \\\n"
            f"  -H 'Accept: application/ld+json' \\\n"
            f"  -H 'Authorization: Key <API_KEY_HIDDEN>' \\\n"
            f"  --data-raw '{json.dumps(patch_operations, indent=2)}'"
        )
        return subject_uri, True, command_str

    curl_command = [
        "curl",
        "-L",
        "-s",
        "-X",
        "PATCH",
        target_url,
        "-H",
        "Content-Type: application/json-patch+json",
        "-H",
        "Accept: application/ld+json",
        "-H",
        f"Authorization: Key {api_key}",
        "--data-raw",
        json_payload,
    ]

    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                curl_command,
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )
            return subject_uri, True, f"Response: {result.stdout}"
        except Exception as exc:
            if attempt + 1 == max_retries:
                return subject_uri, False, f"Error: {exc}"
            tqdm.write(f"\nWarning: {exc}\nRetrying in 5 seconds...", file=sys.stderr)
            time.sleep(5)

    return subject_uri, False, "Should not be reached"


def _load_subjects_from_file(path: str) -> set[str]:
    subjects = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                subjects.add(line)
    return subjects


def _read_graph(input_file: str) -> Graph:
    g = Graph()
    ext = os.path.splitext(input_file)[1].lower()
    if ext == ".jsonld":
        g.parse(input_file, format="json-ld")
    else:
        g.parse(input_file, format="turtle")
    return g


def run(options: PatchOptions) -> None:
    g = _read_graph(options.input_file)

    subjects_filter = None
    if options.subjects_file:
        subjects_filter = _load_subjects_from_file(options.subjects_file)

    subjects = defaultdict(lambda: defaultdict(list))

    for s, p, o in g:
        if options.types_only and p != RDF_TYPE:
            continue
        if subjects_filter and str(s) not in subjects_filter:
            continue
        subjects[str(s)][p].append(o)

    total_subjects = len(subjects)
    if total_subjects == 0:
        print("No subjects found for processing.")
        return

    print(f"Processing {total_subjects} subjects...")

    with ThreadPoolExecutor(max_workers=options.workers) as executor:
        futures = [
            executor.submit(
                process_subject,
                subject_uri,
                predicates,
                options.api_key,
                options.dry_run,
                options.retries,
                options.add_types,
            )
            for subject_uri, predicates in subjects.items()
        ]

        for future in tqdm(as_completed(futures), total=len(futures), desc="Patching"):
            subject_uri, success, message = future.result()
            if not success:
                tqdm.write(f"Failed for {subject_uri}: {message}")
            elif options.dry_run:
                tqdm.write(message)
