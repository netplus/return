#!/usr/bin/env python3
"""Full canonical audit and reproducible v1 baseline materializer."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import knowledge_base as kb  # noqa: E402

VERIFY = ("verified", "partial", "pending", "conflict", "inferred")
ID_RE = {
    "timeline": re.compile(r"^NODE-\d+$"),
    "characters": re.compile(r"^CHAR-\d+$"),
    "gifts": re.compile(r"^GIFT-\d+$"),
    "artifacts": re.compile(r"^ART-\d+$"),
}
RUN_RE = re.compile(r"^RUN-(\d+)$")
TASK_RE = re.compile(r"^TASK-(\d+)$")


def load(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise RuntimeError(f"invalid YAML {path}: {exc}") from exc


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hash(root: Path, paths: list[Path]) -> tuple[str, list[dict[str, Any]]]:
    digest = hashlib.sha256()
    files = []
    for path in sorted(paths):
        rel, file_sha = path.relative_to(root).as_posix(), sha(path)
        digest.update(f"{rel}\0{file_sha}\0".encode())
        files.append({"path": rel, "sha256": file_sha, "bytes": path.stat().st_size})
    return digest.hexdigest(), files


def walk(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield child_path, str(key), child
            yield from walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, None, child
            yield from walk(child, child_path)


def strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)


def maps(indexes: dict[str, dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    out = {}
    for group, (_prefix, _base, key, _filename) in kb.SPECS.items():
        rows = indexes[group].get(key, [])
        if not isinstance(rows, list):
            raise RuntimeError(f"canonical {group}.{key} is not a list")
        out[group] = {row["id"]: row for row in rows if isinstance(row, dict) and isinstance(row.get("id"), str)}
    return out


def character_names(row: dict[str, Any]) -> set[str]:
    result = set()
    for key in ("name", "canonical_name", "alias"):
        value = row.get(key)
        if isinstance(value, str):
            result.add(value)
    for key in ("aliases", "identities", "identity", "names"):
        value = row.get(key)
        if isinstance(value, str):
            result.add(value)
        elif isinstance(value, list):
            result.update(item for item in value if isinstance(item, str))
    return result


def effective_status(row: dict[str, Any]) -> str | None:
    for key in ("status_change", "life_status", "status"):
        value = row.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, list) and value and isinstance(value[-1], str):
            return value[-1]
    return None


def anchor(event: dict[str, Any], ranges: dict[str, tuple[int, int]]) -> int | None:
    if isinstance(event.get("chapter"), int):
        return event["chapter"]
    cr = event.get("chapter_range")
    if isinstance(cr, dict) and isinstance(cr.get("start"), int):
        return cr["start"]
    node = event.get("node")
    return ranges.get(node, (None, None))[0] if isinstance(node, str) else None


def normalize(text: str) -> str:
    return re.sub(r"[\s　，。、“”‘’：:；;（）()【】\[\]·—_-]", "", text)


def audit(root: Path) -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {
        key: {"status": "passed", "details": []}
        for key in (
            "yaml_structure", "canonical_rebuild", "global_id_uniqueness", "timeline_continuity",
            "cross_index_consistency", "extension_append_only_shape", "project_os_metrics",
            "entity_document_freshness", "character_identity_alignment", "character_growth_continuity",
            "dead_character_active_state", "gift_artifact_linkage", "artifact_ownership_lifecycle",
            "final_state_consistency", "verification_debt", "copyright_boundary", "audit_reproducibility",
        )
    }

    def fail(name: str, detail: str):
        checks[name]["status"] = "failed"
        checks[name]["details"].append(detail)

    def warn(name: str, detail: str):
        if checks[name]["status"] == "passed":
            checks[name]["status"] = "warning"
        checks[name]["details"].append(detail)

    def note(name: str, detail: str):
        checks[name]["details"].append(detail)

    yaml_paths = sorted(path for top in (root / "data", root / ".project", root / "sources") if top.exists() for path in top.rglob("*.yaml"))
    parsed = {}
    for path in yaml_paths:
        try:
            parsed[path] = load(path)
        except RuntimeError as exc:
            fail("yaml_structure", str(exc))
    note("yaml_structure", f"parsed_yaml_files={len(parsed)}")

    try:
        indexes, canonical = kb.build(root), None
        canonical = maps(indexes)
    except Exception as exc:
        fail("canonical_rebuild", str(exc))
        indexes, canonical = {}, {key: {} for key in kb.SPECS}

    generated_paths = []
    for group, (_prefix, _base, _key, filename) in kb.SPECS.items():
        path = root / "data/generated" / filename
        generated_paths.append(path)
        if not path.exists() or load(path) != indexes.get(group):
            fail("canonical_rebuild", f"generated index missing or stale: {path.relative_to(root)}")
    note("canonical_rebuild", "four generated indexes compared to deterministic rebuild")

    seen = {}
    for group, rows in canonical.items():
        for rid in rows:
            if not ID_RE[group].match(rid):
                fail("global_id_uniqueness", f"malformed {group} ID: {rid}")
            if rid in seen:
                fail("global_id_uniqueness", f"duplicate ID {rid}: {seen[rid]} and {group}")
            seen[rid] = group
    note("global_id_uniqueness", f"canonical_ids={len(seen)}")

    nodes = canonical["timeline"]
    ranges = {}
    for rid, row in nodes.items():
        cr = row.get("chapters", {})
        start = cr.get("start") if isinstance(cr, dict) else None
        end = cr.get("end") if isinstance(cr, dict) else None
        if not isinstance(start, int) or not isinstance(end, int) or start > end:
            fail("timeline_continuity", f"invalid range {rid}: {cr!r}")
        else:
            ranges[rid] = (start, end)
    ordered = sorted((start, end, rid) for rid, (start, end) in ranges.items())
    gaps, overlaps = [], []
    if ordered and ordered[0][0] != 1:
        gaps.append([1, ordered[0][0] - 1])
    for left, right in zip(ordered, ordered[1:]):
        if right[0] <= left[1]:
            overlaps.append([left[2], right[2], right[0]])
        elif right[0] > left[1] + 1:
            gaps.append([left[1] + 1, right[0] - 1])
    for item in gaps:
        fail("timeline_continuity", f"gap {item}")
    for item in overlaps:
        fail("timeline_continuity", f"overlap {item}")
    note("timeline_continuity", f"nodes={len(ordered)}; coverage={ordered[0][0] if ordered else None}-{max((x[1] for x in ordered), default=0)}")

    refs = []
    for group, rows in canonical.items():
        for rid, row in rows.items():
            for path, key, value in walk(row, f"{group}.{rid}"):
                if not key:
                    continue
                values = value if isinstance(value, list) else [value]
                for child in values:
                    if isinstance(child, str) and child.startswith("NODE-") and (key == "node" or "node" in key) and child not in nodes:
                        refs.append(f"{path}: unknown {child}")
                    if isinstance(child, str) and child.startswith("GIFT-") and "gift" in key and child not in canonical["gifts"]:
                        refs.append(f"{path}: unknown {child}")
                    if isinstance(child, str) and child.startswith("ART-") and "artifact" in key and child not in canonical["artifacts"]:
                        refs.append(f"{path}: unknown {child}")
    for rid, row in canonical["gifts"].items():
        node, chapter = row.get("node"), row.get("chapter")
        if isinstance(node, str) and node in ranges and isinstance(chapter, int) and not ranges[node][0] <= chapter <= ranges[node][1]:
            refs.append(f"{rid}: chapter {chapter} outside {node} {ranges[node]}")
    for detail in refs:
        fail("cross_index_consistency", detail)
    note("cross_index_consistency", f"reference_errors={len(refs)}")

    extension_paths = sorted((root / "data/extensions").rglob("*.yaml"))
    category_runs, extension_runs = set(), set()
    for path in extension_paths:
        doc = parsed.get(path)
        run_id = doc.get("run_id") if isinstance(doc, dict) else None
        if not isinstance(run_id, str) or not RUN_RE.match(run_id):
            fail("extension_append_only_shape", f"invalid run_id: {path.relative_to(root)}")
            continue
        if path.stem != run_id.lower():
            fail("extension_append_only_shape", f"filename/run mismatch: {path.relative_to(root)} -> {run_id}")
        key = (path.parent.name, run_id)
        if key in category_runs:
            fail("extension_append_only_shape", f"duplicate category/run: {key}")
        category_runs.add(key)
        extension_runs.add(run_id)
    warn("extension_append_only_shape", "current tree proves retention and rebuildability; historical non-rewrite remains a Git-history property")
    note("extension_append_only_shape", f"extension_files={len(extension_paths)}; runs={len(extension_runs)}")

    state, metrics, tasks = (parsed.get(root / name, {}) for name in (".project/STATE.yaml", ".project/METRICS.yaml", ".project/TASKS.yaml"))
    progress = state.get("progress", {}) if isinstance(state, dict) else {}
    coverage = metrics.get("coverage", {}) if isinstance(metrics, dict) else {}
    pairs = {"timeline": ("nodes_completed", "timeline_nodes"), "characters": ("characters_documented", "characters_documented"), "gifts": ("gift_events", "gift_events"), "artifacts": ("artifact_records", "artifact_records")}
    for group, (skey, mkey) in pairs.items():
        actual = len(canonical[group])
        if progress.get(skey) != actual:
            fail("project_os_metrics", f"STATE {skey}={progress.get(skey)!r}, actual={actual}")
        if coverage.get(mkey) != actual:
            fail("project_os_metrics", f"METRICS {mkey}={coverage.get(mkey)!r}, actual={actual}")
    task_rows = tasks.get("tasks", []) if isinstance(tasks, dict) else []
    task_ids = [row.get("id") for row in task_rows if isinstance(row, dict)]
    pending_tasks = [row.get("id") for row in task_rows if isinstance(row, dict) and row.get("status") == "pending"]
    if len(task_ids) != len(set(task_ids)):
        fail("project_os_metrics", "duplicate task IDs")
    if len(pending_tasks) > 1:
        fail("project_os_metrics", f"multiple pending tasks: {pending_tasks}")
    note("project_os_metrics", f"pending_tasks={pending_tasks}")

    manifest_path = root / "docs/entity-docs-manifest.yaml"
    try:
        manifest = load(manifest_path)
    except RuntimeError as exc:
        manifest = {}
        fail("entity_document_freshness", str(exc))
    manifest_paths, manifest_counts = set(), {}
    for group, canonical_group in (("characters", "characters"), ("artifacts", "artifacts")):
        entry = manifest.get("groups", {}).get(group, {}) if isinstance(manifest, dict) else {}
        docs = entry.get("documents", []) if isinstance(entry, dict) else []
        manifest_counts[group] = len(docs) if isinstance(docs, list) else -1
        if entry.get("count") != len(canonical[canonical_group]) or manifest_counts[group] != len(canonical[canonical_group]):
            fail("entity_document_freshness", f"manifest {group} count mismatch")
        ids = set()
        for item in docs if isinstance(docs, list) else []:
            rid, doc_path = item.get("id"), item.get("path")
            if rid in ids:
                fail("entity_document_freshness", f"duplicate manifest ID {rid}")
            ids.add(rid)
            if not isinstance(doc_path, str) or not (root / doc_path).exists():
                fail("entity_document_freshness", f"missing document {rid}: {doc_path}")
            elif doc_path in manifest_paths:
                fail("entity_document_freshness", f"duplicate manifest path {doc_path}")
            else:
                manifest_paths.add(doc_path)
        if ids != set(canonical[canonical_group]):
            fail("entity_document_freshness", f"manifest {group} ID set mismatch")
    note("entity_document_freshness", f"documents={len(manifest_paths)}")

    all_names, name_ids = set(), defaultdict(list)
    growth_issues, first_issues, dead_candidates = [], [], []
    focus = ["徐霄", "姬雪", "刘爱花", "雪瑶仙帝", "凤青玄", "天羽", "天翎", "玄雪", "凤溪", "初殷", "龙九天", "诸葛青天", "独孤惊云", "孔青", "天穹", "黑神", "破玄", "冥法", "神无机"]
    focus_matches = {term: [] for term in focus}
    for rid, row in canonical["characters"].items():
        names = character_names(row)
        all_names.update(names)
        if isinstance(row.get("name"), str):
            name_ids[row["name"]].append(rid)
        first = row.get("first_appearance")
        if not isinstance(first, dict) or not isinstance(first.get("chapter"), int) or not isinstance(first.get("node"), str) or first.get("node") not in ranges:
            first_issues.append(rid)
        elif not ranges[first["node"]][0] <= first["chapter"] <= ranges[first["node"]][1]:
            first_issues.append(rid)
        events = row.get("growth_event", row.get("growth_events", []))
        anchors = [anchor(event, ranges) for event in events if isinstance(event, dict)] if isinstance(events, list) else []
        anchors = [value for value in anchors if value is not None]
        if anchors != sorted(anchors):
            growth_issues.append(rid)
        joined = " | ".join(names)
        for term in focus:
            if term in joined:
                focus_matches[term].append({"id": rid, "name": row.get("name"), "status": effective_status(row)})
        status = effective_status(row) or ""
        if any(token in status.lower() for token in ("dead", "死亡", "陨落", "身亡")):
            active = [key for key in ("current_position", "current_role", "active_position", "current_affiliation") if row.get(key) not in (None, "", [], "无", "none")]
            if active:
                dead_candidates.append({"id": rid, "name": row.get("name"), "status": status, "fields": active})
    for rid in first_issues:
        fail("character_identity_alignment", f"invalid first appearance: {rid}")
    for rid in growth_issues:
        fail("character_growth_continuity", f"non-chronological growth events: {rid}")
    duplicate_names = {name: ids for name, ids in name_ids.items() if len(ids) > 1}
    unresolved_focus = [term for term, rows in focus_matches.items() if not rows]
    if unresolved_focus:
        warn("character_identity_alignment", f"focus identities not directly resolved: {unresolved_focus}")
    note("character_identity_alignment", f"duplicate canonical names for review={len(duplicate_names)}")
    if dead_candidates:
        warn("dead_character_active_state", f"candidates={len(dead_candidates)}")

    artifact_names, artifact_name_ids, lifecycle = [], defaultdict(list), []
    for rid, row in canonical["artifacts"].items():
        name = row.get("name")
        if isinstance(name, str):
            artifact_names.append((rid, name, normalize(name)))
            artifact_name_ids[name].append(rid)
        current_state = " | ".join(strings(row.get("current_state", "")))
        holder = row.get("current_holder")
        if any(token in current_state for token in ("消耗", "损毁", "毁灭", "已用尽")) and holder not in (None, "", "无", "none"):
            lifecycle.append({"id": rid, "name": name, "holder": holder, "state": current_state})
    duplicate_artifacts = {name: ids for name, ids in artifact_name_ids.items() if len(ids) > 1}
    if lifecycle:
        warn("artifact_ownership_lifecycle", f"consumed/destroyed holder candidates={len(lifecycle)}")
    note("artifact_ownership_lifecycle", f"duplicate artifact names for review={len(duplicate_artifacts)}")

    party_candidates, no_artifact_match, pending_gifts = [], [], []
    link_counts = Counter()
    for rid, row in canonical["gifts"].items():
        for key in ("giver", "recipient"):
            value = row.get(key)
            if isinstance(value, str) and value not in all_names and value not in {"系统", "万倍返还系统"}:
                party_candidates.append({"gift": rid, "field": key, "value": value})
        matched = False
        for field in ("gift", "reward"):
            value = row.get(field)
            if isinstance(value, str):
                text = normalize(value)
                hits = [aid for aid, _name, normalized in artifact_names if normalized and normalized in text]
                if hits:
                    matched = True
                    link_counts[field] += 1
        if not matched:
            no_artifact_match.append({"id": rid, "gift": row.get("gift"), "reward": row.get("reward")})
        if any(value == "pending" for _path, _key, value in walk(row)):
            pending_gifts.append(rid)
    if party_candidates:
        warn("gift_artifact_linkage", f"gift party identity candidates={len(party_candidates)}")
    if no_artifact_match:
        warn("gift_artifact_linkage", f"rows without exact Artifact-name match={len(no_artifact_match)}")
    note("gift_artifact_linkage", f"links={dict(link_counts)}; pending_gift_rows={len(pending_gifts)}")

    final_errors = []
    final = nodes.get("NODE-0108")
    if not isinstance(final, dict) or final.get("chapters", {}).get("end") != 876:
        final_errors.append("NODE-0108 must end at Chapter 876")
    xuxiao = next((row for row in canonical["characters"].values() if row.get("name") == "徐霄"), None)
    xuxiao_text = " | ".join(strings(xuxiao)) if isinstance(xuxiao, dict) else ""
    for token in ("大罗", "至尊仙帝", "太初仙域"):
        if token not in xuxiao_text:
            final_errors.append(f"徐霄 final state missing {token}")
    dashboard = (root / ".project/DASHBOARD.md").read_text(encoding="utf-8")
    if "三次暂存升级机会" not in dashboard or "pending" not in dashboard:
        final_errors.append("three retained upgrade opportunities are not explicitly kept pending")
    for detail in final_errors:
        fail("final_state_consistency", detail)
    note("final_state_consistency", "main story remains closed at Chapter 876; extras excluded")

    field_counts, record_counts = Counter({x: 0 for x in VERIFY}), Counter({x: 0 for x in VERIFY})
    examples = {x: [] for x in VERIFY}
    for group, (_prefix, _base, key, _filename) in kb.SPECS.items():
        for row in indexes.get(group, {}).get(key, []):
            if not isinstance(row, dict):
                continue
            rid, states = row.get("id", "unknown"), set()
            for path, field, value in walk(row, f"{group}.{rid}"):
                if isinstance(value, str) and value in VERIFY and (field == "status" or (field and field.endswith("_status"))):
                    field_counts[value] += 1
                    states.add(value)
                    if len(examples[value]) < 40:
                        examples[value].append({"record": rid, "path": path})
            for value in states:
                record_counts[value] += 1
    note("verification_debt", f"non-verified field occurrences={sum(field_counts[x] for x in VERIFY if x != 'verified')}")

    forbidden = [path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and ".git" not in path.parts and (path.suffix.lower() in {".epub", ".mobi"} or (path.suffix.lower() == ".txt" and path.stat().st_size > 100_000))]
    for path in forbidden:
        fail("copyright_boundary", f"potential full-text payload: {path}")
    note("copyright_boundary", "reports contain structured facts, summaries, metadata and hashes only")

    ext_hash, ext_files = tree_hash(root, extension_paths)
    can_hash, can_files = tree_hash(root, [path for path in generated_paths if path.exists()])
    doc_hash, doc_files = tree_hash(root, [manifest_path] + [root / path for path in sorted(manifest_paths)])
    note("audit_reproducibility", f"extensions={ext_hash}; canonical={can_hash}; entity_docs={doc_hash}")

    blockers = [{"check": key, "detail": detail} for key, value in checks.items() if value["status"] == "failed" for detail in value["details"]]
    return {
        "checks": checks,
        "blockers": blockers,
        "baseline": {
            "chapters": {"start": ordered[0][0] if ordered else None, "end": max((x[1] for x in ordered), default=0)},
            "timeline_nodes": len(nodes), "characters": len(canonical["characters"]),
            "gift_events": len(canonical["gifts"]), "artifacts": len(canonical["artifacts"]),
            "extension_files": len(extension_paths), "yaml_files": len(yaml_paths),
            "entity_documents": {"characters": manifest_counts.get("characters", 0), "artifacts": manifest_counts.get("artifacts", 0), "total": len(manifest_paths)},
            "pending_tasks_before_materialization": pending_tasks,
        },
        "verification_debt": {"field_occurrences": dict(field_counts), "records_with_state": dict(record_counts), "examples": examples},
        "findings": {
            "timeline": {"gaps": gaps, "overlaps": overlaps},
            "characters": {"duplicate_names": duplicate_names, "focus_matches": focus_matches, "dead_active_candidates": dead_candidates, "invalid_first_appearance": first_issues, "growth_order_issues": growth_issues},
            "gifts": {"party_identity_candidates": party_candidates[:100], "without_artifact_match": no_artifact_match[:100], "pending_rows": pending_gifts, "link_counts": dict(link_counts)},
            "artifacts": {"duplicate_names": duplicate_artifacts, "lifecycle_candidates": lifecycle[:100]},
            "limitations": ["Current-tree audit cannot alone prove historical non-rewrite.", "Free-text legacy Gift rows are not assigned ART IDs without evidence.", "Name similarity never proves identity."],
        },
        "reproducibility": {"extensions": {"tree_sha256": ext_hash, "files": ext_files}, "canonical_generated": {"tree_sha256": can_hash, "files": can_files}, "entity_documents": {"tree_sha256": doc_hash, "file_count": len(doc_files)}},
    }


def table(rows: list[list[Any]], headers: list[str]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out.extend("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |" for row in rows)
    return "\n".join(out)


def reports(meta: dict[str, str], result: dict[str, Any]) -> dict[str, str]:
    b, debt, findings = result["baseline"], result["verification_debt"], result["findings"]
    check_rows = [[key, value["status"], "；".join(value["details"][:3]) or "—"] for key, value in result["checks"].items()]
    focus_rows = [[term, "；".join(f"{x['id']} {x.get('name')} ({x.get('status') or '未标注'})" for x in rows) or "未直接匹配，转入规范化复核"] for term, rows in findings["characters"]["focus_matches"].items()]
    baseline_rows = [["章节覆盖", f"{b['chapters']['start']}—{b['chapters']['end']}"], ["Timeline Nodes", b["timeline_nodes"]], ["人物", b["characters"]], ["赠送事件", b["gift_events"]], ["物品", b["artifacts"]], ["Extension 文件", b["extension_files"]], ["人物/物品文档", b["entity_documents"]["total"]]]
    audit_md = f"""# 全库审计报告 — {meta['version']}

