"""Convert link group CSV to RDF and optionally apply changes via WordLift API."""

from __future__ import annotations

import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from functools import partial
from urllib.parse import quote_plus

import requests
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

SCHEMA = Namespace("http://schema.org/")
SEOVOC = Namespace("https://w3id.org/seovoc/")


@dataclass
class LinkGroupsOptions:
    input_file: str
    output_format: str = "turtle"
    apply: bool = False
    dry_run: bool = False
    api_key: str | None = None
    concurrency: int = 2
    retries: int = 3


def get_link_group_iri_and_id(target_link_iri: str) -> tuple[str, str]:
    link_group_iri = target_link_iri.rsplit("/", 1)[0]
    link_group_identifier = link_group_iri.rsplit("/", 1)[-1]
    return link_group_iri, link_group_identifier


def requests_retry_session(
    retries: int = 3,
    backoff_factor: float = 0.3,
    status_forcelist: tuple[int, ...] = (500, 502, 504),
    session: requests.Session | None = None,
) -> requests.Session:
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def delete_link_group(lg_iri: str, wordlift_key: str, session: requests.Session, dry_run: bool = False):
    delete_url = f"https://api.wordlift.io/entities?id={quote_plus(lg_iri)}&include_children=true"
    if dry_run:
        return f"curl -X DELETE -H 'Authorization: Key {wordlift_key}' '{delete_url}'"
    try:
        response = session.delete(delete_url, headers={"Authorization": f"Key {wordlift_key}"})
        response.raise_for_status()
        if response.status_code not in [200, 204]:
            return f"Unexpected status {response.status_code} for DELETE {lg_iri}"
    except requests.exceptions.RequestException as exc:
        return f"Error deleting {lg_iri}: {exc}"
    return None


def create_link_group(lg_item, wordlift_key: str, session: requests.Session, dry_run: bool = False):
    lg_iri, lg_graph = lg_item
    create_url = "https://api.wordlift.io/entities"
    ttl_data = lg_graph.serialize(format="turtle")
    if dry_run:
        escaped_ttl_data = ttl_data.replace("'", "'\\''")
        return (
            "curl -X PUT -H 'Authorization: Key {key}' -H 'Content-Type: text/turtle' "
            "--data-binary $'{data}' '{url}'"
        ).format(key=wordlift_key, data=escaped_ttl_data, url=create_url)
    try:
        headers = {"Authorization": f"Key {wordlift_key}", "Content-Type": "text/turtle"}
        response = session.put(create_url, data=ttl_data.encode("utf-8"), headers=headers)
        response.raise_for_status()
        if response.status_code not in [200, 201]:
            return f"Unexpected status {response.status_code} for CREATE {lg_iri}"
    except requests.exceptions.RequestException as exc:
        return f"Error creating {lg_iri}: {exc}"
    return None


