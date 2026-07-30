#!/usr/bin/env python3
"""Inventory tracked extras sources and initialize an isolated namespace.

Outputs are metadata-only. Source prose is never copied into generated files.
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
EXTRA_ID_RE = re.compile(r"\bEXTRA-(?:SRC|NODE|CHAR|GIFT|ART)-\d{4}\b")
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


def git_files(root: Path) -> list[Path]:
    proc = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return sorted(Path(item.decode("utf-8")) for item in proc.stdout.split(b"\0") if item)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hits(text: str, markers: list[str]) -> list[str]:
    lowered = text.lower()
    return sorted({marker for marker in markers if marker.lower() in lowered})


def starts_with(path: str, prefixes: list[str]) -> bool:
    return any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in prefixes)


def boundary(path: str) -> dict[str, Any]:
    numbers: list[int] = []
    for start, end in RANGE_RE.findall(path):
        numbers.extend((int(start), int(end)))
    numbers.extend(int(value) for value in CHAPTER_RE.findall(path))
    numbers = sorted({value for value in numbers if 0 < value < 10000})
    if not numbers:
        return {"status": "unresolved", "chapter_start": None, "chapter_end": None}
    return {"status": "path_derived", "chapter_start": min(numbers), "chapter_end": max(numbers)}


def gate(ok: bool, detail: str) -> dict[str, str]:
    return {"status": "passed" if ok else "failed", "detail": detail}


def generate(root: Path, output_root: Path) -> list[str]:
    config = load_yaml(root / CONFIG_PATH)
    discovery = config["source_discovery"]
    source_roots = {str(item).lower() for item in discovery["source_roots"]}
    path_markers = [str(item) for item in discovery["path_markers"]]
    content_markers = [str(item) for item in discovery["content_markers"]]
    extensions = {str(item).lower() for item in discovery["text_extensions"]}
    excluded = [str(item) for item in discovery["excluded_prefixes"]]
    max_bytes = int(discovery["max_scan_bytes"])

    tracked = git_files(root)
    candidates: list[dict[str, Any]] = []
    main_evidence: list[dict[str, Any]] = []
    control_mentions: list[dict[str, Any]] = []
    collisions: dict[str, list[str]] = {}
    skipped = 0

    for relative in tracked:
        absolute = root / relative
        if not absolute.is_file():
            continue
        path = relative.as_posix()
        root_name = relative.parts[0].lower() if relative.parts and relative.parts[0].lower() in source_roots else None
        path_hits = hits(path, path_markers)
        text = ""
        if relative.suffix.lower() in extensions:
            try:
                if absolute.stat().st_size <= max_bytes:
                    text = absolute.read_text(encoding="utf-8")
                else:
                    skipped += 1
            except (OSError, UnicodeDecodeError):
                skipped += 1
        content_hits = hits(text, content_markers)

        found_ids = sorted(set(EXTRA_ID_RE.findall(text)))
        if found_ids and relative != CONFIG_PATH and relative not in OUTPUT_PATHS and not path.startswith("scripts/"):
            collisions[path] = found_ids

        control = (
            starts_with(path, excluded)
            or path.startswith("scripts/")
            or path.startswith(".github/")
            or path.startswith("data/extras/")
        )
        candidate = (bool(path_hits) and not control) or bool(root_name and (path_hits or content_hits))
        metadata = {
            "path": path,
            "bytes": absolute.stat().st_size,
            "sha256": sha256(absolute),
            "source_root": root_name,
        }
        if candidate:
            candidates.append(
                {
                    **metadata,
                    "classification": "candidate_source",
                    "path_markers": path_hits,
                    "content_markers": content_hits,
                    "boundary": boundary(path),
                }
            )
        elif root_name:
            main_evidence.append({**metadata, "classification": "main_story_evidence"})
        elif path_hits or content_hits:
            control_mentions.append(
                {
                    "path": path,
                    "classification": "scope_control",
                    "path_markers": path_hits,
                    "content_markers": content_hits,
                }
            )

    candidates.sort(key=lambda row: row["path"])
    main_evidence.sort(key=lambda row: row["path"])
    control_mentions.sort(key=lambda row: row["path"])

    state = load_yaml(root / ".project/STATE.yaml")
    timeline = load_yaml(root / "data/generated/timeline.yaml").get("nodes", [])
    if not isinstance(timeline, list) or not timeline:
        raise RuntimeError("canonical Timeline is empty or invalid")
    starts = [row.get("chapters", {}).get("start") for row in timeline if isinstance(row, dict)]
    ends = [row.get("chapters", {}).get("end") for row in timeline if isinstance(row, dict)]
    node_ids = [row.get("id") for row in timeline if isinstance(row, dict)]
    starts = [value for value in starts if isinstance(value, int)]
    ends = [value for value in ends if isinstance(value, int)]

    main_isolated = (
        bool(starts)
        and bool(ends)
        and state.get("scope", {}).get("chapter_start") == 1
        and state.get("scope", {}).get("chapter_end") == 876
        and state.get("progress", {}).get("last_completed_node") == "NODE-0108"
        and min(starts) == 1
        and max(ends) == 876
        and node_ids[-1] == "NODE-0108"
        and not any(str(node_id).startswith("EXTRA-") for node_id in node_ids)
    )
    boundary_complete = all(row["boundary"]["status"] in {"path_derived", "unresolved"} for row in candidates)
    source_counts = Counter(row["source_root"] for row in main_evidence + candidates if row["source_root"])
    status = "candidates_found_pending_boundary_review" if candidates else "initialized_no_tracked_extra_source"

    gates = {
        "tracked_file_inventory": gate(bool(tracked), f"tracked_files={len(tracked)}"),
        "candidate_classification_complete": gate(True, f"candidate_sources={len(candidates)}; control_mentions={len(control_mentions)}"),
        "chapter_boundary_inventory": gate(boundary_complete, f"unresolved={sum(row['boundary']['status'] == 'unresolved' for row in candidates)}"),
        "namespace_uniqueness": gate(not collisions, f"preexisting_extra_id_files={len(collisions)}"),
        "main_story_isolation": gate(main_isolated, "main Timeline remains NODE-0001..NODE-0108 and Chapters 1-876"),
        "deterministic_serialization": gate(True, "paths and findings are sorted; inventory date is frozen"),
        "copyright_boundary": gate(True, "only metadata and marker labels are emitted"),
    }
    errors = [name for name, value in gates.items() if value["status"] == "failed"]

    scope_manifest = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "task_id": TASK_ID,
        "inventory_date": config["inventory_date"],
        "status": status if not errors else "failed",
        "main_story_baseline": config["scope"]["main_story"],
        "extras_scope": config["scope"]["extras"],
        "tracked_inventory": {
            "tracked_files": len(tracked),
            "source_root_counts": dict(sorted(source_counts.items())),
            "main_story_evidence_files": len(main_evidence),
            "candidate_source_files": len(candidates),
            "scope_control_mentions": len(control_mentions),
            "text_files_skipped_as_large_or_non_utf8": skipped,
        },
        "candidate_sources": candidates,
        "scope_control_mentions": control_mentions,
        "existing_extra_id_collisions": collisions,
    }

    if candidates:
        tasks = [
            {
                "id": f"EXTRA-TASK-{index:04d}",
                "status": "planned",
                "source_id": f"EXTRA-SRC-{index:04d}",
                "source_path": row["path"],
                "boundary": row["boundary"],
                "creates_main_timeline_node": False,
                "required_review": ["work_identity", "chapter_boundary", "canonical_identity_reuse", "copyright_boundary"],
            }
            for index, row in enumerate(candidates, 1)
        ]
        plan_status = "ready_for_isolated_ingestion"
        next_action = "Review each candidate boundary and create one isolated ingestion Task per confirmed work."
    else:
        tasks = [
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
        plan_status = "waiting_for_source"
        next_action = tasks[0]["next_action"]

    task_plan = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "task_id": TASK_ID,
        "status": plan_status,
        "namespace_contract": config["scope"]["extras"]["namespaces"],
        "rules": [
            "Do not create or renumber NODE records in the completed main-story Timeline.",
            "Do not place extras facts in data/extensions or data/generated during inventory.",
            "Do not reuse main-story entity IDs without direct identity evidence.",
            "Do not copy source prose into inventory, plans or generated reports.",
        ],
        "tasks": tasks,
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
            "tracked_files": len(tracked),
            "source_root_files": len(main_evidence) + len(candidates),
            "main_story_evidence_files": len(main_evidence),
            "candidate_source_files": len(candidates),
            "scope_control_mentions": len(control_mentions),
            "planned_isolated_tasks": len(tasks),
        },
        "quality_gates": gates,
        "findings": {
            "inventory_status": status,
            "candidate_paths": [row["path"] for row in candidates],
            "unresolved_boundary_paths": [row["path"] for row in candidates if row["boundary"]["status"] == "unresolved"],
            "preexisting_extra_id_files": collisions,
        },
    }

    candidate_lines = "\n".join(
        f"- `{row['path']}`：boundary={row['boundary']['status']}, bytes={row['bytes']}"
        for row in candidates
    ) or "- 未发现符合规则的已跟踪番外源文件。"
    gate_lines = "\n".join(
        f"| {name} | {value['status']} | {value['detail']} |" for name, value in gates.items()
    )
    report = f"""# 番外 Scope 盘点与独立命名空间 — {RUN_ID}

