"""CLI wrapper for SHACL validation."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import typer

from worai.core.validate_shacl import validate_file
from worai.errors import UsageError
from rdflib import BNode, Graph, Namespace, URIRef, RDF
from rdflib.collection import Collection

app = typer.Typer(add_completion=False, no_args_is_help=True, invoke_without_command=True)

_SH = Namespace("http://www.w3.org/ns/shacl#")
_SCHEMA = "http://schema.org/"


def _shorten_term(term: URIRef) -> str:
    value = str(term)
    if value.startswith(_SCHEMA):
        return value[len(_SCHEMA) :]
    if "#" in value:
        return value.rsplit("#", 1)[-1]
    if "/" in value:
        return value.rsplit("/", 1)[-1]
    return value


def _path_to_str(graph: Graph, path: URIRef | BNode | None) -> str:
    if path is None:
        return ""
    if isinstance(path, BNode):
        items = [item for item in Collection(graph, path)]
        if items:
            return ".".join(_shorten_term(item) if isinstance(item, URIRef) else str(item) for item in items)
        return str(path)
    if isinstance(path, URIRef):
        return _shorten_term(path)
    return str(path)


def _describe_path(graph: Graph, path: URIRef | BNode | None) -> str:
    if path is None:
        return ""
    if isinstance(path, BNode):
        inv = graph.value(path, _SH.inversePath)
        if inv:
            return f"inverse { _shorten_term(inv) }"
        items = [item for item in Collection(graph, path)]
        if items:
            return ".".join(_shorten_term(item) if isinstance(item, URIRef) else str(item) for item in items)
    if isinstance(path, URIRef):
        return _shorten_term(path)
    return str(path)


def _or_shape_hint(graph: Graph, shape: URIRef | BNode | None) -> str | None:
    if shape is None:
        return None
    or_list = graph.value(shape, _SH["or"])
    if not or_list:
        return None
    alts = []
    for alt in Collection(graph, or_list):
        prop = graph.value(alt, _SH.property)
        if prop is None:
            continue
        path = graph.value(prop, _SH.path)
        if path is None:
            continue
        desc = _describe_path(graph, path)
        if desc:
            alts.append(desc)
    if not alts:
        return None
    if len(alts) == 1:
        return f"Provide: {alts[0]}."
    return f"Provide one of: {', '.join(alts)}."


def _format_pretty_lines(
    report_graph: Graph,
    data_graph: Graph | None,
    shape_source_map: dict[URIRef | BNode, str] | None,
) -> tuple[str, list[tuple[str, str]]]:
    results = []
    for result in report_graph.subjects(_SH.resultSeverity, None):
        severity = report_graph.value(result, _SH.resultSeverity)
        focus = report_graph.value(result, _SH.focusNode)
        path = report_graph.value(result, _SH.resultPath)
        message = report_graph.value(result, _SH.resultMessage)
        source_shape = report_graph.value(result, _SH.sourceShape)
        value_node = report_graph.value(result, _SH.value)
        results.append(
            {
                "severity": severity,
                "focus": focus,
                "path": path,
                "message": str(message) if message else "",
                "source_shape": source_shape,
                "value_node": value_node,
            }
        )

    if not results:
        return "Status: OK (0 errors, 0 warnings, 0 infos)", []

    def severity_label(sev: URIRef | None) -> str:
        if sev == _SH.Violation:
            return "ERROR"
        if sev == _SH.Warning:
            return "WARN"
        if sev == _SH.Info:
            return "INFO"
        return "WARN"

    errors = sum(1 for r in results if r["severity"] == _SH.Violation)
    warnings = sum(1 for r in results if r["severity"] == _SH.Warning)
    infos = sum(1 for r in results if r["severity"] == _SH.Info)

    status = "ERROR" if errors else "WARNING" if warnings else "INFO" if infos else "OK"
    lines: list[tuple[str, str]] = []
    header = f"Status: {status} ({errors} errors, {warnings} warnings, {infos} infos)"

    by_focus: dict[str, list[dict]] = {}
    for r in results:
        focus = str(r["focus"]) if r["focus"] is not None else "(unknown)"
        by_focus.setdefault(focus, []).append(r)

    for focus, items in by_focus.items():
        focus_types: list[str] = []
        if data_graph is not None and focus != "(unknown)":
            for t in data_graph.objects(URIRef(focus), RDF.type):
                focus_types.append(_shorten_term(t))
        if focus_types:
            lines.append(("text", f"Entity: {focus} (types: {', '.join(sorted(set(focus_types)))})"))
        else:
            lines.append(("text", f"Entity: {focus}"))
        for item in items:
            label = severity_label(item["severity"])
            path = _path_to_str(report_graph, item["path"])
            msg = item["message"]
            value_node = item.get("value_node")
            value_str = f" Value: {value_node}" if value_node is not None else ""
            focus = item.get("focus")
            focus_str = f" Focus: {focus}" if focus is not None else ""
            shape = item.get("source_shape")
            shape_str = ""
            if shape is not None:
                mapped = shape_source_map.get(shape) if shape_source_map else None
                if mapped:
                    shape_str = f" [shape: {mapped}]"
                elif isinstance(shape, URIRef):
                    shape_str = f" [shape: {_shorten_term(shape)}]"
                else:
                    shape_str = " [shape: (anonymous)]"
            google_required_suffix = ""
            if label == "ERROR" and shape is not None:
                shape_text = str(shape)
                if "google_" in shape_text or "/google/" in shape_text:
                    google_required_suffix = " Required by Google."
            if msg.startswith("Less than 1 values") and path:
                prefix = "Missing recommended property" if label == "WARN" else "Missing required property"
                lines.append((label, f"- {label} {path}: {prefix}.{google_required_suffix}{shape_str}"))
            elif "Value does not conform to Shape" in msg:
                fallback = "Value does not satisfy the required shape."
                if shape:
                    shape_msg = report_graph.value(shape, _SH.message)
                    if shape_msg:
                        fallback = str(shape_msg)
                    else:
                        hint = _or_shape_hint(report_graph, shape)
                        if hint:
                            fallback = hint
                if path:
                    lines.append((label, f"- {label} {path}: {fallback}{value_str}{shape_str}"))
                else:
                    lines.append((label, f"- {label} {fallback}{value_str}{focus_str}{shape_str}"))
            elif "must conform to one or more shapes" in msg:
                fallback = "Failed to satisfy one of the alternative constraints."
                if shape:
                    shape_msg = report_graph.value(shape, _SH.message)
                    if shape_msg:
                        fallback = str(shape_msg)
                    else:
                        hint = _or_shape_hint(report_graph, shape)
                        if hint:
                            fallback = hint
                if path:
                    lines.append((label, f"- {label} {path}: {fallback}{value_str}{shape_str}"))
                else:
                    lines.append((label, f"- {label} {fallback}{value_str}{focus_str}{shape_str}"))
            elif path and msg:
                lines.append((label, f"- {label} {path}: {msg}{value_str}{shape_str}"))
            elif msg:
                lines.append((label, f"- {label} {msg}{value_str}{focus_str}{shape_str}"))
            else:
                lines.append((label, f"- {label}"))
        lines.append(("text", ""))

    return header, lines


@app.callback(invoke_without_command=True)
def run(
    ctx: typer.Context,
    input_file: str | None = typer.Argument(
        None,
        help="Path or URL to RDF input file (.ttl or .jsonld).",
    ),
    shape: list[str] | None = typer.Option(
        None,
        "--shape",
        "-s",
        help="Shape path or packaged shape name (default: all packaged shapes).",
        show_default=False,
    ),
    report_file: str | None = typer.Option(
        None,
        "--report-file",
        help="Write the SHACL report text to this file.",
    ),
    format: str = typer.Option(
        "pretty",
        "--format",
        help="Output format: pretty or raw.",
        show_default=True,
    ),
    color: bool = typer.Option(
        True,
        "--color/--no-color",
        help="Colorize pretty output.",
        show_default=True,
    ),
    list_shapes: bool = typer.Option(
        False,
        "--list-shapes",
        help="List available packaged shapes and exit.",
    ),
) -> None:
    if list_shapes:
        from worai.core.validate_shacl import list_shape_names

        for name in list_shape_names():
            typer.echo(name)
        return

    if not input_file:
        raise UsageError("Missing input file or URL.")

    result = validate_file(input_file, shape)

    if format not in {"pretty", "raw"}:
        raise UsageError("Invalid format. Use 'pretty' or 'raw'.")

    if format == "raw":
        output_text = result.report_text
        if report_file:
            Path(report_file).write_text(output_text, encoding="utf-8")
        else:
            typer.echo(output_text)
    else:
        header, lines = _format_pretty_lines(
            result.report_graph,
            result.data_graph,
            result.shape_source_map,
        )
        if report_file:
            output_text = "\n".join([header] + [line for _, line in lines]).rstrip() + "\n"
            Path(report_file).write_text(output_text, encoding="utf-8")
        else:
            status_color = {
                "Status: ERROR": typer.colors.RED,
                "Status: WARNING": typer.colors.YELLOW,
                "Status: INFO": typer.colors.BLUE,
                "Status: OK": typer.colors.GREEN,
            }
            header_color = None
            for prefix, fg in status_color.items():
                if header.startswith(prefix):
                    header_color = fg
                    break
            typer.secho(header, fg=header_color if color else None)
            for label, line in lines:
                if not line:
                    typer.echo("")
                    continue
                fg = None
                if color:
                    if label == "ERROR":
                        fg = typer.colors.RED
                    elif label == "WARN":
                        fg = typer.colors.YELLOW
                    elif label == "INFO":
                        fg = typer.colors.BLUE
                typer.secho(line, fg=fg)

    if not result.conforms:
        raise UsageError("SHACL validation failed.")
    if result.warning_count:
        raise UsageError("SHACL validation warnings found.")

    typer.echo("OK: no errors or warnings.")