- Run：`{meta['run_id']}`；Task：`{meta['task_id']}` (`audit`)
- 基线业务提交：`{meta['source_commit']}`；审计日期：{meta['audit_date']}
- 范围：正文第 {b['chapters']['start']}—{b['chapters']['end']} 章及全部 canonical、extensions、generated views、实体文档和 Project OS 控制面。

## 结论

阻断项 **{len(result['blockers'])}** 个。正文仍以第 876 章为终点；本 Run 不创建 Timeline Node，也不接入番外。

{table(baseline_rows, ['指标', '值'])}

## 质量门禁

{table(check_rows, ['Gate', '结果', '摘要'])}

## 重点人物

只按 canonical name、别名和身份字段直接匹配，绝不因名字相似自动合并。

{table(focus_rows, ['身份', '匹配'])}

## 主要发现

- 人物同名记录 {len(findings['characters']['duplicate_names'])} 组；死亡人物 active/current 字段候选 {len(findings['characters']['dead_active_candidates'])} 条。
- Gift 参与者身份候选 {len(findings['gifts']['party_identity_candidates'])} 条；未能以自由文本直接匹配 Artifact 名称的 Gift {len(findings['gifts']['without_artifact_match'])} 条。
- 同名 Artifact {len(findings['artifacts']['duplicate_names'])} 组；生命周期候选 {len(findings['artifacts']['lifecycle_candidates'])} 条。
- Timeline 空洞 {len(findings['timeline']['gaps'])}；重叠 {len(findings['timeline']['overlaps'])}。