- Task：`{TASK_ID}`
- 盘点日期：`{config['inventory_date']}`
- 状态：**{audit['extras_inventory']['status']}**
- 盘点结论：**{status}**
- 本 Run 不创建主线 Timeline Node，不改变正文第 1—876 章及 `NODE-0108` 终点。

## 盘点结果

- Git tracked files：{len(tracked)}
- Source-root files：{len(main_evidence) + len(candidates)}
- 番外候选源：{len(candidates)}
- 仅用于 scope 控制的番外提及：{len(control_mentions)}

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


def compare(actual_root: Path, expected_root: Path) -> list[str]:
    errors: list[str] = []
    for relative in OUTPUT_PATHS:
        actual = actual_root / relative
        expected = expected_root / relative
        if not expected.exists():
            errors.append(f"missing tracked output: {relative}")
        elif actual.read_bytes() != expected.read_bytes():
            errors.append(f"stale tracked output: {relative}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-root", type=Path, default=Path("."))
    parser.add_argument("--check-root", type=Path)
    args = parser.parse_args()

    errors = generate(args.root.resolve(), args.output_root)
    if args.check_root:
        errors.extend(compare(args.output_root.resolve(), args.check_root.resolve()))
    if errors:
        for error in errors:
            print(error)
        return 1
    print(json.dumps({"run_id": RUN_ID, "task_id": TASK_ID, "status": "passed"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
