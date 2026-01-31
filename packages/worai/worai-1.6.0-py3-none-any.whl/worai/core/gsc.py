"""Google Search Console utilities."""

from __future__ import annotations

import csv
import datetime as dt
import os
from dataclasses import dataclass
from typing import Dict
from urllib.parse import quote

from google.auth.transport.requests import AuthorizedSession, Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
GSC_QUERY_ENDPOINT = "https://www.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query"


@dataclass
class GscOptions:
    site: str
    client_secrets: str
    token: str
    port: int
    output: str
    row_limit: int
    search_type: str
    data_state: str


def load_credentials(client_secrets_path: str, token_path: str, port: int) -> Credentials:
    creds = None
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception:
            creds = None

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
        creds = flow.run_local_server(port=port)

    with open(token_path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    return creds


def gsc_post(session: AuthorizedSession, site: str, payload: dict) -> dict:
    url = GSC_QUERY_ENDPOINT.format(site=quote(site, safe=""))
    response = session.post(url, json=payload)
    if response.status_code != 200:
        raise RuntimeError(
            f"GSC API request failed ({response.status_code}): {response.text}"
        )
    return response.json()


def find_last_available_date(session: AuthorizedSession, site: str) -> dt.date:
    end_date = dt.datetime.now(dt.timezone.utc).date()
    start_date = end_date - dt.timedelta(days=10)
    payload = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": ["date"],
    }
    data = gsc_post(session, site, payload)
    rows = data.get("rows", [])
    if not rows:
        raise RuntimeError("No data returned when checking last available date.")

    dates = [row["keys"][0] for row in rows if row.get("keys")]
    if not dates:
        raise RuntimeError("No date keys returned when checking last available date.")

    return max(dt.date.fromisoformat(d) for d in dates)


def fetch_page_metrics(
    session: AuthorizedSession,
    site: str,
    start_date: dt.date,
    end_date: dt.date,
    row_limit: int,
    search_type: str,
    data_state: str,
) -> Dict[str, Dict[str, float]]:
    all_rows = []
    start_row = 0

    while True:
        payload = {
            "dataState": data_state,
            "startRow": start_row,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["page"],
            "rowLimit": row_limit,
            "type": search_type,
            "aggregationType": "byPage",
        }
        data = gsc_post(session, site, payload)
        rows = data.get("rows", [])
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < row_limit:
            break
        start_row += row_limit

    metrics = {}
    for row in all_rows:
        keys = row.get("keys") or []
        if not keys:
            continue
        page = keys[0]
        metrics[page] = {
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": row.get("ctr", 0),
            "position": row.get("position", 0),
        }

    return metrics


def merge_metrics(
    metrics_7d: Dict[str, Dict[str, float]],
    metrics_28d: Dict[str, Dict[str, float]],
    metrics_3m: Dict[str, Dict[str, float]],
) -> Dict[str, Dict[str, float]]:
    pages = set(metrics_7d) | set(metrics_28d) | set(metrics_3m)
    merged: Dict[str, Dict[str, float]] = {}

    def build_row(data: Dict[str, float], suffix: str) -> Dict[str, float]:
        return {
            f"clicks_{suffix}": data.get("clicks", 0),
            f"impressions_{suffix}": data.get("impressions", 0),
            f"ctr_{suffix}": data.get("ctr", 0),
            f"position_{suffix}": data.get("position", 0),
        }

    for page in pages:
        merged[page] = {
            **build_row(metrics_7d.get(page, {}), "7d"),
            **build_row(metrics_28d.get(page, {}), "28d"),
            **build_row(metrics_3m.get(page, {}), "3m"),
        }

    return merged


def write_csv(path: str, merged: Dict[str, Dict[str, float]]) -> None:
    fieldnames = [
        "page",
        "clicks_7d",
        "impressions_7d",
        "ctr_7d",
        "position_7d",
        "clicks_28d",
        "impressions_28d",
        "ctr_28d",
        "position_28d",
        "clicks_3m",
        "impressions_3m",
        "ctr_3m",
        "position_3m",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for page in sorted(merged.keys()):
            writer.writerow({"page": page, **merged[page]})


def run(options: GscOptions) -> None:
    creds = load_credentials(options.client_secrets, options.token, options.port)
    session = AuthorizedSession(creds)

    last_date = find_last_available_date(session, options.site)

    end_7d = last_date
    start_7d = end_7d - dt.timedelta(days=7)

    end_28d = last_date
    start_28d = end_28d - dt.timedelta(days=28)

    end_3m = last_date
    start_3m = end_3m - dt.timedelta(days=90)

    metrics_7d = fetch_page_metrics(
        session,
        options.site,
        start_7d,
        end_7d,
        options.row_limit,
        options.search_type,
        options.data_state,
    )
    metrics_28d = fetch_page_metrics(
        session,
        options.site,
        start_28d,
        end_28d,
        options.row_limit,
        options.search_type,
        options.data_state,
    )
    metrics_3m = fetch_page_metrics(
        session,
        options.site,
        start_3m,
        end_3m,
        options.row_limit,
        options.search_type,
        options.data_state,
    )

    merged = merge_metrics(metrics_7d, metrics_28d, metrics_3m)
    write_csv(options.output, merged)
