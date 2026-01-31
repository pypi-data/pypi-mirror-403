"""Extract schema:url values for specific schema types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from rdflib import Graph, Namespace

SCHEMA = Namespace("http://schema.org/")


@dataclass
class FindUrlByTypeOptions:
    filename: str
    types: Iterable[str]
    show_id: bool = False


def resolve_types(types: Iterable[str]) -> list[str]:
    resolved: list[str] = []
    for type_str in types:
        if type_str.startswith("schema:"):
            type_name = type_str.split(":", 1)[1]
            resolved.append(str(SCHEMA[type_name]))
    return resolved


def find_urls(options: FindUrlByTypeOptions) -> list[tuple[str, str]]:
    g = Graph()
    g.parse(options.filename, format="turtle")

    target_type_uris = resolve_types(options.types)
    if not target_type_uris:
        return []

    filter_values = ", ".join([f"<{uri}>" for uri in target_type_uris])
    sparql_query = f"""
    PREFIX schema: <http://schema.org/>

    SELECT DISTINCT ?s ?url
    WHERE {{
        ?s a ?type .
        ?s schema:url ?url .
        FILTER (?type IN ({filter_values}))
    }}
    """

    results = g.query(sparql_query)
    return [(str(row.s), str(row.url)) for row in results]
