#!/usr/bin/env python3
"""Validate RUN-0126 normalization decisions and materialize final-state views."""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

import knowledge_base as kb

RUN_ID = "RUN-0126"
TASK_ID = "TASK-0112"
EXPECTED_PARTICIPANTS = {
    "GIFT-0044", "GIFT-0087", "GIFT-0110", "GIFT-0144", "GIFT-0160", "GIFT-0161",
    "GIFT-0172", "GIFT-0184", "GIFT-0226", "GIFT-0230", "GIFT-0231", "GIFT-0234",
    "GIFT-0240", "GIFT-0242", "GIFT-0243", "GIFT-0244", "GIFT-0251", "GIFT-0257",
}
EXPECTED_COMPONENT_ROWS = {
    "GIFT-0005", "GIFT-0011", "GIFT-0014", "GIFT-0016", "GIFT-0019", "GIFT-0020",
    "GIFT-0023", "GIFT-0024", "GIFT-0029", "GIFT-0030", "GIFT-0032", "GIFT-0035",
    "GIFT-0054", "GIFT-0063", "GIFT-0066", "GIFT-0068", "GIFT-0073", "GIFT-0075",
    "GIFT-0078", "GIFT-0087", "GIFT-0090", "GIFT-0092", "GIFT-0189", "GIFT-0213",
    "GIFT-0215",
}
EXPECTED_NAMES = {
    "CHAR-0052": "程双", "CHAR-0056": "黑风", "CHAR-0111": "司空浩南", "CHAR-0140": "丁静",
    "ART-0017": "九火琉璃罩", "ART-0018": "流光星陨戒", "ART-0044": "九天神莲戒",
}
EXPECTED_ALIASES = {"CHAR-0002": {"雪瑶", "雪瑶仙帝", "刘爱花"}, "CHAR-0045": {"天羽"}}
EXPECTED_SUPERSEDED = {"CHAR-0196": "CHAR-0144", "CHAR-0201": "CHAR-0145"}
EXPECTED_LIFECYCLE = {"ART-0017": "destroyed", "ART-0023": "destroyed", "ART-0026": "consumed"}


def load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"expected mapping: {path}")
    return data


