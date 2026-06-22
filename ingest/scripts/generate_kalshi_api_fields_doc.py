#!/usr/bin/env python3
"""Generate Kalshi API response field reference from official OpenAPI spec.

Downloads https://docs.kalshi.com/openapi.yaml (Predictions REST API) and writes
docs/architecture/KALSHI_API_RESPONSE_FIELDS.md.

NO REAL TRADING — documentation generator only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import textwrap
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML required: pip install pyyaml") from exc

OPENAPI_URL = "https://docs.kalshi.com/openapi.yaml"
DEFAULT_SPEC_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "specs" / "kalshi_openapi.yaml"
)
DEFAULT_OUT_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "architecture"
    / "KALSHI_API_RESPONSE_FIELDS.md"
)

# Endpoints Console 2 / Kalshi paper loop touch (for a usage appendix).
_KMIA_ENDPOINTS = {
    "GET /markets",
    "GET /markets/{ticker}",
    "GET /markets/{ticker}/orderbook",
    "GET /markets/orderbooks",
    "GET /events",
    "GET /series/{series_ticker}/markets/{ticker}/candlesticks",
    "GET /markets/trades",
}


def _fetch_openapi(url: str) -> bytes:
    try:
        with urllib.request.urlopen(url, timeout=120) as resp:
            return resp.read()
    except Exception:
        # macOS Python often lacks CA bundle; curl uses system trust store.
        proc = subprocess.run(
            ["curl", "-fsSL", url],
            check=True,
            capture_output=True,
        )
        return proc.stdout


def _load_openapi(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


class SchemaResolver:
    def __init__(self, spec: dict[str, Any]) -> None:
        self.spec = spec
        self.schemas: dict[str, Any] = spec.get("components", {}).get("schemas", {})
        self._seen: set[str] = set()

    def resolve(self, node: Any, depth: int = 0) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                name = _ref_name(node["$ref"])
                if name in self._seen and depth > 0:
                    return {"$ref": name, "_circular": True}
                self._seen.add(name)
                target = self.schemas.get(name, {})
                merged = self.resolve(target, depth + 1)
                self._seen.discard(name)
                return merged
            out: dict[str, Any] = {}
            for key, val in node.items():
                if key == "allOf":
                    merged_props: dict[str, Any] = {}
                    merged_required: list[str] = []
                    for part in val or []:
                        resolved = self.resolve(part, depth + 1)
                        if isinstance(resolved, dict):
                            merged_props.update(resolved.get("properties") or {})
                            merged_required.extend(resolved.get("required") or [])
                    out["properties"] = merged_props
                    if merged_required:
                        out["required"] = sorted(set(merged_required))
                elif key in ("oneOf", "anyOf"):
                    out[key] = [self.resolve(v, depth + 1) for v in (val or [])]
                else:
                    out[key] = self.resolve(val, depth + 1)
            return out
        if isinstance(node, list):
            return [self.resolve(v, depth + 1) for v in node]
        return node

    def flatten_fields(
        self,
        schema: Any,
        *,
        prefix: str = "",
        rows: Optional[list[dict[str, Any]]] = None,
    ) -> list[dict[str, Any]]:
        rows = rows if rows is not None else []
        if not isinstance(schema, dict):
            return rows

        if schema.get("_circular"):
            rows.append({
                "path": prefix or "(root)",
                "type": f"$ref → {schema.get('$ref')}",
                "required": False,
                "description": "Circular reference truncated",
            })
            return rows

        schema_type = schema.get("type")
        description = (schema.get("description") or "").strip()

        if schema_type == "array" or "items" in schema:
            items = schema.get("items") or {}
            item_prefix = f"{prefix}[]" if prefix else "[]"
            rows.append({
                "path": item_prefix,
                "type": "array",
                "required": False,
                "description": description,
            })
            self.flatten_fields(items, prefix=item_prefix, rows=rows)
            return rows

        props = schema.get("properties") or {}
        required = set(schema.get("required") or [])
        if not props and schema_type:
            rows.append({
                "path": prefix or "(root)",
                "type": self._type_str(schema),
                "required": False,
                "description": description,
            })
            return rows

        for name, prop in props.items():
            path = f"{prefix}.{name}" if prefix else name
            if isinstance(prop, dict) and prop.get("$ref"):
                prop = self.resolve(prop)
            if not isinstance(prop, dict):
                continue
            if prop.get("properties") or prop.get("allOf") or prop.get("$ref"):
                resolved = self.resolve(prop)
                self.flatten_fields(
                    resolved,
                    prefix=path,
                    rows=rows,
                )
            elif prop.get("type") == "array" or "items" in prop:
                rows.append({
                    "path": path,
                    "type": "array",
                    "required": name in required,
                    "description": (prop.get("description") or "").strip(),
                })
                self.flatten_fields(prop.get("items") or {}, prefix=f"{path}[]", rows=rows)
            else:
                rows.append({
                    "path": path,
                    "type": self._type_str(prop),
                    "required": name in required,
                    "description": (prop.get("description") or "").strip(),
                })
        return rows

    @staticmethod
    def _type_str(prop: dict[str, Any]) -> str:
        t = prop.get("type", "object")
        fmt = prop.get("format")
        if prop.get("enum"):
            vals = ", ".join(str(v) for v in prop["enum"][:8])
            suffix = "…" if len(prop["enum"]) > 8 else ""
            return f"enum({vals}{suffix})"
        if fmt:
            t = f"{t} ({fmt})"
        if prop.get("nullable"):
            t = f"{t} | null"
        return str(t)


def _response_schema(operation: dict[str, Any]) -> Optional[str]:
    responses = operation.get("responses") or {}
    for code in ("200", "201", "204"):
        block = responses.get(code)
        if not block:
            continue
        content = block.get("content") or {}
        app_json = content.get("application/json") or {}
        schema = app_json.get("schema") or {}
        if "$ref" in schema:
            return _ref_name(schema["$ref"])
        if schema.get("type") == "array" and schema.get("items", {}).get("$ref"):
            return f"array<{_ref_name(schema['items']['$ref'])}>"
    return None


def _md_table(rows: list[dict[str, Any]], max_rows: Optional[int] = None) -> str:
    if not rows:
        return "_No fields resolved._\n"
    lines = [
        "| Field | Type | Required | Description |",
        "|-------|------|----------|-------------|",
    ]
    shown = rows[:max_rows] if max_rows else rows
    for row in shown:
        desc = (row.get("description") or "").replace("\n", " ").replace("|", "\\|")
        if len(desc) > 200:
            desc = desc[:197] + "…"
        req = "yes" if row.get("required") else ""
        lines.append(
            f"| `{row['path']}` | {row.get('type', '')} | {req} | {desc} |"
        )
    if max_rows and len(rows) > max_rows:
        lines.append(f"\n_…and {len(rows) - max_rows} more fields (see schema appendix)._")
    return "\n".join(lines) + "\n"


def generate_markdown(spec: dict[str, Any], *, spec_source: str) -> str:
    resolver = SchemaResolver(spec)
    version = (spec.get("info") or {}).get("version", "?")
    title = (spec.get("info") or {}).get("title", "Kalshi Trade API")
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    paths = spec.get("paths") or {}
    endpoints: list[dict[str, Any]] = []
    for path, methods in sorted(paths.items()):
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            if not isinstance(op, dict):
                continue
            schema_name = _response_schema(op)
            endpoints.append({
                "method": method.upper(),
                "path": path,
                "operation_id": op.get("operationId", ""),
                "summary": op.get("summary", ""),
                "tags": op.get("tags") or ["untagged"],
                "schema": schema_name,
            })

    by_tag: dict[str, list[dict[str, Any]]] = {}
    for ep in endpoints:
        tag = ep["tags"][0]
        by_tag.setdefault(tag, []).append(ep)

    parts: list[str] = [
        "# Kalshi API response fields (Predictions REST)",
        "",
        f"**Generated:** {generated}  ",
        f"**Source:** [{spec_source}]({spec_source})  ",
        f"**OpenAPI:** {title} v{version}  ",
        "**Scope:** All documented REST response schemas from Kalshi's official Predictions API spec.  ",
        "**Mode:** Read-only reference — no trading.",
        "",
        "Regenerate:",
        "",
        "```bash",
        "python3 ingest/scripts/generate_kalshi_api_fields_doc.py",
        "```",
        "",
        "Official docs: [docs.kalshi.com](https://docs.kalshi.com/welcome) · "
        "WebSocket fields are in `asyncapi.yaml` (not included here).",
        "",
        "---",
        "",
        "## KMIA endpoints we use",
        "",
        "Console 2 / paper loop primarily calls:",
        "",
    ]
    for ep in sorted(_KMIA_ENDPOINTS):
        parts.append(f"- `{ep}`")
    parts.extend(["", "---", "", "## Endpoints by tag", ""])

    for tag in sorted(by_tag):
        parts.append(f"### {tag}")
        parts.append("")
        for ep in by_tag[tag]:
            key = f"{ep['method']} {ep['path']}"
            kmia = " **← KMIA**" if key in _KMIA_ENDPOINTS else ""
            parts.append(f"#### `{key}`{kmia}")
            parts.append("")
            if ep["summary"]:
                parts.append(f"{ep['summary']}  ")
            parts.append(f"_operationId:_ `{ep['operation_id']}`  ")
            if ep["schema"]:
                parts.append(f"_200 schema:_ `{ep['schema']}`")
            parts.append("")
            if ep["schema"] and ep["schema"].startswith("array<"):
                inner = ep["schema"][6:-1]
                schema = resolver.resolve({"$ref": f"#/components/schemas/{inner}"})
            elif ep["schema"]:
                schema = resolver.resolve({"$ref": f"#/components/schemas/{ep['schema']}"})
            else:
                schema = {}
                parts.append("_No JSON response schema in OpenAPI for HTTP 200._\n")
                continue
            rows = resolver.flatten_fields(schema)
            parts.append(_md_table(rows, max_rows=80))
            parts.append("")

    # Full schema appendix
    parts.extend(["---", "", "## Schema appendix (all response types)", ""])
    schemas = spec.get("components", {}).get("schemas", {})
    for name in sorted(schemas):
        parts.append(f"### `{name}`")
        parts.append("")
        resolved = resolver.resolve({"$ref": f"#/components/schemas/{name}"})
        desc = (resolved.get("description") or schemas[name].get("description") or "").strip()
        if desc:
            parts.append(desc)
            parts.append("")
        rows = resolver.flatten_fields(resolved)
        parts.append(_md_table(rows, max_rows=200))
        if len(rows) > 200:
            parts.append(f"_Total fields: {len(rows)}_\n")
        parts.append("")

    parts.extend([
        "---",
        "",
        "## Notes",
        "",
        "- **Fixed-point strings:** Many price/size fields use `*_fp` or `*_dollars` string "
        "types (e.g. `\"0.4200\"`, `\"13.00\"`). See "
        "[Fixed-Point Migration](https://docs.kalshi.com/getting_started/fixed_point_migration).",
        "- **Orderbook:** API returns bids only; YES ask = 100¢ − NO bid (see orderbook docs).",
        "- **Not in this file:** Perps API (`perps_openapi.yaml`), WebSocket (`asyncapi.yaml`), "
        "undocumented endpoints, or fields absent from the published spec.",
        "- **Vendor snapshot:** `docs/specs/kalshi_openapi.yaml`",
        "",
    ])
    return "\n".join(parts)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Kalshi API response fields doc.")
    parser.add_argument("--spec-url", default=OPENAPI_URL)
    parser.add_argument("--spec-path", type=Path, default=DEFAULT_SPEC_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT_PATH)
    parser.add_argument("--offline", action="store_true", help="Use cached spec only")
    args = parser.parse_args(argv)

    args.spec_path.parent.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    if args.offline:
        if not args.spec_path.is_file():
            raise SystemExit(f"Offline mode but spec missing: {args.spec_path}")
        spec = _load_openapi(args.spec_path)
        source = str(args.spec_path)
    else:
        print(f"Fetching {args.spec_url} …")
        raw = _fetch_openapi(args.spec_url)
        args.spec_path.write_bytes(raw)
        spec = yaml.safe_load(raw)
        print(f"Cached spec: {args.spec_path}")
        source = args.spec_url

    md = generate_markdown(spec, spec_source=source)
    args.output.write_text(md, encoding="utf-8")
    n_paths = len(spec.get("paths") or {})
    n_schemas = len(spec.get("components", {}).get("schemas") or {})
    print(f"Wrote {args.output} ({n_paths} paths, {n_schemas} schemas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
