#!/usr/bin/env python3
"""Materialize, validate and compact the return knowledge-base indexes."""
from __future__ import annotations

import argparse
import copy
import re
import sys
from pathlib import Path
from typing import Any

import yaml

SPECS = {
    "timeline": ("NODE-", "data/timeline/nodes.yaml", "nodes", "timeline.yaml"),
    "characters": ("CHAR-", "data/characters/characters.yaml", "characters", "characters.yaml"),
    "gifts": ("GIFT-", "data/system/gifts.yaml", "gifts", "gifts.yaml"),
    "artifacts": ("ART-", "data/artifacts/artifacts.yaml", "artifacts", "artifacts.yaml"),
}
ID_RE = re.compile(r"^(NODE|CHAR|GIFT|ART)-(\d+)$")
RUN_RE = re.compile(r"^RUN-(\d+)$")


def load(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise RuntimeError(f"invalid YAML {path}: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise RuntimeError(f"top-level YAML must be a mapping: {path}")
    return data


def dump(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )


def extend_unique(items: list[Any], values: list[Any]) -> list[Any]:
    out = copy.deepcopy(items)
    for value in values:
        if value not in out:
            out.append(copy.deepcopy(value))
    return out


def merge_value(old: Any, new: Any) -> Any:
    if isinstance(old, dict) and isinstance(new, dict):
        out = copy.deepcopy(old)
        for key, value in new.items():
            out[key] = merge_value(out[key], value) if key in out else copy.deepcopy(value)
        return out
    if isinstance(old, list) and isinstance(new, list):
        return extend_unique(old, new)
    return copy.deepcopy(new)


def patch(target: dict[str, Any], updates: dict[str, Any]) -> None:
    for key, value in updates.items():
        if key.endswith("_add"):
            dest = key[:-4]
            values = value if isinstance(value, list) else [value]
            if dest not in target:
                target[dest] = copy.deepcopy(value)
            elif isinstance(target[dest], list):
                target[dest] = extend_unique(target[dest], values)
            elif target[dest] != value:
                target[dest] = extend_unique([target[dest]], values)
        elif key.endswith("_remove"):
            dest = key[:-7]
            values = value if isinstance(value, list) else [value]
            if isinstance(target.get(dest), list):
                target[dest] = [item for item in target[dest] if item not in values]
            elif target.get(dest) in values:
                target.pop(dest, None)
        elif key.endswith("_set"):
            target[key[:-4]] = copy.deepcopy(value)
        elif isinstance(value, dict) and isinstance(target.get(key), dict):
            patch(target[key], value)
        else:
            target[key] = merge_value(target[key], value) if key in target else copy.deepcopy(value)


def merge_record(old: dict[str, Any] | None, new: dict[str, Any]) -> dict[str, Any]:
    direct = {key: value for key, value in new.items() if key != "update"}
    out = merge_value(old or {}, direct)
    if "update" in new:
        if not isinstance(new["update"], dict):
            raise RuntimeError(f"update must be a mapping: {new.get('id')}")
        patch(out, new["update"])
    return out


def records(value: Any):
    if isinstance(value, dict):
        if isinstance(value.get("id"), str) and ID_RE.match(value["id"]):
            yield value
            return
        for child in value.values():
            yield from records(child)
    elif isinstance(value, list):
        for child in value:
            yield from records(child)


def run_number(value: Any) -> int | None:
    match = RUN_RE.match(str(value or ""))
    return int(match.group(1)) if match else None


def run_order(item: tuple[Path, dict[str, Any]]) -> tuple[int, str]:
    path, doc = item
    number = run_number(doc.get("run_id"))
    return (number if number is not None else -1, path.as_posix())


def extension_documents(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    documents = [
        (path, load(path))
        for path in sorted((root / "data/extensions").rglob("*.yaml"))
    ]
    documents.sort(key=run_order)
    return documents


def latest_extension_run(
    extension_docs: list[tuple[Path, dict[str, Any]]],
) -> tuple[int, str] | None:
    runs = [
        (number, str(doc["run_id"]))
        for _path, doc in extension_docs
        if (number := run_number(doc.get("run_id"))) is not None
    ]
    return max(runs) if runs else None


def id_key(value: str) -> tuple[str, int]:
    match = ID_RE.match(value)
    return (match.group(1), int(match.group(2))) if match else (value, 10**9)


def build(root: Path) -> dict[str, dict[str, Any]]:
    extension_docs = extension_documents(root)
    output: dict[str, dict[str, Any]] = {}
    for name, (prefix, base_rel, key, _filename) in SPECS.items():
        base = load(root / base_rel)
        base_records = base.get(key, [])
        if not isinstance(base_records, list):
            raise RuntimeError(f"{base_rel}:{key} must be a list")

        compacted_run = base.get("compacted_through_run")
        compacted_number = run_number(compacted_run)
        if compacted_run is not None and compacted_number is None:
            raise RuntimeError(
                f"invalid compacted_through_run in {base_rel}: {compacted_run}"
            )

        merged: dict[str, dict[str, Any]] = {}
        for record in base_records:
            rid = record.get("id") if isinstance(record, dict) else None
            if not isinstance(rid, str) or not rid.startswith(prefix) or rid in merged:
                raise RuntimeError(f"invalid or duplicate base record in {base_rel}: {rid}")
            merged[rid] = copy.deepcopy(record)

        used_docs, dates = 0, []
        for _path, doc in extension_docs:
            document_number = run_number(doc.get("run_id"))
            if (
                compacted_number is not None
                and document_number is not None
                and document_number <= compacted_number
            ):
                continue

            used = False
            for record in records(doc):
                rid = record["id"]
                if rid.startswith(prefix):
                    merged[rid] = merge_record(merged.get(rid), record)
                    used = True
            if used:
                used_docs += 1
                if isinstance(doc.get("updated_at"), str):
                    dates.append(doc["updated_at"])

        result = {k: copy.deepcopy(v) for k, v in base.items() if k != key}
        if dates:
            result["updated_at"] = max(dates + [str(result.get("updated_at", ""))])
        result["index_mode"] = "materialized"
        materialized_from: dict[str, Any] = {
            "base": base_rel,
            "extensions": "data/extensions/**/*.yaml",
            "extension_files": used_docs,
        }
        if compacted_run is not None:
            materialized_from["compacted_through_run"] = compacted_run
        result["materialized_from"] = materialized_from
        result[key] = [merged[rid] for rid in sorted(merged, key=id_key)]
        output[name] = result
    return output


def write_generated(root: Path, output_dir: Path) -> None:
    indexes = build(root)
    for name, (_prefix, _base, _key, filename) in SPECS.items():
        dump(output_dir / filename, indexes[name])


def compact(root: Path) -> str | None:
    extension_docs = extension_documents(root)
    latest = latest_extension_run(extension_docs)
    indexes = build(root)

    for name, (_prefix, base_rel, _key, _filename) in SPECS.items():
        data = copy.deepcopy(indexes[name])
        data.pop("index_mode", None)
        data.pop("materialized_from", None)
        if latest is not None:
            data["compacted_through_run"] = latest[1]
        dump(root / base_rel, data)

    return latest[1] if latest is not None else None


def validate(root: Path, generated_dir: Path | None = None) -> list[str]:
    errors: list[str] = []
    for top in (root / "data", root / ".project", root / "sources/evidence"):
        if top.exists():
            for path in sorted(top.rglob("*.yaml")):
                try:
                    load(path)
                except RuntimeError as exc:
                    errors.append(str(exc))
    try:
        indexes = build(root)
    except RuntimeError as exc:
        return errors + [str(exc)]

    maps: dict[str, dict[str, dict[str, Any]]] = {}
    for name, (_prefix, _base, key, filename) in SPECS.items():
        values = indexes[name].get(key, [])
        maps[name] = {item["id"]: item for item in values}
        if generated_dir:
            path = generated_dir / filename
            if not path.exists() or load(path) != indexes[name]:
                errors.append(f"generated index missing or stale: {path}")

    nodes = maps["timeline"]
    ranges = []
    for rid, node in nodes.items():
        chapters = node.get("chapters", {})
        start, end = chapters.get("start"), chapters.get("end")
        if not isinstance(start, int) or not isinstance(end, int) or start > end:
            errors.append(f"invalid chapter range: {rid}")
        else:
            ranges.append((start, end, rid))
    ranges.sort()
    for left, right in zip(ranges, ranges[1:]):
        if right[0] <= left[1]:
            errors.append(f"timeline overlap: {left[2]} and {right[2]}")

    def check_paths(value: Any, rid: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if (
                    key in {"document", "evidence", "profile"}
                    and isinstance(child, str)
                    and not (root / child).exists()
                ):
                    errors.append(f"missing file for {rid}: {child}")
                else:
                    check_paths(child, rid)
        elif isinstance(value, list):
            for child in value:
                check_paths(child, rid)

    for group in maps.values():
        for rid, item in group.items():
            check_paths(item, rid)
    for rid, gift in maps["gifts"].items():
        if isinstance(gift.get("node"), str) and gift["node"] not in nodes:
            errors.append(f"unknown node in {rid}: {gift['node']}")
    for rid, item in maps["artifacts"].items():
        related_nodes = item.get("related_nodes", [])
        for node in related_nodes if isinstance(related_nodes, list) else []:
            if node not in nodes:
                errors.append(f"unknown node in {rid}: {node}")

    state = load(root / ".project/STATE.yaml")
    metrics = load(root / ".project/METRICS.yaml")
    progress, coverage = state.get("progress", {}), metrics.get("coverage", {})
    checks = [
        ("timeline", "nodes_completed", "timeline_nodes"),
        ("characters", "characters_documented", "characters_documented"),
        ("gifts", "gift_events", "gift_events"),
        ("artifacts", "artifact_records", "artifact_records"),
    ]
    for name, state_key, metric_key in checks:
        actual = len(maps[name])
        if isinstance(progress.get(state_key), int) and progress[state_key] != actual:
            errors.append(f"STATE {state_key}={progress[state_key]}, actual={actual}")
        if isinstance(coverage.get(metric_key), int) and coverage[metric_key] != actual:
            errors.append(f"METRICS {metric_key}={coverage[metric_key]}, actual={actual}")
    if (
        isinstance(progress.get("last_completed_node"), str)
        and progress["last_completed_node"] not in nodes
    ):
        errors.append(f"unknown last_completed_node: {progress['last_completed_node']}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "validate", "compact"))
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, default=Path("data/generated"))
    parser.add_argument("--generated-dir", type=Path)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    try:
        if args.command == "build":
            out = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
            write_generated(root, out)
            print(f"generated canonical indexes in {out}")
        elif args.command == "compact":
            compacted_through = compact(root)
            suffix = f" through {compacted_through}" if compacted_through else ""
            print(f"compacted canonical base indexes{suffix}")
        else:
            generated = args.generated_dir
            if generated and not generated.is_absolute():
                generated = root / generated
            errors = validate(root, generated)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print("validation passed")
    except (OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
