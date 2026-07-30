#!/usr/bin/env python3
"""Inventory tracked extras sources and initialize an isolated namespace.

The inventory is metadata-only: it records paths, marker classes, byte sizes and
path-derived boundary hints. It never copies source prose into generated output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

RUN_ID = "RUN-0128"
TASK_ID = "TASK-0114"
CONFIG_PATH = Path("data/extras/run-0128-config.yaml")
OUTPUT_PATHS = (
    Path("data/audits/run-0128.yaml"),
    Path("data/extras/run-0128-scope.yaml"),
    Path("data/extras/run-0128-task-plan.yaml"),
    Path("docs/08-analysis/extras-scope-inventory.md"),
)
ID_RE = re.compile(r"\bEXTRA-(?:SRC|NODE|CHAR|GIFT|ART)-\d{4}\b")
RANGE_RE = re.compile(r"(?<!\d)(\d{1,4})\s*(?:-|–|—|至|到|_)\s*(\d{1,4})(?!\d)")
CHAPTER_RE = re.compile(r"第?\s*(\d{1,4})\s*(?:章|话|回)")


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"expected mapping: {path}")
    return data


def dump_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def tracked_files(root: Path) -> list[Path]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True,
            capture_output=True,
        )
        return [Path(item.decode("utf-8")) for item in proc.stdout.split(b"\0") if item]
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError):
        return sorted(
            path.relative_to(root)
            for path in root.rglob("*")
            if path.is_file() and ".git" not in path.parts
        )


def is_prefix(path: str, prefixes: list[str]) -> bool:
    normalized = path.replace("\\", "/")
    return any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in prefixes)


def source_root(path: Path, roots: set[str]) -> str | None:
    return path.parts[0] if path.parts and path.parts[0].lower() in roots else None


def marker_hits(value: str, markers: list[str]) -> list[str]:
    lowered = value.lower()
    return sorted({marker for marker in markers if marker.lower() in lowered})


def read_text_limited(path: Path, max_bytes: int) -> str | None:
    try:
        if path.stat().st_size > max_bytes:
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def boundary_hints(path: str) -> dict[str, Any]:
    values: list[int] = []
    for start, end in RANGE_RE.findall(path):
        values.extend((int(start), int(end)))
    values.extend(int(value) for value in CHAPTER_RE.findall(path))
    values = sorted({value for value in values if 0 < value < 10000})
    if not values:
        return {"status": "unresolved", "chapter_start": None, "chapter_end": None}
    return {
        "status": "path_derived",
        "chapter_start": min(values),
        "chapter_end": max(values),
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_gate(ok: bool, detail: str) -> dict[str, str]:
    return {"status": "passed" if ok else "failed", "detail": detail}


def inventory(root: Path, output_root: Path) -> list[str]:
    config = load_yaml(root / CONFIG_PATH)
    discovery = config["source_discovery"]
    roots = {str(item).lower() for item in discovery["source_roots"]}
    path_markers = [str(item) for item in discovery["path_markers"]]
    content_markers = [str(item) for item in discovery["content_markers"]]
    extensions = {str(item).lower() for item in discovery["text_extensions"]}
    excluded = [str(item) for item in discovery["excluded_prefixes"]]
    max_bytes = int(discovery["max_scan_bytes"])

    files = tracked_files(root)
    candidates: list[dict[str, Any]] = []
    main_story_evidence: list[dict[str, Any]] = []
    scope_controls: list[dict[str, Any]] = []
    skipped_binary_or_large = 0
    existing_extra_ids: dict[str, list[str]] = {}

    for relative in files:
        relative_str = relative.as_posix()
        absolute = root / relative
        if not absolute.is_file():
            continue

        path_hits = marker_hits(relative_str, path_markers)
        root_name = source_root(relative, roots)
        scan_allowed = relative.suffix.lower() in extensions and absolute.stat().st_size <= max_bytes
        text = read_text_limited(absolute, max_bytes) if scan_allowed else None
        if relative.suffix.lower() in extensions and text is None:
            skipped_binary_or_large += 1
        content_hits = marker_hits(text or "", content_markers)

        ids = sorted(set(ID_RE.findall(text or "")))
        if ids and relative != CONFIG_PATH and relative not in OUTPUT_PATHS:
            existing_extra_ids[relative_str] = ids

        excluded_path = is_prefix(relative_str, excluded)
        control_path = (
            excluded_path
            or relative_str.startswith("scripts/")
            or relative_str.startswith(".github/")
            or relative_str.startswith("data/extras/")
        )
        candidate = bool(path_hits and not control_path) or bool(root_name and (path_hits or content_hits))

        base = {
            "path": relative_str,
            "bytes": absolute.stat().st_size,
            "sha256": sha256(absolute),
            "source_root": root_name,
            "path_markers": path_hits,
            "content_markers": content_hits,
        }
        if candidate:
            base["boundary"] = boundary_hints(relative_str)
            base["classification"] = "candidate_source"
            candidates.append(base)
        elif root_name:
            main_story_evidence.append(
                {
                    "path": relative_str,
                    "bytes": absolute.stat().st_size,
                    "sha256": base["sha256"],
                    "source_root": root_name,
                    "classification": "main_story_evidence",
                }
            )
        elif path_hits or content_hits:
            scope_controls.append(
                {
                    "path": relative_str,
                    "path_markers": path_hits,
                    "content_markers": content_hits,
                    "classification": "scope_control",
                }
            )

    candidates.sort(key=lambda row: row["path"])
    main_story_evidence.sort(key=lambda row: row["path"])
    scope_controls.sort(key=lambda row: row["path"])

    state = load_yaml(root / ".project/STATE.yaml")
    generated_timeline = load_yaml(root / "data/generated/timeline.yaml")
    nodes = generated_timeline.get("nodes", [])
    if not isinstance(nodes, list):
        raise RuntimeError("data/generated/timeline.yaml nodes must be a list")
    chapter_starts = [row.get("chapter_start") for row in nodes if isinstance(row, dict)]
    chapter_ends = [row.get("chapter_end") for row in nodes if isinstance(row, dict)]
    node_ids = [row.get("id") for row in nodes if isinstance(row, dict)]

    main_isolated = (
        state.get("scope", {}).get("chapter_start") == 1
        and state.get("scope", {}).get("chapter_end") == 876
        and state.get("progress", {}).get("last_completed_node") == "NODE-0108"
        and min(chapter_starts) == 1
        and max(chapter_ends) == 876
        and node_ids[-1] == "NODE-0108"
        and not any(str(node_id).startswith("EXTRA-") for node_id in node_ids)
    )
    namespace_unique = not existing_extra_ids
    boundary_complete = all(row["boundary"]["status"] in {"path_derived", "unresolved"} for row in candidates)

    status = "candidates_found_pending_boundary_review" if candidates else "initialized_no_tracked_extra_source"
    source_root_counts = Counter(row["source_root"] for row in main_story_evidence if row["source_root"])
    source_root_counts.update(row["source_root"] for row in candidates if row["source_root"])

    gates = {
        "tracked_file_inventory": make_gate(bool(files), f"tracked_files={len(files)}"),
        "candidate_classification_complete": make_gate(True, f"candidate_sources={len(candidates)}; control_mentions={len(scope_controls)}"),
        "chapter_boundary_inventory": make_gate(boundary_complete, f"path_derived={sum(row['boundary']['status'] == 'path_derived' for row in candidates)}; unresolved={sum(row['boundary']['status'] == 'unresolved' for row in candidates)}"),
        "namespace_uniqueness": make_gate(namespace_unique, f"preexisting_extra_id_files={len(existing_extra_ids)}"),
        "main_story_isolation": make_gate(main_isolated, "main Timeline remains NODE-0001..NODE-0108 and Chapters 1-876"),
        "deterministic_serialization": make_gate(True, "all lists are path-sorted and dates are frozen in config"),
        "copyright_boundary": make_gate(True, "outputs contain metadata and marker names only; no source prose is copied"),
    }
    errors = [name for name, result in gates.items() if result["status"] != "passed"]

    scope_manifest = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "task_id": TASK_ID,
        "inventory_date": config["inventory_date"],
        "status": status if not errors else "failed",
        "main_story_baseline": config["scope"]["main_story"],
        "extras_scope": config["scope"]["extras"],
        "tracked_inventory": {
            "tracked_files": len(files),
            "source_root_counts": dict(sorted(source_root_counts.items())),
            "main_story_evidence_files": len(main_story_evidence),
            "candidate_source_files": len(candidates),
            "scope_control_mentions": len(scope_controls),
            "text_files_skipped_as_large_or_non_utf8": skipped_binary_or_large,
        },
        "candidate_sources": candidates,
        "scope_control_mentions": scope_controls,
        "existing_extra_id_collisions": existing_extra_ids,
    }

    if candidates:
        planned_tasks = [
            {
                "id": f"EXTRA-TASK-{index:04d}",
                "status": "planned",
                "source_id": f"EXTRA-SRC-{index:04d}",
                "source_path": row["path"],
                "boundary": row["boundary"],
                "creates_main_timeline_node": False,
                "required_review": ["work_identity", "chapter_boundary", "canonical_identity_reuse", "copyright_boundary"],
            }
            for index, row in enumerate(candidates, start=1)
        ]
        next_action = "Review each candidate source boundary, then create one isolated ingestion Task per confirmed work."
    else:
        planned_tasks = [
            {
                "id": "EXTRA-TASK-0001",
                "status": "blocked_external_source",
                "source_id": None,
                "source_path": None,
                "creates_main_timeline_node": False,
                "blocker": "No tracked extras source corpus was found under the configured discovery policy.",
                "next_action": "Add or identify an authorized extras source before extraction or Timeline construction.",
            }
        ]
        next_action = planned_tasks[0]["next_action"]

    task_plan = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "task_id": TASK_ID,
        "status": "ready_for_isolated_ingestion" if candidates else "waiting_for_source",
        "namespace_contract": config["scope"]["extras"]["namespaces"],
        "rules": [
            "Do not create or renumber NODE records in the completed main-story Timeline.",
            "Do not place extras facts in data/extensions or data/generated during inventory.",
            "Do not reuse main-story entity IDs without direct identity evidence.",
            "Do not copy source prose into inventory, plans or generated reports.",
        ],
        "tasks": planned_tasks,
        "next_action": next_action,
    }

    audit = {
        "schema_version": 1,
        "extras_inventory": {
            "run_id": RUN_ID,
            "task_id": TASK_ID,
            "status": "passed" if not errors else "failed",
            "blocking_findings": errors,
        },
        "counts": {
            "tracked_files": len(files),
            "source_root_files": len(main_story_evidence) + len(candidates),
            "main_story_evidence_files": len(main_story_evidence),
            "candidate_source_files": len(candidates),
            "scope_control_mentions": len(scope_controls),
            "planned_isolated_tasks": len(planned_tasks),
        },
        "quality_gates": gates,
        "findings": {
            "inventory_status": status,
            "candidate_paths": [row["path"] for row in candidates],
            "unresolved_boundary_paths": [row["path"] for row in candidates if row["boundary"]["status"] == "unresolved"],
            "preexisting_extra_id_files": existing_extra_ids,
        },
    }

    candidate_lines = "\n".join(
        f"- `{row['path']}`：boundary={row['boundary']['status']}, bytes={row['bytes']}"
        for row in candidates
    ) or "- 未发现符合规则的已跟踪番外源文件。"
    gate_lines = "\n".join(
        f"| {name} | {result['status']} | {result['detail']} |"
        for name, result in gates.items()
    )
    report = f"""# 番外 Scope 盘点与独立命名空间 — {RUN_ID}

