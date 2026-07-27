#!/usr/bin/env python3
"""Render reader-friendly character and artifact Markdown from canonical indexes."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml

MANIFEST_PATH = Path("docs/entity-docs-manifest.yaml")
INDEX_FILES = {
    "characters": ("characters.yaml", "characters", Path("docs/02-characters")),
    "artifacts": ("artifacts.yaml", "artifacts", Path("docs/06-artifacts")),
}
INVALID_FILENAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

LABELS = {
    "affiliations": "所属势力", "affiliation": "所属势力", "identities": "身份", "identity": "身份",
    "title": "称号 / 职位", "current_duty": "当前职责", "strategic_role": "战略作用", "role_change": "角色变化",
    "cultivation": "修为", "cultivation_change": "最新修为变化", "cultivation_goal": "修炼目标",
    "age": "年龄", "age_change": "年龄变化", "lifespan": "寿命", "lifespan_change": "寿命变化",
    "luck_grade": "气运等级", "base_multiplier": "基础倍率", "constitution": "体质", "body_effect": "肉身效果",
    "body_resource": "肉身资源", "dao_comprehension": "大道领悟", "power_change": "能力变化",
    "ability": "能力", "abilities": "能力", "array_ability": "阵法能力", "retained_spiritual_sense": "保留神识",
    "hongmeng_qi": "鸿蒙真气", "hongmeng_qi_strands": "鸿蒙真气股数", "condition_change": "状态变化",
    "appearance_recovery": "外貌恢复", "tribulation_record": "渡劫记录", "bond_level": "羁绊度",
    "bond_level_set": "羁绊度", "relationship_change": "关系变化", "relationship_updates": "关系更新",
    "relationship_context": "关系背景", "attitude_change": "态度变化", "enemy_relation": "敌对关系",
    "conflict_context": "冲突背景", "outer_sect_protection": "对外保护", "resource": "核心资源",
    "resource_support": "资源支持", "accepted_gifts": "接受赠送", "accepted_resources": "接受资源",
    "accepted_return": "已接受返还", "artifact_changes": "物品变化", "public_combat_record": "公开战绩",
    "combat_record": "战斗记录", "battle_record": "战斗记录", "major_conflict": "重大冲突",
    "reputation_change": "声望变化", "travel_plan": "行动计划", "public_plan": "公开计划",
    "current_action": "当前行动", "system_behavior": "系统互动", "system_change": "系统变化",
    "system_progress": "系统进度", "system_task_completion": "系统任务结算", "category": "类别", "grade": "品阶",
    "acquisition": "获得方式", "acquisitions": "获得记录", "new_acquisition": "新增获得记录",
    "source_gift": "来源赠送", "source_gifts": "来源赠送", "current_holder": "当前持有人", "holder": "持有人",
    "final_user": "最终使用者", "transfer": "流转记录", "transfers": "流转记录", "transfer_event": "流转事件",
    "transferred_from": "转出者", "transferred_to": "转入者", "transferred_in_chapter": "流转章节",
    "acceptance_confirmed_in_chapter": "确认接受章节", "effect": "效果", "effects": "效果", "properties": "特性",
    "refinement": "炼化状态", "growth_change": "成长变化", "battle_use": "战斗用途",
    "latest_battle_use": "最近战斗用途", "latest_use": "最近用途", "strategic_use": "战略用途",
    "consumption_event": "消耗事件", "consumption": "消耗记录", "current_state": "当前状态", "quantity": "数量",
    "initial_quantity": "初始数量", "quantity_consumed": "已消耗数量", "recorded_return_quantity": "已记录返还数量",
    "inferred_remaining_quantity": "推定剩余数量", "remaining_quantity_statement": "剩余数量说明",
    "instances_acquired_total": "累计获得次数", "instances_consumed_total": "累计消耗次数",
    "confirmed_acquisitions": "已确认获得次数", "confirmed_consumptions": "已确认消耗次数",
    "acquisition_result": "获得 / 使用结果", "consumption_status": "消耗状态", "post_tribulation_state": "渡劫后状态",
    "pending": "未决字段", "pending_fields": "未决字段", "continuity_warning": "连续性警告",
    "continuity_warnings": "连续性警告", "conflict": "冲突记录", "conflicts": "冲突记录",
    "source_qualification": "来源资格",
}

CHAR_SECTIONS = [
    ("身份与阵营", ("affiliations", "affiliation", "identities", "identity", "title", "current_duty", "strategic_role", "role_change")),
    ("修为、能力与成长", ("cultivation", "cultivation_change", "cultivation_goal", "age", "age_change", "lifespan", "lifespan_change", "luck_grade", "base_multiplier", "constitution", "body_effect", "body_resource", "dao_comprehension", "power_change", "ability", "abilities", "array_ability", "retained_spiritual_sense", "hongmeng_qi", "hongmeng_qi_strands", "condition_change", "appearance_recovery", "tribulation_record")),
    ("关系与立场", ("bond_level", "bond_level_set", "relationship_change", "relationship_updates", "relationship_context", "attitude_change", "enemy_relation", "conflict_context", "outer_sect_protection")),
    ("资源与物品", ("resource", "resource_support", "accepted_gifts", "accepted_resources", "accepted_return", "artifact_changes")),
    ("关键经历", ("public_combat_record", "combat_record", "battle_record", "major_conflict", "reputation_change", "travel_plan", "public_plan", "current_action", "system_behavior", "system_change", "system_progress", "system_task_completion")),
]
ART_SECTIONS = [
    ("获取、持有与流转", ("acquisition", "acquisitions", "new_acquisition", "source_gift", "source_gifts", "current_holder", "holder", "final_user", "transfer", "transfers", "transfer_event", "transferred_from", "transferred_to", "transferred_in_chapter", "acceptance_confirmed_in_chapter")),
    ("能力与效果", ("effect", "effects", "properties", "ability", "abilities", "refinement", "growth_change")),
    ("使用与战斗记录", ("battle_use", "latest_battle_use", "latest_use", "strategic_use", "combat_record", "consumption_event", "consumption")),
    ("数量与当前状态", ("current_state", "quantity", "initial_quantity", "quantity_consumed", "recorded_return_quantity", "inferred_remaining_quantity", "remaining_quantity_statement", "instances_acquired_total", "instances_consumed_total", "confirmed_acquisitions", "confirmed_consumptions", "acquisition_result", "consumption_status", "post_tribulation_state")),
]
META = {"id", "name", "status", "role", "category", "grade", "first_appearance", "first_chapter", "documents", "document", "verification_status", "source_chapters", "related_nodes"}
WARNINGS = {"pending", "pending_fields", "continuity_warning", "continuity_warnings", "conflict", "conflicts", "source_qualification"}


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise RuntimeError(f"cannot read YAML {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"top-level YAML must be a mapping: {path}")
    return value


def dump_yaml(value: Any) -> str:
    return yaml.safe_dump(value, allow_unicode=True, sort_keys=False, width=120).rstrip()


def safe_filename(name: str, record_id: str) -> str:
    cleaned = INVALID_FILENAME_RE.sub("＿", name).strip().rstrip(".") or record_id
    return f"{cleaned}.md"


def explicit_document_path(record: dict[str, Any], group: str) -> str | None:
    candidate: Any = None
    if group == "characters":
        docs = record.get("documents")
        candidate = docs.get("profile") if isinstance(docs, dict) else None
        candidate = candidate or record.get("document")
    else:
        candidate = record.get("document")
    if not isinstance(candidate, str) or not candidate.endswith(".md"):
        return None
    path = Path(candidate)
    try:
        path.relative_to(INDEX_FILES[group][2])
    except ValueError:
        return None
    return path.as_posix()


def choose_paths(records: list[dict[str, Any]], group: str) -> dict[str, str]:
    used: dict[str, str] = {}
    result: dict[str, str] = {}
    root = INDEX_FILES[group][2]
    for record in records:
        rid = str(record.get("id") or "")
        path = explicit_document_path(record, group) or (root / safe_filename(str(record.get("name") or rid), rid)).as_posix()
        if path.casefold() in used and used[path.casefold()] != rid:
            path = (root / f"{Path(path).stem}-{rid}.md").as_posix()
        used[path.casefold()] = rid
        result[rid] = path
    return result


def label(key: str) -> str:
    return LABELS.get(key, key.replace("_", " "))


def text(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "是" if value else "否"
    return str(value)


def status_text(value: Any) -> str:
    return {"alive": "存活", "dead": "死亡", "unknown": "未知", "partial": "部分核验", "verified": "已核验", "pending": "待确认", "inferred": "推断", "conflict": "存在冲突", "protagonist": "主角", "supporting": "重要配角", "antagonist": "对立角色"}.get(str(value), text(value))


def brief(value: Any, limit: int = 4) -> str:
    if value is None:
        return "—"
    if isinstance(value, dict):
        for key in ("current", "value", "remaining_years", "state", "result", "level"):
            if key in value and not isinstance(value[key], (dict, list)):
                return text(value[key])
        parts = [f"{label(str(k))}：{text(v)}" for k, v in value.items() if not isinstance(v, (dict, list))]
        return "；".join(parts[:limit]) or "详见正文"
    if isinstance(value, list):
        values = [text(item) for item in value if not isinstance(item, (dict, list))]
        if values:
            return "、".join(values[:limit]) + (f" 等 {len(values)} 项" if len(values) > limit else "")
        return f"{len(value)} 项记录"
    return text(value)


def current_realm(record: dict[str, Any]) -> str:
    changed = record.get("cultivation_change")
    if isinstance(changed, str):
        return changed
    if isinstance(changed, list):
        values = [text(item) for item in changed if not isinstance(item, (dict, list))]
        if values:
            return values[-1]
    return brief(record.get("cultivation"))


def current_value(record: dict[str, Any], primary: str, changed: str) -> str:
    value = record.get(changed)
    if isinstance(value, (str, int, float, bool)):
        return text(value)
    if isinstance(value, list):
        values = [text(item) for item in value if not isinstance(item, (dict, list))]
        if values:
            return values[-1]
    return brief(record.get(primary))


def first_appearance(record: dict[str, Any], group: str) -> str:
    if group == "artifacts":
        chapter = record.get("first_chapter")
        return f"第 {chapter} 章" if chapter is not None else "—"
    value = record.get("first_appearance")
    if not isinstance(value, dict):
        return brief(value)
    parts = []
    if value.get("chapter") is not None:
        parts.append(f"第 {value['chapter']} 章")
    if value.get("title"):
        parts.append(f"《{value['title']}》")
    if value.get("node"):
        parts.append(f"`{value['node']}`")
    return " ".join(parts) or "—"


def compress_numbers(numbers: Iterable[int]) -> str:
    values = sorted(set(numbers))
    if not values:
        return "—"
    out: list[str] = []
    start = previous = values[0]
    for number in values[1:]:
        if number == previous + 1:
            previous = number
            continue
        out.append(str(start) if start == previous else f"{start}—{previous}")
        start = previous = number
    out.append(str(start) if start == previous else f"{start}—{previous}")
    return "、".join(out)


def render_nested(value: Any, indent: int = 0) -> list[str]:
    prefix = "  " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, child in value.items():
            if isinstance(child, (dict, list)):
                lines.append(f"{prefix}- **{label(str(key))}**")
                lines.extend(render_nested(child, indent + 1))
            else:
                lines.append(f"{prefix}- **{label(str(key))}**：{text(child)}")
        return lines
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(render_nested(item, indent + 1))
            else:
                lines.append(f"{prefix}- {text(item)}")
        return lines
    return [f"{prefix}- {text(value)}"]


def render_field(key: str, value: Any) -> list[str]:
    if isinstance(value, (dict, list)):
        return [f"- **{label(key)}**", *render_nested(value, 1)]
    return [f"- **{label(key)}**：{text(value)}"]


def render_section(record: dict[str, Any], keys: tuple[str, ...], consumed: set[str]) -> list[str]:
    lines: list[str] = []
    for key in keys:
        if key in record and record[key] not in (None, [], {}, ""):
            lines.extend(render_field(key, record[key]))
            consumed.add(key)
    return lines


def overview(record: dict[str, Any], group: str, rid: str) -> list[tuple[str, str]]:
    if group == "characters":
        return [("ID", f"`{rid}`"), ("状态", status_text(record.get("status"))), ("角色定位", status_text(record.get("role"))), ("首次登场", first_appearance(record, group)), ("当前境界", current_realm(record)), ("年龄", current_value(record, "age", "age_change")), ("剩余寿命", current_value(record, "lifespan", "lifespan_change")), ("主要势力", brief(record.get("affiliations", record.get("affiliation")))), ("核心身份", brief(record.get("identities", record.get("identity"))))]
    return [("ID", f"`{rid}`"), ("类别", brief(record.get("category"))), ("品阶", brief(record.get("grade"))), ("首次出现", first_appearance(record, group)), ("当前持有人", brief(record.get("current_holder", record.get("holder")))), ("最终使用者", brief(record.get("final_user"))), ("当前状态", brief(record.get("current_state"))), ("核验状态", status_text(record.get("status")))]


def source_section(record: dict[str, Any], updated: str) -> list[str]:
    chapters = record.get("source_chapters")
    nodes = record.get("related_nodes")
    numbers = [item for item in chapters if isinstance(item, int)] if isinstance(chapters, list) else []
    summary = f"{len(numbers)} 章；范围 {min(numbers)}—{max(numbers)}" if numbers else "—"
    lines = ["## 来源与核验", "", f"- **核验状态**：{status_text(record.get('verification_status', record.get('status')))}", f"- **来源章节**：{summary}", f"- **关联剧情节点**：{len(nodes) if isinstance(nodes, list) else 0} 个", f"- **Canonical 索引更新时间**：{updated or '—'}"]
    details = []
    if numbers:
        details.append(f"- 来源章节：{compress_numbers(numbers)}")
    if isinstance(nodes, list) and nodes:
        details.append("- 关联节点：" + "、".join(f"`{item}`" for item in nodes))
    if details:
        lines += ["", "<details>", "<summary>查看完整来源章节与关联节点</summary>", "", *details, "", "</details>"]
    return [*lines, ""]


def warning_section(record: dict[str, Any], consumed: set[str]) -> list[str]:
    lines: list[str] = []
    verification = status_text(record.get("verification_status", record.get("status")))
    if verification in {"部分核验", "待确认", "推断", "存在冲突"}:
        lines.append(f"- **整体核验状态**：{verification}；阅读时应保留不确定性。")
    for key in WARNINGS:
        if key in record and record[key] not in (None, [], {}, ""):
            lines.extend(render_field(key, record[key]))
            consumed.add(key)
    return ["## 未决与注意事项", "", *lines, ""] if lines else []


def render_profile(record: dict[str, Any], group: str, updated: str) -> str:
    rid = str(record.get("id") or "UNKNOWN")
    name = str(record.get("name") or rid)
    consumed = set(META)
    lines = [f"# {name}", "", "<!-- AUTO-GENERATED FROM CANONICAL INDEX. DO NOT EDIT BY HAND. -->", "", "> 本档案面向读者展示；事实来自 canonical 索引。结构化原始记录默认折叠在文末。", "", "## 一览", "", "| 字段 | 当前信息 |", "|---|---|"]
    for key, value in overview(record, group, rid):
        if value not in ("", "—"):
            lines.append(f"| {key} | {value.replace('|', r'\|')} |")
    lines.append("")
    sections = CHAR_SECTIONS if group == "characters" else ART_SECTIONS
    for title, keys in sections:
        content = render_section(record, keys, consumed)
        if content:
            lines += [f"## {title}", "", *content, ""]
    warnings = warning_section(record, consumed)
    extra = [key for key in record if key not in consumed and key not in WARNINGS and record[key] not in (None, [], {}, "")]
    if extra:
        lines += ["## 补充信息", ""]
        for key in extra:
            lines.extend(render_field(key, record[key]))
        lines.append("")
    lines += source_section(record, updated)
    lines += warnings
    lines += ["<details>", "<summary>结构化数据附录（供维护与审计）</summary>", "", "以下 YAML 是基础索引与全部追加扩展合并后的完整机器记录。日常阅读无需展开。", "", "```yaml", dump_yaml(record), "```", "", "</details>", ""]
    return "\n".join(lines)


def render_index(records: list[dict[str, Any]], paths: dict[str, str], group: str) -> str:
    title = "人物档案索引" if group == "characters" else "物品档案索引"
    lines = [f"# {title}", "", "<!-- AUTO-GENERATED FROM CANONICAL INDEX. DO NOT EDIT BY HAND. -->", "", f"- Canonical 记录数：**{len(records)}**", "- 每个条目优先展示读者版摘要、分主题事实和未决项；机器 YAML 默认折叠在文末。", "- 文档由 `scripts/render_entity_docs.py` 自动生成；事实修正应写入基础索引或追加扩展。", ""]
    lines += ["| ID | 名称 | 状态 | 当前境界 | 主要势力 | 文档 |", "|---|---|---|---|---|---|"] if group == "characters" else ["| ID | 名称 | 类别 | 品阶 | 持有人 / 状态 | 文档 |", "|---|---|---|---|---|---|"]
    root = INDEX_FILES[group][2]
    for record in records:
        rid = str(record.get("id") or "")
        name = str(record.get("name") or rid).replace("|", r"\|")
        rel = Path(paths[rid]).relative_to(root).as_posix()
        if group == "characters":
            row = (status_text(record.get("status")), current_realm(record), brief(record.get("affiliations", record.get("affiliation"))))
        else:
            row = (brief(record.get("category")), brief(record.get("grade")), brief(record.get("current_holder", record.get("holder", record.get("current_state")))))
        lines.append(f"| `{rid}` | {name} | {row[0]} | {row[1]} | {row[2]} | [{Path(rel).stem}]({rel}) |")
    return "\n".join([*lines, ""])


def expected_files(repo_root: Path, output_root: Path, generated_dir: Path) -> tuple[dict[Path, str], dict[str, Any]]:
    outputs: dict[Path, str] = {}
    manifest: dict[str, Any] = {"schema_version": 2, "generator": "scripts/render_entity_docs.py", "presentation": "reader_friendly_with_collapsed_canonical_appendix", "source": generated_dir.relative_to(repo_root).as_posix() if generated_dir.is_relative_to(repo_root) else generated_dir.as_posix(), "groups": {}}
    for group, (filename, key, target_root) in INDEX_FILES.items():
        index = load_yaml(generated_dir / filename)
        records = index.get(key)
        if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
            raise RuntimeError(f"{generated_dir / filename}:{key} must be a list of mappings")
        records = sorted(records, key=lambda item: str(item.get("id") or ""))
        paths = choose_paths(records, group)
        updated = str(index.get("updated_at") or "")
        for record in records:
            rid = str(record.get("id") or "")
            outputs[output_root / paths[rid]] = render_profile(record, group, updated)
        outputs[output_root / target_root / "_INDEX.md"] = render_index(records, paths, group)
        index_path = generated_dir / filename
        manifest["groups"][group] = {"count": len(records), "index": index_path.relative_to(repo_root).as_posix() if index_path.is_relative_to(repo_root) else index_path.as_posix(), "index_document": (target_root / "_INDEX.md").as_posix(), "documents": [{"id": str(item.get("id") or ""), "path": paths[str(item.get("id") or "")]} for item in records]}
    outputs[output_root / MANIFEST_PATH] = dump_yaml(manifest) + "\n"
    return outputs, manifest


def prior_managed_paths(output_root: Path) -> set[Path]:
    path = output_root / MANIFEST_PATH
    if not path.exists():
        return set()
    manifest = load_yaml(path)
    managed: set[Path] = {path}
    for group in manifest.get("groups", {}).values():
        if not isinstance(group, dict):
            continue
        if isinstance(group.get("index_document"), str):
            managed.add(output_root / group["index_document"])
        for item in group.get("documents", []):
            if isinstance(item, dict) and isinstance(item.get("path"), str):
                managed.add(output_root / item["path"])
    return managed


def compare(outputs: dict[Path, str]) -> list[str]:
    errors = []
    for path, expected in sorted(outputs.items()):
        if not path.exists():
            errors.append(f"missing generated entity document: {path}")
        elif path.read_text(encoding="utf-8") != expected:
            errors.append(f"stale generated entity document: {path}")
    return errors


def write(outputs: dict[Path, str], previous: set[Path]) -> None:
    for stale in sorted(previous - set(outputs)):
        if stale.exists() and stale.is_file():
            stale.unlink()
    for path, content in sorted(outputs.items()):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--generated-dir", type=Path, default=Path("data/generated"))
    parser.add_argument("--output-root", type=Path, default=Path("."))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    generated = args.generated_dir if args.generated_dir.is_absolute() else root / args.generated_dir
    output = args.output_root if args.output_root.is_absolute() else root / args.output_root
    try:
        outputs, manifest = expected_files(root, output, generated)
        if args.check:
            errors = compare(outputs)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print(f"entity documents are current and reader-friendly: {manifest['groups']['characters']['count']} characters, {manifest['groups']['artifacts']['count']} artifacts")
        else:
            write(outputs, prior_managed_paths(output))
            print(f"rendered reader-friendly entity documents: {manifest['groups']['characters']['count']} characters, {manifest['groups']['artifacts']['count']} artifacts")
    except (OSError, RuntimeError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
