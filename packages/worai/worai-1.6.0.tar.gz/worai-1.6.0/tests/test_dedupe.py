from __future__ import annotations

from worai.core.dedupe import group_by_url


def test_group_by_url() -> None:
    entities = [
        {"iri": "iri1", "url": "https://example.com/a"},
        {"iri": "iri2", "url": "https://example.com/a"},
        {"iri": "iri3", "url": "https://example.com/b"},
    ]
    grouped = group_by_url(entities)
    assert grouped["https://example.com/a"] == ["iri1", "iri2"]
    assert grouped["https://example.com/b"] == ["iri3"]