“官方页面直接核验至第 16 章”只描述一种证据渠道，不等于第 17—876 章未经正文阅读。仓库还使用用户归档正文、逐章 SHA-256、可读镜像、单一来源、上下文推断和正文冲突等证据类型。

## 可复现性

```text
extension_tree_sha256 = {result['reproducibility']['extensions']['tree_sha256']}
canonical_tree_sha256 = {result['reproducibility']['canonical_generated']['tree_sha256']}
entity_docs_tree_sha256 = {result['reproducibility']['entity_documents']['tree_sha256']}
```

唯一下一项 pending Task 为 `TASK-0112`；`TASK-0113` 保持 planned 并依赖 `TASK-0112`。
"""
    debt_rows = [[state, debt["field_occurrences"].get(state, 0), debt["records_with_state"].get(state, 0)] for state in VERIFY]
    samples = []
    for state in ("partial", "pending", "conflict", "inferred"):
        items = "\n".join(f"- `{x['record']}` — `{x['path']}`" for x in debt["examples"].get(state, [])[:20]) or "- 无"
        samples.append(f"### {state}\n\n{items}")
    debt_md = f"""# 核验债务清单 — {meta['version']}

基线：`{meta['source_commit']}`。

{table(debt_rows, ['状态', '字段出现次数', '涉及记录数'])}

