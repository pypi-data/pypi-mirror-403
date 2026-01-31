"""Find collection pages missing schema:name or schema:headline."""

from __future__ import annotations

import rdflib

QUERY = """
PREFIX schema: <http://schema.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT ?url
WHERE {
  ?entity rdf:type schema:CollectionPage .
  ?entity schema:url ?url .
  FILTER (
    NOT EXISTS { ?entity schema:name ?anyName . } &&
    NOT EXISTS { ?entity schema:headline ?anyHeadline . }
  )
}
"""


def find_pages_without_name_or_headline(file_path: str) -> list[str]:
    g = rdflib.Graph()
    g.parse(file_path)
    results = g.query(QUERY)
    return [str(row.url) for row in results]


def run(file_path: str) -> list[str]:
    return find_pages_without_name_or_headline(file_path)