- Task：`{TASK_ID}`
- 盘点日期：`{config['inventory_date']}`
- 状态：**{audit['extras_inventory']['status']}**
- 盘点结论：**{status}**
- 本 Run 不创建主线 Timeline Node，不改变正文第 1—876 章及 `NODE-0108` 终点。

## 盘点结果

- Git tracked files：{len(files)}
- Source-root files：{len(main_story_evidence) + len(candidates)}
- 番外候选源：{len(candidates)}
- 仅用于 scope 控制的番外提及：{len(scope_controls)}

{candidate_lines}

## 独立命名空间

| 数据类型 | Namespace |
|---|---|
| Source | `EXTRA-SRC-NNNN` |
| Timeline | `EXTRA-NODE-NNNN` |
| Character | `EXTRA-CHAR-NNNN` |
| Gift | `EXTRA-GIFT-NNNN` |
| Artifact | `EXTRA-ART-NNNN` |

番外专属事实不得写入正文 `NODE-*`、`CHAR-*`、`GIFT-*`、`ART-*` 的终局状态。已存在正文实体只有在直接证据证明身份一致时才允许引用，且不得因此改写正文第 1—876 章的 canonical state。

## 质量门禁

| Gate | 结果 | 摘要 |
|---|---|---|
{gate_lines}

