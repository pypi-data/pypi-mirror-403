"""SEO Report Core Logic."""

from __future__ import annotations

import datetime as dt
import re
import time
import requests
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from google.auth.transport.requests import AuthorizedSession

from worai.core.gsc import find_last_available_date, gsc_post, load_credentials

@dataclass
class ReportOptions:
    site: str
    url_regex: Optional[str] = None
    client_secrets: Optional[str] = None
    token: Optional[str] = None
    port: int = 0
    output: str = "seo_report.md"
    format: str = "markdown"
    inspect_limit: int = 10

@dataclass
class InspectionResult:
    url: str
    verdict: str  # PASS, FAIL, NEUTRAL
    indexing_state: str
    robotstxt_state: str
    last_crawl_time: Optional[str] = None
    page_fetch_state: Optional[str] = None

@dataclass
class IndexingSummary:
    valid: int = 0
    excluded: int = 0
    error: int = 0
    issues: Dict[str, List[str]] = field(default_factory=dict)
    sample_size: int = 0

@dataclass
class LiveMetric:
    url: str
    status_code: int
    response_time_ms: float
    is_ok: bool

@dataclass
class HealthSummary:
    avg_response_time: float
    host_availability: float  # percentage
    slow_pages: int
    error_pages: int
    total_checked: int
    details: List[LiveMetric] = field(default_factory=list)

@dataclass
class DateRange:
    start: dt.date
    end: dt.date

@dataclass
class PeriodRanges:
    current: DateRange
    pop: DateRange
    yoy: DateRange

@dataclass
class QueryMetric:
    query: str
    clicks: int
    impressions: int
    ctr: float
    position: float
    # Diffs (Optional, calculated later)
    clicks_diff: float = 0
    impressions_diff: float = 0
    ctr_diff: float = 0
    position_diff: float = 0

@dataclass
class DailyMetric:
    date: str  # YYYY-MM-DD
    clicks: int
    impressions: int
    ctr: float
    position: float

@dataclass
class PeriodAnalysis:
    name: str
    dates: PeriodRanges
    overall: Dict[str, Any]
    winning: List[Dict[str, Any]]
    losing: List[Dict[str, Any]]
    opportunities: List[Dict[str, Any]]
    daily_trend: List[DailyMetric] = field(default_factory=list)

def get_period_ranges(last_date: dt.date, days: int) -> PeriodRanges:
    """Calculate Current, PoP, and YoY ranges."""
    # Current: [last - days + 1, last]
    curr_end = last_date
    curr_start = curr_end - dt.timedelta(days=days - 1)
    
    # PoP: [curr_start - days, curr_start - 1]
    # Wait, usually PoP is same duration immediately before.
    # [last - 2*days + 1, last - days]
    pop_end = curr_start - dt.timedelta(days=1)
    pop_start = pop_end - dt.timedelta(days=days - 1)
    
    # YoY: Same dates last year.
    # Note: simplistic 365 days subtraction.
    yoy_end = curr_end - dt.timedelta(days=365)
    yoy_start = curr_start - dt.timedelta(days=365)
    
    return PeriodRanges(
        current=DateRange(curr_start, curr_end),
        pop=DateRange(pop_start, pop_end),
        yoy=DateRange(yoy_start, yoy_end),
    )

def fetch_gsc_data(
    session: AuthorizedSession,
    site: str,
    start: dt.date,
    end: dt.date,
    dimensions: List[str],
    row_limit: int = 25000,
) -> pd.DataFrame:
    """Fetch GSC data for a specific range and dimensions."""
    all_rows = []
    start_row = 0

    while True:
        payload = {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "dimensions": dimensions,
            "rowLimit": row_limit,
            "startRow": start_row,
        }
        data = gsc_post(session, site, payload)
        rows = data.get("rows", [])
        
        if not rows:
            break
            
        for row in rows:
            keys = row.get("keys", [])
            # Map keys to dimensions
            item = {dim: k for dim, k in zip(dimensions, keys)}
            item["clicks"] = row.get("clicks", 0)
            item["impressions"] = row.get("impressions", 0)
            item["ctr"] = row.get("ctr", 0)
            item["position"] = row.get("position", 0)
            all_rows.append(item)
            
        if len(rows) < row_limit:
            break
        start_row += row_limit

    if not all_rows:
        return pd.DataFrame(columns=dimensions + ["clicks", "impressions", "ctr", "position"])

    return pd.DataFrame(all_rows)

