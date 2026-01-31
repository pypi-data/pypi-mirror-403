from __future__ import annotations

from pathlib import Path

from worai.core.find_missing_names import find_pages_without_name_or_headline


def test_find_pages_without_name_or_headline(tmp_path: Path) -> None:
    ttl = """
    @prefix schema: <http://schema.org/> .
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

    <https://example.com/page1> rdf:type schema:CollectionPage ;
      schema:url <https://example.com/page1> .

    <https://example.com/page2> rdf:type schema:CollectionPage ;
      schema:url <https://example.com/page2> ;
      schema:name "Has name" .
    """
    ttl_path = tmp_path / "data.ttl"
    ttl_path.write_text(ttl)

    results = find_pages_without_name_or_headline(str(ttl_path))
    assert results == ["https://example.com/page1"]