def patch_webpage(page_item, wordlift_key: str, session: requests.Session, dry_run: bool = False):
    page_iri, lg_iri = page_item
    patch_url = f"https://api.wordlift.io/entities?id={quote_plus(page_iri)}"

    json_ld_graph = {"@id": str(page_iri), str(SEOVOC.hasLinkGroup): {"@id": str(lg_iri)}}
    value_string = json.dumps(json_ld_graph)

    patch_payload = [
        {
            "op": "add",
            "path": f"/{SEOVOC.hasLinkGroup}",
            "value": value_string,
        }
    ]

    if dry_run:
        data_raw = json.dumps(patch_payload)
        return (
            "curl -L -X PATCH '{url}' -H 'Content-Type: application/json-patch+json' "
            "-H 'Accept: application/ld+json' -H 'Authorization: Key {key}' "
            "--data-raw '{data}'"
        ).format(url=patch_url, key=wordlift_key, data=data_raw)

    try:
        headers = {
            "Content-Type": "application/json-patch+json",
            "Accept": "application/ld+json",
            "Authorization": f"Key {wordlift_key}",
        }
        response = session.patch(patch_url, json=patch_payload, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        return f"Error patching {page_iri} for LG {lg_iri}: {exc}"
    return None


def run_concurrently(worker_func, items, description: str, max_workers: int) -> None:
    items_list = list(items)
    if not items_list:
        return

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {executor.submit(worker_func, item): item for item in items_list}
        with tqdm(total=len(items_list), desc=description) as pbar:
            for future in as_completed(future_to_item):
                result = future.result()
                if result:
                    if "curl" in result:
                        tqdm.write(f"\n{result}")
                    else:
                        tqdm.write(result)
                pbar.update(1)


def apply_changes(webpages, link_groups_data, wordlift_key, retries, concurrency, dry_run=False) -> None:
    print("\n--- Applying Changes ---")
    session = requests_retry_session(retries=retries)

    delete_worker = partial(delete_link_group, wordlift_key=wordlift_key, session=session, dry_run=dry_run)
    create_worker = partial(create_link_group, wordlift_key=wordlift_key, session=session, dry_run=dry_run)
    patch_worker = partial(patch_webpage, wordlift_key=wordlift_key, session=session, dry_run=dry_run)

    print("\n1. Deleting existing Link Groups...")
    run_concurrently(delete_worker, link_groups_data.keys(), "Deleting Link Groups", concurrency)

    print("\n2. Creating new Link Groups and Links...")
    run_concurrently(create_worker, link_groups_data.items(), "Creating Link Groups", concurrency)

    print("\n3. Patching WebPage entities...")
    patch_jobs = []
    for page_iri, page_data in webpages.items():
        for lg_iri in page_data["link_groups"]:
            patch_jobs.append((page_iri, lg_iri))

    run_concurrently(patch_worker, patch_jobs, "Patching WebPages  ", concurrency)


def convert_csv_to_rdf(input_file: str):
    g = Graph()
    g.bind("schema", SCHEMA)
    g.bind("seovoc", SEOVOC)
    g.bind("xsd", XSD)

    webpages = {}
    link_groups = {}
    link_groups_graphs = {}

    with open(input_file, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

        for row in tqdm(rows, desc="Processing CSV rows "):
            source_iri = URIRef(row["source_iri"])
            target_link_iri = URIRef(row["target_link_iri"])
            target_web_page_iri = URIRef(row["target_web_page_iri"])
            target_headline = Literal(row["target_headline"])
            target_url = Literal(row["target_url"])
            target_position = Literal(row["target_position"], datatype=XSD.integer)
            target_score = Literal(row["target_score"], datatype=XSD.float)
            target_anchor_text = Literal(row["target_anchor_text"])

            if source_iri not in webpages:
                webpages[source_iri] = {"link_groups": set()}
                g.add((source_iri, RDF.type, SCHEMA.WebPage))

            link_group_iri_str, link_group_id = get_link_group_iri_and_id(row["target_link_iri"])
            link_group_iri = URIRef(link_group_iri_str)
            webpages[source_iri]["link_groups"].add(link_group_iri)

            if link_group_iri not in link_groups:
                link_groups[link_group_iri] = True
                g.add((link_group_iri, RDF.type, SEOVOC.LinkGroup))
                g.add((link_group_iri, SEOVOC.identifier, Literal(link_group_id)))
                g.add((link_group_iri, SEOVOC.isLinkGroupOf, source_iri))
                g.add((source_iri, SEOVOC.hasLinkGroup, link_group_iri))

                lg_graph = Graph()
                lg_graph.bind("schema", SCHEMA)
                lg_graph.bind("seovoc", SEOVOC)
                lg_graph.add((link_group_iri, RDF.type, SEOVOC.LinkGroup))
                lg_graph.add((link_group_iri, SEOVOC.identifier, Literal(link_group_id)))
                lg_graph.add((link_group_iri, SEOVOC.isLinkGroupOf, source_iri))
                link_groups_graphs[link_group_iri] = lg_graph

            lg_graph = link_groups_graphs[link_group_iri]

            g.add((target_link_iri, RDF.type, SEOVOC.Link))
            g.add((target_link_iri, SEOVOC.position, target_position))
            g.add((target_link_iri, SEOVOC.name, target_headline))
            g.add((target_link_iri, SEOVOC.weight, target_score))
            g.add((target_link_iri, SEOVOC.anchorText, target_anchor_text))
            g.add((target_link_iri, SEOVOC.anchorValue, target_url))
            g.add((target_link_iri, SEOVOC.anchorResource, target_web_page_iri))
            g.add((target_link_iri, SEOVOC.isLinkOf, link_group_iri))
            g.add((link_group_iri, SEOVOC.hasLink, target_link_iri))

            for p, o in g.predicate_objects(subject=target_link_iri):
                lg_graph.add((target_link_iri, p, o))
            lg_graph.add((link_group_iri, SEOVOC.hasLink, target_link_iri))

    return g, webpages, link_groups_graphs


def run(options: LinkGroupsOptions) -> str:
    full_graph, webpages_data, link_groups_api_data = convert_csv_to_rdf(options.input_file)

    if options.apply:
        if not options.api_key:
            raise RuntimeError("API key required when --apply is set.")
        apply_changes(
            webpages_data,
            link_groups_api_data,
            options.api_key,
            options.retries,
            options.concurrency,
            options.dry_run,
        )
        print("\n--- Done ---")
        return ""

    return full_graph.serialize(format=options.output_format)