def aggregate_data(df: pd.DataFrame, url_regex: Optional[str] = None) -> pd.DataFrame:
    """Filter and aggregate data by query."""
    if df.empty:
        return df

    if "page" in df.columns and url_regex:
        # Filter by regex
        df = df[df["page"].str.match(url_regex, na=False)].copy()

    if df.empty:
        return pd.DataFrame(columns=["query", "clicks", "impressions", "ctr", "position"])

    # If we have 'page' column (or others), we need to group by 'query'
    # Weighted average for position and ctr is tricky.
    # GSC Average Position is average of highest position of the site for the query.
    # When aggregating multiple pages for same query, summing clicks/impressions is correct.
    # Re-calculating CTR = Clicks / Impressions
    # Re-calculating Position:
    # Technically, we can't perfectly reconstruct average position from paginated page-query data 
    # without knowing impression volume per specific position occurrence.
    # However, a weighted average by impressions is the standard approximation.
    # Position * Impressions = Sum_Pos_Imp
    # Avg Pos = Sum_Pos_Imp / Total_Impressions
    
    # Check if we need grouping
    if "query" not in df.columns:
        # Should not happen given we always request query
        return df

    # If rows are already unique by query (no page dimension), just return.
    if "page" not in df.columns:
        return df.set_index("query")

    # Grouping
    df["pos_x_imp"] = df["position"] * df["impressions"]
    
    grouped = df.groupby("query").agg({
        "clicks": "sum",
        "impressions": "sum",
        "pos_x_imp": "sum"
    })
    
    grouped["ctr"] = grouped.apply(lambda x: x["clicks"] / x["impressions"] if x["impressions"] > 0 else 0, axis=1)
    grouped["position"] = grouped.apply(lambda x: x["pos_x_imp"] / x["impressions"] if x["impressions"] > 0 else 0, axis=1)
    
    return grouped[["clicks", "impressions", "ctr", "position"]]

def calculate_diffs(current: pd.Series, comparison: pd.Series) -> Dict[str, Any]:
    """Calculate absolute and percentage differences."""
    # Handle missing comparison data
    if comparison.empty or comparison.isna().all():
        return {
            "abs": current.fillna(0).to_dict(),
            "pct": {k: 100.0 if v > 0 else 0.0 for k, v in current.fillna(0).items()} # If prev is 0, growth is 100% or infinite? Let's say 100% for now or None
        }

    # Current values
    curr_dict = current.fillna(0).to_dict()
    comp_dict = comparison.fillna(0).to_dict()
    
    diffs = {}
    pcts = {}
    
    for metric in ["clicks", "impressions", "ctr", "position"]:
        c_val = curr_dict.get(metric, 0)
        p_val = comp_dict.get(metric, 0)
        
        diff = c_val - p_val
        diffs[metric] = diff
        
        if p_val != 0:
            pct = (diff / p_val) * 100
        else:
            pct = 100.0 if c_val > 0 else 0.0
        pcts[metric] = pct
        
    return {"abs": diffs, "pct": pcts}