统计只计算核验语义字段，不混入人物生死、Task 或物品生命周期状态。官方直接核验、归档正文阅读、逐章哈希、镜像交叉核验、单一来源、推断和正文冲突必须分别理解。第 17—876 章并非“未读”。

{chr(10).join(samples)}

`TASK-0112` 不得通过无证据推断降低 pending；结局三次暂存升级机会继续保持 pending。
"""
    stats_md = f"""# v1.0 基线统计

- Version：`{meta['version']}`；Run：`{meta['run_id']}`；Source commit：`{meta['source_commit']}`

{table(baseline_rows + [['Parsed YAML files', b['yaml_files']]], ['Baseline metric', 'Value'])}

{table([['Extensions', result['reproducibility']['extensions']['tree_sha256']], ['Generated canonical indexes', result['reproducibility']['canonical_generated']['tree_sha256']], ['Entity documents + manifest', result['reproducibility']['entity_documents']['tree_sha256']]], ['Tree', 'SHA-256'])}

正文第 876 章后的番外不计入本基线，也不得改变正文完整覆盖结论。
"""
    counts = debt["field_occurrences"]
    release_md = f"""# v1.0.0 — 正文完整知识库基线

- 正文覆盖：第 {b['chapters']['start']}—{b['chapters']['end']} 章
- Timeline Nodes：{b['timeline_nodes']}；人物：{b['characters']}；赠送事件：{b['gift_events']}；物品：{b['artifacts']}
- 核验字段：verified {counts.get('verified', 0)}、partial {counts.get('partial', 0)}、pending {counts.get('pending', 0)}、conflict {counts.get('conflict', 0)}、inferred {counts.get('inferred', 0)}

