from __future__ import annotations

from pathlib import Path

from worai.core.find_url_by_type import FindUrlByTypeOptions, find_urls, resolve_types


def test_resolve_types_filters_schema_prefix() -> None:
    types = resolve_types(["schema:Service", "BadType"])
    assert types == ["http://schema.org/Service"]


def test_find_urls(tmp_path: Path) -> None:
    ttl = """
    @prefix schema: <http://schema.org/> .

    <https://example.com/a> a schema:Service ;
      schema:url <https://example.com/a> .

    <https://example.com/b> a schema:Product ;
      schema:url <https://example.com/b> .
    """
    ttl_path = tmp_path / "data.ttl"
    ttl_path.write_text(ttl)

    options = FindUrlByTypeOptions(filename=str(ttl_path), types=["schema:Service"], show_id=False)
    results = find_urls(options)
    assert results == [("https://example.com/a", "https://example.com/a")]