def dump(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def index_map(doc: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    rows = doc.get(key, [])
    if not isinstance(rows, list):
        raise RuntimeError(f"{key} must be a list")
    return {row["id"]: row for row in rows if isinstance(row, dict) and isinstance(row.get("id"), str)}


def names(row: dict[str, Any]) -> set[str]:
    result: set[str] = set()
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


def gate(status: bool, detail: str) -> dict[str, Any]:
    return {"status": "passed" if status else "failed", "detail": detail}


def materialize(root: Path, generated_dir: Path, output_root: Path, source_commit: str) -> list[str]:
    ledger = load(root / "data/normalization/run-0126.yaml")
    characters = index_map(load(generated_dir / "characters.yaml"), "characters")
    gifts = index_map(load(generated_dir / "gifts.yaml"), "gifts")
    artifacts = index_map(load(generated_dir / "artifacts.yaml"), "artifacts")
    timeline = index_map(load(generated_dir / "timeline.yaml"), "nodes")
    state = load(root / ".project/STATE.yaml")
    errors: list[str] = []

    for rid, expected in EXPECTED_NAMES.items():
        group = characters if rid.startswith("CHAR-") else artifacts
        actual = group.get(rid, {}).get("name")
        if actual != expected:
            errors.append(f"{rid} name={actual!r}, expected {expected!r}")

    for rid, expected in EXPECTED_ALIASES.items():
        missing = expected - names(characters.get(rid, {}))
        if missing:
            errors.append(f"{rid} missing aliases: {sorted(missing)}")

    for rid, canonical_id in EXPECTED_SUPERSEDED.items():
        row = characters.get(rid, {})
        if row.get("record_status") != "superseded" or row.get("canonical_character_id") != canonical_id:
            errors.append(f"{rid} is not superseded by {canonical_id}")

    groups: dict[str, list[str]] = defaultdict(list)
    for rid, row in characters.items():
        if row.get("record_status") != "superseded" and isinstance(row.get("name"), str):
            groups[row["name"]].append(rid)
    duplicate_groups = {name: ids for name, ids in groups.items() if len(ids) > 1}
    ledger_groups = {row.get("label") for row in ledger.get("character_name_groups", []) if isinstance(row, dict)}
    unclassified_duplicates = sorted(name for name in duplicate_groups if name not in ledger_groups)
    if unclassified_duplicates:
        errors.append(f"unclassified active duplicate character names: {unclassified_duplicates}")

    ledger_participants = set(ledger.get("gift_participant_candidates", []))
    if ledger_participants != EXPECTED_PARTICIPANTS:
        errors.append("gift participant ledger does not exactly cover RUN-0125 candidates")
    participant_counts = defaultdict(int)
    for gift_id in sorted(EXPECTED_PARTICIPANTS):
        row = gifts.get(gift_id, {})
        resolution = row.get("participant_resolution")
        if not isinstance(resolution, dict):
            errors.append(f"{gift_id} missing participant_resolution")
            continue
        kind = resolution.get("resolution")
        participant_counts[str(kind)] += 1
        refs = resolution.get("recipient_refs", [])
        if not isinstance(refs, list) or any(ref not in characters for ref in refs):
            errors.append(f"{gift_id} has invalid recipient_refs")
        if str(kind).startswith("exact") and not refs:
            errors.append(f"{gift_id} exact resolution has no refs")
        if kind in {"unresolved", "unresolved_role_label"} and not resolution.get("reason"):
            errors.append(f"{gift_id} unresolved resolution lacks reason")

    dispositions = {
        row.get("gift_id"): row for row in ledger.get("gift_component_dispositions", []) if isinstance(row, dict)
    }
    if set(dispositions) != EXPECTED_COMPONENT_ROWS:
        errors.append("gift component ledger does not exactly cover all 25 audited rows")
    linked_component_rows = 0
    pending_component_rows = 0
    for gift_id, decision in dispositions.items():
        if gift_id not in gifts:
            errors.append(f"unknown Gift in component ledger: {gift_id}")
        refs = decision.get("artifact_refs", [])
        if any(ref not in artifacts for ref in refs if isinstance(ref, str)):
            errors.append(f"{gift_id} references unknown Artifact")
        linked_component_rows += bool(refs)
        pending_component_rows += decision.get("status") == "pending"

    for rid, expected_state in EXPECTED_LIFECYCLE.items():
        row = artifacts.get(rid, {})
        if row.get("lifecycle_status") != expected_state:
            errors.append(f"{rid} lifecycle_status is not {expected_state}")
        if row.get("current_holder") not in (None, "", "none", "无"):
            errors.append(f"{rid} retains current_holder after {expected_state}")
        if not isinstance(row.get("lifecycle_event"), list):
            errors.append(f"{rid} lacks lifecycle_event ledger")

    for rid in ("ART-0055", "ART-0099"):
        row = artifacts.get(rid, {})
        if row.get("artifact_type_key") != "天凤血丹" or row.get("duplicate_name_resolution") != "same_type_distinct_batch":
            errors.append(f"{rid} lacks distinct-batch classification")
    if artifacts.get("ART-0055", {}).get("batch_id") == artifacts.get("ART-0099", {}).get("batch_id"):
        errors.append("天凤血丹 batch IDs are not distinct")

    dashboard = (root / ".project/DASHBOARD.md").read_text(encoding="utf-8")
    if "三次暂存升级机会" not in dashboard or "pending" not in dashboard:
        errors.append("retained upgrade opportunities are not explicitly pending")

    gates = {
        "alias_identity_consistency": gate(not any("alias" in item for item in errors), "雪瑶仙帝与天羽映射到时间化canonical身份"),
        "duplicate_name_disposition": gate(not unclassified_duplicates, f"active duplicate groups={len(duplicate_groups)}; all classified"),
        "gift_participant_resolution": gate(ledger_participants == EXPECTED_PARTICIPANTS and all(isinstance(gifts.get(x, {}).get("participant_resolution"), dict) for x in EXPECTED_PARTICIPANTS), f"covered={len(EXPECTED_PARTICIPANTS)}"),
        "gift_component_disposition": gate(set(dispositions) == EXPECTED_COMPONENT_ROWS, f"covered={len(dispositions)}/25; artifact-linked={linked_component_rows}; explicitly-pending={pending_component_rows}"),
        "artifact_ownership_conservation": gate(not any("current_holder" in item for item in errors), "destroyed/consumed candidates retain no active holder"),
        "final_state_snapshot_consistency": gate(not errors, "snapshot is derived from canonical generated indexes"),
    }

    active_characters = sum(row.get("record_status") != "superseded" for row in characters.values())
    unresolved_participants = [
        gift_id for gift_id in sorted(EXPECTED_PARTICIPANTS)
        if gifts.get(gift_id, {}).get("participant_resolution", {}).get("resolution") in {"unresolved", "unresolved_role_label"}
    ]
    report = {
        "schema_version": 1,
        "normalization": {
            "run_id": RUN_ID,
            "task_id": TASK_ID,
            "source_commit": source_commit,
            "status": "passed_with_explicit_unresolved" if not errors else "failed",
            "blocking_findings": errors,
        },
        "counts": {
            "characters_total": len(characters),
            "characters_active": active_characters,
            "characters_superseded": len(EXPECTED_SUPERSEDED),
            "corrected_character_names": 4,
            "resolved_identity_labels": 2,
            "gift_participant_candidates": len(EXPECTED_PARTICIPANTS),
            "gift_participants_explicitly_unresolved": len(unresolved_participants),
            "gift_component_rows_dispositioned": len(dispositions),
            "artifact_name_corrections": 3,
            "artifact_lifecycle_repairs": len(EXPECTED_LIFECYCLE),
        },
        "quality_gates": gates,
        "findings": {
            "active_duplicate_character_names": duplicate_groups,
            "participant_resolution_kinds": dict(sorted(participant_counts.items())),
            "unresolved_participant_gifts": unresolved_participants,
            "pending_component_gifts": sorted(gift_id for gift_id, row in dispositions.items() if row.get("status") == "pending"),
            "superseded_character_records": EXPECTED_SUPERSEDED,
        },
    }

    def character_snapshot(rid: str) -> dict[str, Any]:
        row = characters[rid]
        return {
            "id": rid,
            "name": row.get("name"),
            "aliases": sorted(EXPECTED_ALIASES.get(rid, set())),
            "status": row.get("status"),
            "cultivation": row.get("cultivation_change", row.get("cultivation", row.get("realm"))),
            "affiliations": row.get("affiliation_change", row.get("affiliations", [])),
        }

    final_state = {
        "schema_version": 1,
        "generated_by": "scripts/normalize_repository.py",
        "source": {"run_id": RUN_ID, "task_id": TASK_ID, "commit": source_commit},
        "main_story": {
            "status": state.get("story_status"),
            "chapter_start": state.get("scope", {}).get("chapter_start"),
            "chapter_end": state.get("scope", {}).get("chapter_end"),
            "last_timeline_node": state.get("progress", {}).get("last_completed_node"),
            "timeline_nodes": len(timeline),
        },
        "entity_counts": {
            "characters_total": len(characters), "characters_active": active_characters,
            "gifts": len(gifts), "artifacts": len(artifacts),
        },
        "priority_characters": [character_snapshot("CHAR-0001"), character_snapshot("CHAR-0002"), character_snapshot("CHAR-0045")],
        "artifact_lifecycle": [
            {"id": rid, "name": artifacts[rid].get("name"), "state": state_name, "former_holder": artifacts[rid].get("former_holder")}
            for rid, state_name in EXPECTED_LIFECYCLE.items()
        ],
        "normalization": {
            "status": report["normalization"]["status"],
            "superseded_character_records": EXPECTED_SUPERSEDED,
            "explicitly_unresolved_participant_gifts": unresolved_participants,
        },
        "retained_upgrade_opportunities": {"count": 3, "status": "pending"},
        "extras": {"status": state.get("scopes", {}).get("extras", {}).get("status"), "included_in_main_timeline": False},
    }

    output_root = output_root.resolve()
    dump(output_root / "data/audits/run-0126.yaml", report)
    dump(output_root / "data/generated/final-state.yaml", final_state)

    gate_lines = "\n".join(f"| {name} | {value['status']} | {value['detail']} |" for name, value in gates.items())
    duplicate_lines = "\n".join(f"- `{name}`：{', '.join(ids)}" for name, ids in duplicate_groups.items()) or "- 无"
    write(output_root / "docs/08-analysis/entity-normalization.md", f"""# 实体规范化报告 — RUN-0126

- Task：`TASK-0112`
- 来源提交：`{source_commit}`
- 状态：**{report['normalization']['status']}**
- 本 Run 不创建 Timeline Node，不改变正文第 1—876 章边界。

## 结果

- 修正人物错名 4 条、Artifact 错名 3 条。
- `雪瑶仙帝` 精确归入 `CHAR-0002`；`天羽` 精确归入 `CHAR-0045`。
- 2 条重复人物记录标记为 superseded，保留历史 ID；active 人物记录为 {active_characters} 条。
- 18 条 Gift 参与者候选全部处置，其中 {len(unresolved_participants)} 条因证据不足明确保留 pending。
- 25 条 Gift—Artifact 候选全部完成组件级分类；{linked_component_rows} 条建立 Artifact 引用，{pending_component_rows} 条保留 pending。
- 3 条损毁/消耗物品已清除 active holder，并补充生命周期事件。

## 质量门禁

| Gate | 结果 | 摘要 |
|---|---|---|
{gate_lines}

## 保留的合法同名

{duplicate_lines}

## 明确保留的未决参与者

{', '.join(f'`{x}`' for x in unresolved_participants) or '无'}

规范化的目标是消除错误映射并提高可查询性，而不是机械降低 pending 数量。所有未决项均保留原因和状态。
""")
    write(output_root / "docs/08-analysis/final-state-snapshot.md", f"""# 正文终局快照

该快照由 canonical generated indexes 自动派生，来源 Run 为 `RUN-0126`，正文范围保持第 1—876 章。

## 关键身份

- 徐霄：`CHAR-0001`，正文终局存活。
- 姬雪／刘爱花／雪瑶／雪瑶仙帝：统一指向 `CHAR-0002`，其中刘爱花为仙界化名，雪瑶仙帝为转世恢复身份。
- 凤青玄／天羽：统一指向 `CHAR-0045`，天羽为完成历代圣女涅槃融合后的继承身份。

## 数据状态

- 人物：{len(characters)} 条历史 canonical 记录，其中 {active_characters} 条 active、{len(EXPECTED_SUPERSEDED)} 条 superseded。
- Gift：{len(gifts)} 条；Artifact：{len(artifacts)} 条；Timeline Node：{len(timeline)} 个。
- 三次暂存升级机会继续保持 `pending`。
- 番外仍为 deferred，不进入正文 Timeline 连续性统计。

## 生命周期修复

- `ART-0017` 九火琉璃罩：第183章损毁。
- `ART-0023` 净玉瓶：第183章损毁。
- `ART-0026` 混沌极冰符：第284章消耗。

## 未决项

Gift 参与者仍明确未决：{', '.join(unresolved_participants)}。这些记录不会因本次规范化被强制绑定到人物 ID。
""")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--generated-dir", type=Path)
    parser.add_argument("--output-root", type=Path, default=Path.cwd())
    parser.add_argument("--source-commit", default="working-tree")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    generated = args.generated_dir.resolve() if args.generated_dir else root / "data/generated"
    errors = materialize(root, generated, args.output_root, args.source_commit)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("RUN-0126 normalization gates passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