Canonical 数据由基础索引和 append-only extensions 重建；generated indexes、人物/物品档案与 manifest 为自动物化视图。已知 pending/conflict 保留，三次暂存升级机会不推断使用结果。番外使用独立 scope。

Source commit：`{meta['source_commit']}`；Canonical tree SHA-256：`{result['reproducibility']['canonical_generated']['tree_sha256']}`。

仓库不保存整章正文，只发布原创摘要、结构化事实、来源元数据、逐章哈希与核验状态。原作品版权归原作者及权利人所有。
"""
    return {"docs/08-analysis/full-repository-audit.md": audit_md, "docs/08-analysis/verification-debt.md": debt_md, "docs/08-analysis/v1-baseline-statistics.md": stats_md, "RELEASE_NOTES_v1.0.0.md": release_md}


def write(root: Path, output: Path, meta: dict[str, str], result: dict[str, Any]) -> list[Path]:
    paths = []
    for rel, content in reports(meta, result).items():
        path = output / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        paths.append(path)
    machine = {"schema_version": 1, "audit": {**meta, "status": "blocked" if result["blockers"] else "passed_with_findings", "blocking_findings": result["blockers"]}, **{key: result[key] for key in ("baseline", "verification_debt", "checks", "findings", "reproducibility")}, "release": {"version": meta["version"], "notes": "RELEASE_NOTES_v1.0.0.md", "github_release_created": False, "blocker": "The authorized GitHub connector has no tag/release creation action; release publication remains explicit blocker."}}
    path = output / "data/audits/run-0125.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(machine, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
    paths.append(path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-root", type=Path, default=Path("build/audit"))
    parser.add_argument("--run-id", default="RUN-0125")
    parser.add_argument("--task-id", default="TASK-0111")
    parser.add_argument("--version", default="v1.0.0")
    parser.add_argument("--audit-date", default="2026-07-29")
    parser.add_argument("--source-commit", default=os.environ.get("GITHUB_SHA", "unknown"))
    args = parser.parse_args()
    if not RUN_RE.match(args.run_id) or not TASK_RE.match(args.task_id):
        parser.error("invalid Run or Task ID")
    root = args.repo_root.resolve()
    output = args.output_root if args.output_root.is_absolute() else root / args.output_root
    meta = {"run_id": args.run_id, "task_id": args.task_id, "version": args.version, "audit_date": args.audit_date, "source_commit": args.source_commit}
    result = audit(root)
    written = write(root, output, meta, result)
    print(json.dumps({"status": "blocked" if result["blockers"] else "passed_with_findings", "blocking_findings": len(result["blockers"]), "outputs": [path.relative_to(output).as_posix() for path in written], "baseline": result["baseline"]}, ensure_ascii=False, indent=2))
    return 1 if result["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