def analyze_period(
    name: str,
    ranges: PeriodRanges,
    session: AuthorizedSession,
    site: str,
    url_regex: Optional[str]
) -> PeriodAnalysis:
    """Analyze a specific period (Current vs PoP vs YoY)."""
    
    dimensions = ["query"]
    if url_regex:
        dimensions.append("page")
        
    # Fetch Data
    print(f"Fetching {name} data...")
    df_curr_raw = fetch_gsc_data(session, site, ranges.current.start, ranges.current.end, dimensions)
    df_pop_raw = fetch_gsc_data(session, site, ranges.pop.start, ranges.pop.end, dimensions)
    df_yoy_raw = fetch_gsc_data(session, site, ranges.yoy.start, ranges.yoy.end, dimensions)
    
    # Fetch Daily Trend Data (Current Period Only)
    print(f"Fetching {name} daily trend...")
    # For daily trend, we just need 'date' dimension, filtering by the regex if needed is tricky
    # because GSC API aggregates differently.
    # If we want daily trend for the filtered pages, we MUST include 'page' in dimensions and then aggregate.
    trend_dims = ["date"]
    if url_regex:
        trend_dims.append("page")
        
    df_trend_raw = fetch_gsc_data(session, site, ranges.current.start, ranges.current.end, trend_dims)
    
    # Process Trend Data
    if url_regex and "page" in df_trend_raw.columns:
         df_trend_raw = df_trend_raw[df_trend_raw["page"].str.match(url_regex, na=False)]
    
    if not df_trend_raw.empty:
        # Group by date if we have page dimension or multiple rows
        # Weighted average logic applies here too for position/ctr
        df_trend_raw["pos_x_imp"] = df_trend_raw["position"] * df_trend_raw["impressions"]
        trend_grouped = df_trend_raw.groupby("date").agg({
            "clicks": "sum",
            "impressions": "sum",
            "pos_x_imp": "sum"
        }).reset_index()
        
        trend_grouped["ctr"] = trend_grouped.apply(lambda x: x["clicks"] / x["impressions"] if x["impressions"] > 0 else 0, axis=1)
        trend_grouped["position"] = trend_grouped.apply(lambda x: x["pos_x_imp"] / x["impressions"] if x["impressions"] > 0 else 0, axis=1)
        trend_grouped = trend_grouped.sort_values("date")
        
        daily_trend = [
            DailyMetric(
                date=row["date"],
                clicks=int(row["clicks"]),
                impressions=int(row["impressions"]),
                ctr=float(row["ctr"]),
                position=float(row["position"])
            )
            for _, row in trend_grouped.iterrows()
        ]
    else:
        daily_trend = []

    # Process/Aggregate
    df_curr = aggregate_data(df_curr_raw, url_regex)
    df_pop = aggregate_data(df_pop_raw, url_regex)
    df_yoy = aggregate_data(df_yoy_raw, url_regex)
    
    # Overall Metrics
    overall_curr = df_curr[["clicks", "impressions", "ctr", "position"]].mean() # Wait, sum for clicks/imp, mean for ctr/pos?
    # Actually for overall stats:
    # Clicks: Sum
    # Impressions: Sum
    # CTR: Sum(Clicks) / Sum(Impressions)
    # Position: Weighted Average by Impressions
    
    def get_totals(df):
        if df.empty:
            return pd.Series({"clicks": 0, "impressions": 0, "ctr": 0, "position": 0})
        
        clicks = df["clicks"].sum()
        impressions = df["impressions"].sum()
        ctr = clicks / impressions if impressions > 0 else 0
        # Position weighted
        pos_x_imp = (df["position"] * df["impressions"]).sum()
        position = pos_x_imp / impressions if impressions > 0 else 0
        return pd.Series({
            "clicks": clicks, 
            "impressions": impressions, 
            "ctr": ctr, 
            "position": position
        })

    total_curr = get_totals(df_curr)
    total_pop = get_totals(df_pop)
    total_yoy = get_totals(df_yoy)
    
    overall_stats = {
        "current": total_curr.to_dict(),
        "pop_change": calculate_diffs(total_curr, total_pop),
        "yoy_change": calculate_diffs(total_curr, total_yoy),
    }

    # Join for Query comparisons (Current vs PoP)
    # We want Winning/Losing based on IMPRESSIONS change
    
    # Align DataFrames
    # merge on index (query)
    merged = df_curr.join(df_pop, lsuffix="_curr", rsuffix="_prev", how="outer").fillna(0)
    
    merged["imp_diff"] = merged["impressions_curr"] - merged["impressions_prev"]
    merged["clicks_diff"] = merged["clicks_curr"] - merged["clicks_prev"]
    
    # Winning: Largest Positive Impression Diff
    winning_df = merged.sort_values("imp_diff", ascending=False).head(10)
    # Filter only positive
    winning_df = winning_df[winning_df["imp_diff"] > 0]
    
    # Losing: Largest Negative Impression Diff
    losing_df = merged.sort_values("imp_diff", ascending=True).head(10)
    # Filter only negative
    losing_df = losing_df[losing_df["imp_diff"] < 0]
    
    # Opportunities: Pos 8-12 in Current, sorted by Imp
    # Use df_curr for this
    opts_df = df_curr[
        (df_curr["position"] >= 8.0) & (df_curr["position"] <= 12.0)
    ].sort_values("impressions", ascending=False).head(20) # Top 20 opportunities

    def to_list(df_part):
        # We need to construct the list of dicts. 
        # For winning/losing, we want current stats + diffs.
        res = []
        for query, row in df_part.iterrows():
            # If coming from 'merged', keys have suffixes
            if "impressions_curr" in row:
                base = {
                    "query": query,
                    "clicks": row["clicks_curr"],
                    "impressions": row["impressions_curr"],
                    "ctr": row["ctr_curr"],
                    "position": row["position_curr"],
                    "clicks_diff": row["clicks_diff"],
                    "impressions_diff": row["imp_diff"],
                    # We might want CTR/Pos diffs too?
                    "ctr_diff": row["ctr_curr"] - row["ctr_prev"],
                    "position_diff": row["position_curr"] - row["position_prev"],
                }
            else:
                # Coming from opts_df (single period)
                base = {
                    "query": query,
                    "clicks": row["clicks"],
                    "impressions": row["impressions"],
                    "ctr": row["ctr"],
                    "position": row["position"],
                }
            res.append(base)
        return res

    return PeriodAnalysis(
        name=name,
        dates=ranges,
        overall=overall_stats,
        winning=to_list(winning_df),
        losing=to_list(losing_df),
        opportunities=to_list(opts_df),
        daily_trend=daily_trend
    )

