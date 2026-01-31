"""CLI for structured data generation."""

from __future__ import annotations

import json
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from pathlib import Path
from urllib.parse import urlparse

import typer
from rdflib import Graph

from worai.core.html_to_xhtml import (
    CleanupOptions,
    RenderOptions,
    clean_xhtml,
    render_html,
)
from worai.core.structured_data import (
    StructuredDataOptions,
    StructuredDataResult,
    build_output_basename,
    ensure_no_blank_nodes,
    generate_from_agent,
    get_dataset_uri,
    make_reusable_yarrrml,
    materialize_yarrrml_jsonld,
    normalize_yarrrml_mappings,
    postprocess_jsonld,
    shape_specs_for_type,
)
from worai.core.validate_shacl import validate_file
from worai.core.wordlift import resolve_api_key
from worai.errors import UsageError

app = typer.Typer(add_completion=False, no_args_is_help=True)

_OUTPUT_FORMATS: dict[str, tuple[str, str]] = {
    "ttl": ("turtle", "ttl"),
    "jsonld": ("json-ld", "jsonld"),
    "json-ld": ("json-ld", "jsonld"),
    "rdf": ("xml", "rdf"),
    "nt": ("nt", "nt"),
    "nq": ("nquads", "nq"),
}


def _write_output(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _default_output_paths(out_dir: Path, base_name: str) -> tuple[Path, Path]:
    jsonld_path = out_dir / f"{base_name}.jsonld"
    yarrml_path = out_dir / f"{base_name}.yarrml"
    return jsonld_path, yarrml_path


def _echo_debug(debug_path: Path) -> None:
    if not debug_path.exists():
        return
    try:
        payload = json.loads(debug_path.read_text())
    except Exception:
        typer.echo(f"Debug output written to {debug_path}", err=True)
        return
    prompt = payload.get("prompt", "")
    response = payload.get("response")
    typer.echo("--- Agent prompt ---", err=True)
    typer.echo(prompt, err=True)
    typer.echo("--- Agent response ---", err=True)
    typer.echo(json.dumps(response, indent=2), err=True)


def _normalize_output_format(value: str) -> tuple[str, str]:
    key = value.strip().lower()
    if key not in _OUTPUT_FORMATS:
        supported = ", ".join(sorted({k for k in _OUTPUT_FORMATS if "-" not in k}))
        raise UsageError(f"Unsupported format '{value}'. Choose from: {supported}.")
    return _OUTPUT_FORMATS[key]


def _serialize_graph(graph: Graph, output_format: str) -> str:
    rdflib_format, _ = _normalize_output_format(output_format)
    serialized = graph.serialize(format=rdflib_format)
    if isinstance(serialized, bytes):
        return serialized.decode("utf-8")
    return serialized


def _is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"}


def _urls_from_sitemap(source: str) -> list[str]:
    try:
        import advertools as adv
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise UsageError("advertools is required. Install with: pip install advertools") from exc
    df = adv.sitemap_to_df(source)
    if df is None or df.empty:
        return []
    for column in ("loc", "url"):
        if column in df.columns:
            values = df[column].dropna().astype(str).tolist()
            return [value for value in values if value]
    return df.iloc[:, 0].dropna().astype(str).tolist()


def _resolve_input_urls(value: str) -> list[str]:
    path = Path(value)
    if path.exists():
        urls = _urls_from_sitemap(str(path))
        if not urls:
            raise UsageError("No URLs found in sitemap file.")
        return urls
    if _is_url(value):
        try:
            urls = _urls_from_sitemap(value)
            if urls:
                return urls
        except Exception:
            pass
        return [value]
    raise UsageError("INPUT must be a sitemap URL/path or a page URL.")


def _status_bucket(status_code: int | None) -> str:
    if status_code is None:
        return "error"
    if status_code == 429:
        return "throttle"
    if 500 <= status_code < 600:
        return "server_error"
    if 200 <= status_code < 400:
        return "ok"
    return "client_error"


@app.command("create")
def create(
    ctx: typer.Context,
    url: str = typer.Argument(..., help="Target page URL."),
    target_type_arg: str | None = typer.Argument(
        None, help="Schema.org type to generate (e.g., Review)."
    ),
    target_type: str | None = typer.Option(
        None, "--type", help="Schema.org type to generate (e.g., Review)."
    ),
    output_dir: Path = typer.Option(Path("."), "--output-dir", help="Output directory."),
    base_name: str = typer.Option("structured-data", "--base-name", help="Base output filename."),
    jsonld_path: Path | None = typer.Option(
        None, "--jsonld", help="Write JSON-LD to this file path."
    ),
    yarrml_path: Path | None = typer.Option(
        None, "--yarrml", help="Write YARRRML to this file path."
    ),
    debug: bool = typer.Option(False, "--debug", help="Write agent prompt/response to disk."),
    headed: bool = typer.Option(False, "--headed", help="Run the browser with a visible UI."),
    timeout_ms: int = typer.Option(30000, "--timeout-ms", help="Timeout (ms) for page loads."),
    max_retries: int = typer.Option(
        2, "--max-retries", help="Max retries for agent refinement when required props are missing."
    ),
    quality_check: bool = typer.Option(
        True,
        "--quality-check/--no-quality-check",
        help="Use agent-based quality scoring to decide retries.",
    ),
    max_xhtml_chars: int = typer.Option(
        40000, "--max-xhtml-chars", help="Max characters to keep in cleaned XHTML."
    ),
    max_text_node_chars: int = typer.Option(
        400, "--max-text-node-chars", help="Max characters per text node in cleaned XHTML."
    ),
    max_nesting_depth: int = typer.Option(
        2, "--max-nesting-depth", help="Max depth for related types in the schema guide."
    ),
    verbose: bool = typer.Option(
        True, "--verbose/--no-verbose", help="Emit progress logs to stderr."
    ),
    validate: bool = typer.Option(
        False, "--validate", help="Validate JSON-LD output with SHACL shapes."
    ),
    wait_until: str = typer.Option(
        "networkidle",
        "--wait-until",
        help="Playwright wait strategy.",
    ),
) -> None:
    api_key = resolve_api_key(ctx.obj.get("config") if ctx.obj else None)
    if not api_key:
        raise UsageError("WORDLIFT_KEY is required (or set wordlift.api_key in config).")

    if target_type is None:
        target_type = target_type_arg
    if not target_type:
        raise UsageError("Schema.org type is required. Pass it as an argument or via --type.")

    dataset_uri = get_dataset_uri(api_key)

    render_options = RenderOptions(
        url=url,
        headless=not headed,
        timeout_ms=timeout_ms,
        wait_until=wait_until,
    )
    def log(message: str) -> None:
        if verbose:
            typer.echo(message, err=True)

    log("Rendering page with Playwright...")
    rendered = render_html(render_options)

    log("Cleaning XHTML for prompt usage...")
    cleanup_options = CleanupOptions(
        max_xhtml_chars=max_xhtml_chars,
        max_text_node_chars=max_text_node_chars,
    )
    cleaned_xhtml = clean_xhtml(rendered.xhtml, cleanup_options)

    options = StructuredDataOptions(
        url=url,
        target_type=target_type,
        dataset_uri=dataset_uri,
        headless=not headed,
        timeout_ms=timeout_ms,
        wait_until=wait_until,
        max_retries=max_retries,
        max_xhtml_chars=max_xhtml_chars,
        max_text_node_chars=max_text_node_chars,
        max_nesting_depth=max_nesting_depth,
        verbose=verbose,
    )

    workdir = output_dir / ".structured-data"
    debug_path = workdir / "agent_debug.json"
    try:
        log("Generating YARRRML mapping and JSON-LD...")
        yarrml, jsonld = generate_from_agent(
            options.url,
            rendered.html,
            rendered.xhtml,
            cleaned_xhtml,
            api_key,
            options.dataset_uri,
            options.target_type,
            workdir,
            debug=debug,
            max_retries=options.max_retries,
            max_nesting_depth=options.max_nesting_depth,
            quality_check=quality_check,
            log=log,
        )
    except Exception:
        if debug:
            _echo_debug(debug_path)
        raise
    if debug:
        _echo_debug(debug_path)

    if jsonld_path is None or yarrml_path is None:
        jsonld_path, yarrml_path = _default_output_paths(output_dir, base_name)

    _write_output(jsonld_path, json.dumps(jsonld, indent=2))
    yarrml = make_reusable_yarrrml(yarrml, url)
    _write_output(yarrml_path, yarrml)

    if verbose:
        mapping_validation_path = workdir / "mapping.validation.json"
        if mapping_validation_path.exists():
            try:
                validation_payload = json.loads(mapping_validation_path.read_text())
            except Exception:
                validation_payload = {}
            for warning in validation_payload.get("warnings", []):
                if "reviewRating dropped" in warning:
                    typer.echo(warning, err=True)

    if validate:
        log("Validating JSON-LD output...")
        shape_specs = shape_specs_for_type(options.target_type)
        result = validate_file(str(jsonld_path), shape_specs=shape_specs)
        (workdir / "jsonld.validation.json").write_text(
            json.dumps(
                {
                    "conforms": result.conforms,
                    "warning_count": result.warning_count,
                    "report_text": result.report_text,
                },
                indent=2,
            )
        )
        typer.echo(result.report_text, err=True)

    result = StructuredDataResult(
        jsonld=jsonld,
        yarrml=yarrml,
        jsonld_filename=str(jsonld_path),
        yarrml_filename=str(yarrml_path),
    )
    typer.echo(json.dumps(result.__dict__, indent=2))


@app.command("generate")
def generate(
    ctx: typer.Context,
    input_value: str = typer.Argument(..., metavar="INPUT", help="Sitemap URL/path or page URL."),
    yarrrml_path: Path = typer.Option(..., "--yarrrml", help="Path to YARRRML mapping file."),
    regex: str = typer.Option(".*", "--regex", help="Regex to filter URLs (matches full URL)."),
    output_dir: Path = typer.Option(Path("."), "--output-dir", help="Output directory."),
    output_format: str = typer.Option(
        "ttl", "--format", help="Output format: ttl, jsonld, rdf, nt, nq."
    ),
    concurrency: str = typer.Option(
        "auto", "--concurrency", help="Worker count or 'auto' to adapt to responses."
    ),
    headed: bool = typer.Option(False, "--headed", help="Run the browser with a visible UI."),
    timeout_ms: int = typer.Option(30000, "--timeout-ms", help="Timeout (ms) for page loads."),
    wait_until: str = typer.Option("networkidle", "--wait-until", help="Playwright wait strategy."),
    max_xhtml_chars: int = typer.Option(
        40000, "--max-xhtml-chars", help="Max characters to keep in cleaned XHTML."
    ),
    max_text_node_chars: int = typer.Option(
        400, "--max-text-node-chars", help="Max characters per text node in cleaned XHTML."
    ),
    max_pages: int | None = typer.Option(None, "--max-pages", help="Max pages to process."),
    verbose: bool = typer.Option(True, "--verbose/--no-verbose", help="Emit progress logs to stderr."),
) -> None:
    api_key = resolve_api_key(ctx.obj.get("config") if ctx.obj else None)
    dataset_uri = get_dataset_uri(api_key) if api_key else None
    if not dataset_uri:
        raise UsageError("WORDLIFT_KEY is required (or set wordlift.api_key in config).")
    if not yarrrml_path.exists():
        raise UsageError(f"YARRRML file not found: {yarrrml_path}")
    yarrrml = yarrrml_path.read_text()

    urls = _resolve_input_urls(input_value)
    pattern = re.compile(regex)
    urls = [url for url in urls if pattern.search(url)]
    if not urls:
        raise UsageError("No URLs matched the provided regex.")
    if max_pages is not None:
        urls = urls[: max_pages]

    _, extension = _normalize_output_format(output_format)
    output_dir.mkdir(parents=True, exist_ok=True)

    auto_concurrency = concurrency.strip().lower() == "auto"
    if auto_concurrency:
        min_workers = 2
        max_workers = 12
        current_workers = min(max_workers, max(min_workers, 4))
    else:
        try:
            current_workers = int(concurrency)
        except ValueError as exc:
            raise UsageError("Concurrency must be an integer or 'auto'.") from exc
        if current_workers <= 0:
            raise UsageError("Concurrency must be greater than 0.")

    def log(message: str) -> None:
        if verbose:
            typer.echo(message, err=True)

    results: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []

    with tempfile.TemporaryDirectory(prefix="structured-data-generate-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        index = 0
        total = len(urls)
        if verbose:
            log(f"Processing {total} URLs...")
        from tqdm import tqdm  # noqa: WPS433 - runtime dependency

        progress = tqdm(total=total, disable=not verbose)

        def _process_url(url: str) -> dict[str, object]:
            status_code = None
            try:
                step_start = time.perf_counter()
                log(f"Start: {url}")
                render_options = RenderOptions(
                    url=url,
                    headless=not headed,
                    timeout_ms=timeout_ms,
                    wait_until=wait_until,
                )
                rendered = render_html(render_options)
                log(f"Rendered: {url} in {time.perf_counter() - step_start:.2f}s")
                status_code = rendered.status_code
                step_start = time.perf_counter()
                cleanup_options = CleanupOptions(
                    max_xhtml_chars=max_xhtml_chars,
                    max_text_node_chars=max_text_node_chars,
                )
                cleaned_xhtml = clean_xhtml(rendered.xhtml, cleanup_options)
                log(f"Cleaned XHTML: {url} in {time.perf_counter() - step_start:.2f}s")
                basename = build_output_basename(url)
                xhtml_path = tmp_root / f"{basename}.xhtml"
                xhtml_path.write_text(cleaned_xhtml)
                workdir = tmp_root / f"work-{basename}"
                step_start = time.perf_counter()
                normalized_yarrrml, mappings = normalize_yarrrml_mappings(
                    yarrrml,
                    url,
                    xhtml_path,
                    target_type=None,
                )
                log(f"Normalized YARRRML: {url} in {time.perf_counter() - step_start:.2f}s")
                step_start = time.perf_counter()
                jsonld_raw = materialize_yarrrml_jsonld(normalized_yarrrml, xhtml_path, workdir, url=url)
                log(f"Materialized JSON-LD: {url} in {time.perf_counter() - step_start:.2f}s")
                step_start = time.perf_counter()
                jsonld = postprocess_jsonld(
                    jsonld_raw,
                    mappings,
                    cleaned_xhtml,
                    dataset_uri,
                    url,
                    target_type=None,
                )
                log(f"Postprocessed JSON-LD: {url} in {time.perf_counter() - step_start:.2f}s")
                step_start = time.perf_counter()
                graph = Graph()
                graph.parse(data=json.dumps(jsonld), format="json-ld")
                ensure_no_blank_nodes(graph)
                output_path = output_dir / f"{basename}.{extension}"
                if output_format.lower() in {"jsonld", "json-ld"}:
                    _write_output(output_path, json.dumps(jsonld, indent=2))
                else:
                    serialized = _serialize_graph(graph, output_format)
                    _write_output(output_path, serialized)
                log(f"Wrote output: {url} in {time.perf_counter() - step_start:.2f}s")
                return {
                    "ok": True,
                    "url": url,
                    "status_code": status_code,
                    "output": str(output_path),
                }
            except Exception as exc:
                log(f"Failed: {url} with {exc}")
                return {
                    "ok": False,
                    "url": url,
                    "status_code": status_code,
                    "error": str(exc),
                }

        while index < total:
            batch = urls[index : index + current_workers]
            if not batch:
                break
            batch_results: list[dict[str, object]] = []
            with ThreadPoolExecutor(max_workers=current_workers) as executor:
                futures = {executor.submit(_process_url, url): url for url in batch}
                for future in as_completed(futures):
                    result = future.result()
                    batch_results.append(result)
                    progress.update(1)
                    if not result.get("ok"):
                        errors.append({"url": str(result.get("url")), "error": str(result.get("error"))})
            results.extend(batch_results)

            if auto_concurrency:
                buckets = {_status_bucket(item.get("status_code")) for item in batch_results}
                if buckets & {"throttle", "server_error", "error"}:
                    current_workers = max(min_workers, current_workers - 1)
                elif buckets == {"ok"}:
                    current_workers = min(max_workers, current_workers + 1)
            index += len(batch)
        progress.close()

    summary = {
        "input": input_value,
        "format": output_format,
        "output_dir": str(output_dir),
        "total": len(urls),
        "success": sum(1 for item in results if item.get("ok")),
        "failed": sum(1 for item in results if not item.get("ok")),
        "errors": errors,
    }
    typer.echo(json.dumps(summary, indent=2))
