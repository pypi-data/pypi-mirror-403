from __future__ import annotations

from pathlib import Path

from worai.core.canonicalize_duplicate_pages import load_gsc_csv, select_canonical


def test_load_gsc_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "gsc.csv"
    csv_path.write_text(
        "page,clicks_28d,impressions_28d\n"
        "https://example.com/a,10,100\n"
        "https://example.com/b,5,50\n"
    )

    data = load_gsc_csv(str(csv_path), None)
    assert data["https://example.com/a"]["clicks_28d"] == 10.0


def test_select_canonical() -> None:
    urls = ["https://example.com/a", "https://example.com/b"]
    kpis = {
        "https://example.com/a": {"clicks_28d": 10.0},
        "https://example.com/b": {"clicks_28d": 5.0},
    }
    canonical = select_canonical(urls, kpis, "clicks_28d")
    assert canonical == "https://example.com/a"