def fetch_inspection_data(session: AuthorizedSession, site: str, urls: List[str]) -> IndexingSummary:
    """Fetch URL Inspection data for a list of URLs."""
    if not urls:
        return IndexingSummary()
    
    print(f"Inspecting {len(urls)} URLs via GSC API...")
    summary = IndexingSummary(sample_size=len(urls))
    
    # Simple rate limiting/batching
    # Quota is strict (e.g., 2000/day, but also minute limits).
    # sequential is safest.
    
    for url in urls:
        try:
            # Inspection API requires siteUrl and inspectionUrl
            payload = {
                "inspectionUrl": url,
                "siteUrl": site,
                "languageCode": "en-US"
            }
            # Need to call: https://searchconsole.googleapis.com/v1/urlTestingTools/mobileFriendlyTest:run ? No.
            # Endpoint: https://searchconsole.googleapis.com/v1/urlInspection/index:inspect
            
            # Since gsc_post is likely configured for 'webmasters/v3' or 'searchconsole/v1/sites/...', 
            # we might need to construct the full URL or check gsc_post implementation.
            # Worai's gsc_post uses session.post(f"https://www.googleapis.com/webmasters/v3/sites/{encoded_site}/searchAnalytics/query", ...)
            # We need a different endpoint.
            
            api_url = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
            resp = session.post(api_url, json=payload)
            
            if resp.status_code != 200:
                print(f"Error inspecting {url}: {resp.status_code} {resp.text}")
                continue
                
            data = resp.json()
            result = data.get("inspectionResult", {})
            index_result = result.get("indexStatusResult", {})
            
            verdict = index_result.get("verdict", "NEUTRAL") # PASS, FAIL, NEUTRAL
            coverage_state = index_result.get("coverageState", "Unknown") # e.g. "Indexed, not submitted in sitemap"
            
            # Map verdict
            if verdict == "PASS":
                summary.valid += 1
            elif verdict == "FAIL":
                summary.error += 1
            else:
                summary.excluded += 1
                
            # Identify specific issues
            # "Crawled - currently not indexed"
            if "Crawled - currently not indexed" in coverage_state:
                if "Crawled - currently not indexed" not in summary.issues:
                    summary.issues["Crawled - currently not indexed"] = []
                summary.issues["Crawled - currently not indexed"].append(url)
            
            # "Duplicate without user selected canonical"
            if "Duplicate without user-selected canonical" in coverage_state:
                if "Duplicate without user selected canonical" not in summary.issues:
                    summary.issues["Duplicate without user selected canonical"] = []
                summary.issues["Duplicate without user selected canonical"].append(url)
                
            # Soft 404
            if "Soft 404" in coverage_state:
                 if "Soft 404" not in summary.issues:
                    summary.issues["Soft 404"] = []
                 summary.issues["Soft 404"].append(url)

            # Generic aggregation of other exclusions
            if verdict != "PASS" and "Crawled" not in coverage_state and "Duplicate" not in coverage_state and "Soft 404" not in coverage_state:
                 if coverage_state not in summary.issues:
                     summary.issues[coverage_state] = []
                 summary.issues[coverage_state].append(url)

        except Exception as e:
            print(f"Exception inspecting {url}: {e}")
            
        time.sleep(0.5) # Courtesy sleep
        
    return summary