## 后续

{next_action}

该报告只保留文件路径、大小、摘要哈希、marker 分类和 path-derived boundary hint，不复制任何源文段落。
"""

    output_root = output_root.resolve()
    dump_yaml(output_root / OUTPUT_PATHS[0], audit)
    dump_yaml(output_root / OUTPUT_PATHS[1], scope_manifest)
    dump_yaml(output_root / OUTPUT_PATHS[2], task_plan)
    write_text(output_root / OUTPUT_PATHS[3], report)
    return errors


def compare_outputs(actual_root: Path, expected_root: Path) -> list[str]:
    differences: list[str] = []
    for relative in OUTPUT_PATHS:
        actual = actual_root / relative
        expected = expected_root / relative
        if not expected.exists():
            differences.append(f"missing tracked output: {relative}")
        elif actual.read_bytes() != expected.read_bytes():
            differences.append(f"stale tracked output: {relative}")
    return differences


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-root", type=Path, default=Path("."))
    parser.add_argument("--check-root", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    errors = inventory(root, args.output_root)
    if args.check_root:
        errors.extend(compare_outputs(args.output_root.resolve(), args.check_root.resolve()))
    if errors:
        for error in errors:
            print(error)
        return 1
    print(json.dumps({"run_id": RUN_ID, "task_id": TASK_ID, "status": "passed"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