def run_live_health_check(urls: List[str]) -> HealthSummary:
    """Run live HTTP checks on URLs."""
    if not urls:
        return HealthSummary(0, 0, 0, 0, 0)
        
    print(f"Running live health check on {len(urls)} URLs...")
    metrics = []
    
    for url in urls:
        start = time.time()
        try:
            resp = requests.head(url, timeout=10, allow_redirects=True)
            # If HEAD fails or method not allowed, try GET
            if resp.status_code == 405:
                 resp = requests.get(url, timeout=10, stream=True)
                 resp.close()
            
            duration = (time.time() - start) * 1000
            metrics.append(LiveMetric(
                url=url,
                status_code=resp.status_code,
                response_time_ms=duration,
                is_ok=200 <= resp.status_code < 400
            ))
        except Exception as e:
            duration = (time.time() - start) * 1000
            metrics.append(LiveMetric(
                url=url,
                status_code=0, # 0 indicates connection error
                response_time_ms=duration,
                is_ok=False
            ))
            
    # Aggregate
    total = len(metrics)
    if total == 0:
        return HealthSummary(0, 0, 0, 0, 0)
        
    avg_time = sum(m.response_time_ms for m in metrics) / total
    ok_count = sum(1 for m in metrics if m.is_ok)
    host_avail = (ok_count / total) * 100
    slow = sum(1 for m in metrics if m.response_time_ms > 2000)
    errors = total - ok_count
    
    return HealthSummary(
        avg_response_time=avg_time,
        host_availability=host_avail,
        slow_pages=slow,
        error_pages=errors,
        total_checked=total,
        details=metrics
    )

def generate_report_data(options: ReportOptions) -> Dict[str, Any]:
    creds = load_credentials(options.client_secrets, options.token, options.port)
    session = AuthorizedSession(creds)
    
    last_date = find_last_available_date(session, options.site)
    
    # 1. Analyze Periods
    periods = [7, 30, 90]
    results = []
    
    # We will use the 7-day period to identify the "Current Top URLs" for inspection
    cohort_urls = []
    
    for days in periods:
        ranges = get_period_ranges(last_date, days)
        name = f"Last {days} Days"
        analysis = analyze_period(name, ranges, session, options.site, options.url_regex)
        results.append(analysis)
        
        # Capture cohort from 7-day period (most recent relevant data)
        if days == 7:
            # We need URLs (pages), but analyze_period aggregates by Query by default unless page dimension is forced?
            # analyze_period logic: if url_regex is set, it fetches 'page'. 
            # If url_regex is NOT set, it fetches only 'query'.
            # To do inspection, we NEED pages.
            # We must make a separate call to get top pages if we don't have them.
            pass

    # 2. Identify Cohort for Inspection
    # Fetch top pages for the last 7 days
    print("Fetching top pages for inspection cohort...")
    last_7_range = get_period_ranges(last_date, 7)
    top_pages_df = fetch_gsc_data(
        session, 
        options.site, 
        last_7_range.current.start, 
        last_7_range.current.end, 
        ["page"]
    )
    
    if not top_pages_df.empty:
        # Sort by impressions
        cohort_urls = top_pages_df.sort_values("impressions", ascending=False).head(options.inspect_limit)["page"].tolist()
    
    # 3. Run Inspections & Checks
    indexing_data = None
    health_data = None
    
    if cohort_urls:
        indexing_data = fetch_inspection_data(session, options.site, cohort_urls)
        health_data = run_live_health_check(cohort_urls)
    else:
        indexing_data = IndexingSummary()
        health_data = HealthSummary(0, 0, 0, 0, 0)
        
    return {
        "site_url": options.site,
        "generated_at": dt.datetime.now(),
        "periods": results,
        "indexing": indexing_data,
        "health": health_data
    }