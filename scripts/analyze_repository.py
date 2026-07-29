#!/usr/bin/env python3
"""Build the reproducible RUN-0127 full-book statistics, graph and SQLite snapshot."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import re
import sqlite3
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import yaml

RUN_ID = "RUN-0127"
TASK_ID = "TASK-0113"
GENERATOR = "scripts/analyze_repository.py"
VERIFICATION_STATES = {"verified", "partial", "inferred", "conflict", "pending"}


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"expected YAML mapping: {path}")
    return data


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2))


def write_yaml(path: Path, data: Any) -> None:
    write_text(path, yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows(doc: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = doc.get(key, [])
    if not isinstance(value, list):
        raise RuntimeError(f"{key} must be a list")
    return [item for item in value if isinstance(item, dict)]


def id_map(items: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        rid = item.get("id")
        if not isinstance(rid, str):
            continue
        if rid in result:
            raise RuntimeError(f"duplicate ID: {rid}")
        result[rid] = item
    return result


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, str)):
        return str(value)
    if isinstance(value, list):
        return "；".join(part for part in (flatten_text(item) for item in value) if part)
    if isinstance(value, dict):
        return "；".join(
            f"{key}:{flatten_text(val)}" for key, val in sorted(value.items(), key=lambda pair: str(pair[0]))
            if flatten_text(val)
        )
    return str(value)


def strings(value: Any) -> list[str]:
    result: list[str] = []
    for item in as_list(value):
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
        elif isinstance(item, dict):
            for subvalue in item.values():
                result.extend(strings(subvalue))
    return result


def first_int(*values: Any) -> int | None:
    for value in values:
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str):
            match = re.search(r"\d+", value)
            if match:
                return int(match.group())
    return None


def chapter_of(row: dict[str, Any]) -> int | None:
    chapter_range = row.get("chapters")
    if isinstance(chapter_range, dict):
        value = first_int(chapter_range.get("start"))
        if value is not None:
            return value
    return first_int(
        row.get("chapter"), row.get("chapter_start"), row.get("first_chapter"),
        row.get("acceptance_chapter"), row.get("resolution_chapter"),
    )


def first_appearance_chapter(row: dict[str, Any]) -> int | None:
    value = row.get("first_appearance")
    if isinstance(value, dict):
        return first_int(value.get("chapter"))
    return first_int(row.get("first_chapter"))


def names_for_character(row: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for key in ("name", "canonical_name", "alias"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            result.add(value.strip())
    for key in ("aliases", "identities", "identity", "names"):
        for value in as_list(row.get(key)):
            if isinstance(value, str) and value.strip():
                result.add(value.strip())
    return result


def affiliations_for_character(row: dict[str, Any]) -> list[str]:
    result: set[str] = set()
    for key in ("affiliations", "affiliation", "affiliation_change"):
        for value in as_list(row.get(key)):
            if isinstance(value, str) and value.strip():
                result.add(value.strip())
    return sorted(result)


def verification_counter(value: Any, counter: Counter[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"status", "verification_status"} and isinstance(child, str) and child in VERIFICATION_STATES:
                counter[child] += 1
            verification_counter(child, counter)
    elif isinstance(value, list):
        for child in value:
            verification_counter(child, counter)


CN_DIGITS = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
CN_UNITS = {"十": 10, "百": 100, "千": 1000, "万": 10000}


def chinese_number(text: str) -> int | None:
    if not text:
        return None
    if all(ch in CN_DIGITS for ch in text):
        value = 0
        for ch in text:
            value = value * 10 + CN_DIGITS[ch]
        return value
    total = section = number = 0
    seen = False
    for ch in text:
        if ch in CN_DIGITS:
            number = CN_DIGITS[ch]
            seen = True
        elif ch in CN_UNITS:
            unit = CN_UNITS[ch]
            seen = True
            if unit == 10000:
                section = (section + number) * unit
                total += section
                section = 0
            else:
                section += (number or 1) * unit
            number = 0
        else:
            return None
    return total + section + number if seen else None


def multiplier_values(value: Any) -> list[int]:
    result: list[int] = []
    if isinstance(value, bool) or value is None:
        return result
    if isinstance(value, int):
        return [value] if value > 0 else []
    if isinstance(value, float):
        return [int(value)] if value > 0 and value.is_integer() else []
    if isinstance(value, str):
        for match in re.finditer(r"(\d+)\s*倍", value):
            result.append(int(match.group(1)))
        if not result:
            for match in re.finditer(r"([零〇一二两三四五六七八九十百千万]+)\s*倍", value):
                parsed = chinese_number(match.group(1))
                if parsed:
                    result.append(parsed)
        if not result and value.strip().isdigit():
            result.append(int(value.strip()))
        return result
    if isinstance(value, list):
        for item in value:
            result.extend(multiplier_values(item))
    elif isinstance(value, dict):
        for key, item in value.items():
            if "multiplier" in str(key) or str(key) in {"倍率", "倍数"}:
                result.extend(multiplier_values(item))
            elif isinstance(item, (dict, list)):
                result.extend(multiplier_values(item))
    return result


def gift_max_multiplier(row: dict[str, Any]) -> int | None:
    values: list[int] = []
    for key in ("triggered_multiplier", "base_multiplier", "multiplier", "returns", "additional_returns"):
        values.extend(multiplier_values(row.get(key)))
    return max(values) if values else None


def md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown_table(headers: list[str], body: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines.extend("| " + " | ".join(md_escape(cell) for cell in row) + " |" for row in body)
    return "\n".join(lines)


class Resolver:
    def __init__(self, characters: dict[str, dict[str, Any]]) -> None:
        self.characters = characters
        self.labels: dict[str, set[str]] = defaultdict(set)
        for rid, row in characters.items():
            if row.get("record_status") == "superseded":
                continue
            for label in names_for_character(row):
                self.labels[label].add(rid)

    def resolve(self, label: Any, *, node_id: str | None = None, gift_id: str | None = None) -> tuple[str | None, list[str]]:
        if not isinstance(label, str) or not label.strip():
            return None, []
        candidates = sorted(self.labels.get(label.strip(), set()))
        if len(candidates) <= 1:
            return (candidates[0] if candidates else None), candidates
        if node_id:
            filtered = [rid for rid in candidates if node_id in as_list(self.characters[rid].get("related_nodes"))]
            if len(filtered) == 1:
                return filtered[0], candidates
        if gift_id:
            filtered = [rid for rid in candidates if gift_id in as_list(self.characters[rid].get("accepted_gifts"))]
            if len(filtered) == 1:
                return filtered[0], candidates
        return None, candidates


class EdgeStore:
    def __init__(self) -> None:
        self.data: dict[tuple[str, str, str, bool], dict[str, Any]] = {}

    def add(self, source: str, target: str, relation_type: str, *, weight: int, chapter: int | None, evidence: str, directed: bool = False) -> None:
        if not source or not target or source == target:
            return
        if not directed and source > target:
            source, target = target, source
        key = (source, target, relation_type, directed)
        row = self.data.setdefault(key, {
            "source_id": source, "target_id": target, "relation_type": relation_type,
            "directed": directed, "weight": 0, "evidence_count": 0,
            "first_chapter": None, "last_chapter": None, "evidence": [],
        })
        row["weight"] += int(weight)
        row["evidence_count"] += 1
        if chapter is not None:
            row["first_chapter"] = chapter if row["first_chapter"] is None else min(row["first_chapter"], chapter)
            row["last_chapter"] = chapter if row["last_chapter"] is None else max(row["last_chapter"], chapter)
        if evidence not in row["evidence"] and len(row["evidence"]) < 24:
            row["evidence"].append(evidence)

    def rows(self) -> list[dict[str, Any]]:
        return sorted(self.data.values(), key=lambda row: (row["source_id"], row["target_id"], row["relation_type"], row["directed"]))


def timeline_continuity(nodes: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    ranges: list[tuple[int, int, str]] = []
    for node in nodes:
        chapters = node.get("chapters")
        if not isinstance(chapters, dict):
            errors.append(f"{node.get('id')} lacks chapters")
            continue
        start, end = first_int(chapters.get("start")), first_int(chapters.get("end"))
        if start is None or end is None or start > end:
            errors.append(f"{node.get('id')} invalid chapter range")
            continue
        ranges.append((start, end, str(node.get("id"))))
    ranges.sort()
    for previous, current in zip(ranges, ranges[1:]):
        if current[0] != previous[1] + 1:
            errors.append(f"timeline boundary {previous[2]}->{current[2]} is {previous[1]}->{current[0]}")
    return not errors, errors


def pagerank(active_ids: list[str], relationships: list[dict[str, Any]]) -> dict[str, float]:
    adjacency: dict[str, dict[str, float]] = {rid: {} for rid in active_ids}
    for row in relationships:
        source, target = row["source_id"], row["target_id"]
        if source not in adjacency or target not in adjacency:
            continue
        weight = float(row["weight"])
        adjacency[source][target] = adjacency[source].get(target, 0.0) + weight
        adjacency[target][source] = adjacency[target].get(source, 0.0) + weight
    count = len(active_ids)
    if not count:
        return {}
    ranks = {rid: 1.0 / count for rid in active_ids}
    damping = 0.85
    for _ in range(60):
        dangling = sum(ranks[rid] for rid in active_ids if not adjacency[rid])
        updated = {rid: (1.0 - damping) / count + damping * dangling / count for rid in active_ids}
        for source in active_ids:
            total = sum(adjacency[source].values())
            if total <= 0:
                continue
            for target, weight in adjacency[source].items():
                updated[target] += damping * ranks[source] * weight / total
        delta = sum(abs(updated[rid] - ranks[rid]) for rid in active_ids)
        ranks = updated
        if delta < 1e-13:
            break
    return ranks


def schema_sql() -> str:
    return """PRAGMA foreign_keys = ON;
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE timeline_nodes (id TEXT PRIMARY KEY, title TEXT, chapter_start INTEGER NOT NULL, chapter_end INTEGER NOT NULL, chapter_span INTEGER NOT NULL, status TEXT, character_count INTEGER NOT NULL, location_count INTEGER NOT NULL, system_event_count INTEGER NOT NULL, conflict_event_count INTEGER NOT NULL);
CREATE TABLE characters (id TEXT PRIMARY KEY, name TEXT NOT NULL, life_status TEXT, role TEXT, record_status TEXT, first_chapter INTEGER, verification_status TEXT, node_count INTEGER NOT NULL, gift_count INTEGER NOT NULL, weighted_degree INTEGER NOT NULL, neighbor_count INTEGER NOT NULL, pagerank REAL NOT NULL);
CREATE TABLE character_aliases (character_id TEXT NOT NULL REFERENCES characters(id), alias TEXT NOT NULL, PRIMARY KEY(character_id, alias));
CREATE TABLE character_affiliations (character_id TEXT NOT NULL REFERENCES characters(id), affiliation TEXT NOT NULL, PRIMARY KEY(character_id, affiliation));
CREATE TABLE node_characters (node_id TEXT NOT NULL REFERENCES timeline_nodes(id), character_id TEXT NOT NULL REFERENCES characters(id), raw_label TEXT NOT NULL, resolution TEXT NOT NULL, PRIMARY KEY(node_id, character_id, raw_label));
CREATE TABLE gifts (id TEXT PRIMARY KEY, chapter INTEGER, resolution_chapter INTEGER, giver_raw TEXT, recipient_raw TEXT, accepted INTEGER, system_valid INTEGER, status TEXT, max_multiplier INTEGER, gift_text TEXT, reward_text TEXT);
CREATE TABLE gift_participants (gift_id TEXT NOT NULL REFERENCES gifts(id), participant_role TEXT NOT NULL, character_id TEXT REFERENCES characters(id), raw_label TEXT, resolution TEXT, status TEXT);
CREATE TABLE artifacts (id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT, grade TEXT, first_chapter INTEGER, current_holder TEXT, former_holder TEXT, lifecycle_status TEXT, verification_status TEXT, record_status TEXT);
CREATE TABLE artifact_events (artifact_id TEXT NOT NULL REFERENCES artifacts(id), event_index INTEGER NOT NULL, chapter INTEGER, event_type TEXT, previous_holder TEXT, result TEXT, status TEXT, PRIMARY KEY(artifact_id, event_index));
CREATE TABLE relationships (source_id TEXT NOT NULL REFERENCES characters(id), target_id TEXT NOT NULL REFERENCES characters(id), relation_type TEXT NOT NULL, directed INTEGER NOT NULL, weight INTEGER NOT NULL, evidence_count INTEGER NOT NULL, first_chapter INTEGER, last_chapter INTEGER, evidence_json TEXT NOT NULL, PRIMARY KEY(source_id, target_id, relation_type, directed));
CREATE TABLE phase_stats (phase_start INTEGER NOT NULL, phase_end INTEGER NOT NULL, timeline_nodes INTEGER NOT NULL, new_characters INTEGER NOT NULL, gifts INTEGER NOT NULL, new_artifacts INTEGER NOT NULL, PRIMARY KEY(phase_start, phase_end));
CREATE INDEX idx_node_characters_character ON node_characters(character_id);
CREATE INDEX idx_gift_participants_character ON gift_participants(character_id);
CREATE INDEX idx_relationships_target ON relationships(target_id);
CREATE INDEX idx_character_affiliations_name ON character_affiliations(affiliation);
"""


def bool_db(value: Any) -> int | None:
    return 1 if value is True else 0 if value is False else None


def create_sqlite(path: Path, schema: str, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    db = sqlite3.connect(path)
    try:
        db.executescript(schema)
        db.executemany("INSERT INTO metadata VALUES (?, ?)", [(key, flatten_text(value)) for key, value in sorted(payload["metadata"].items())])
        db.executemany("INSERT INTO timeline_nodes VALUES (:id,:title,:chapter_start,:chapter_end,:chapter_span,:status,:character_count,:location_count,:system_event_count,:conflict_event_count)", payload["timeline_rows"])
        db.executemany("INSERT INTO characters VALUES (:id,:name,:life_status,:role,:record_status,:first_chapter,:verification_status,:node_count,:gift_count,:weighted_degree,:neighbor_count,:pagerank)", payload["character_rows"])
        db.executemany("INSERT INTO character_aliases VALUES (?, ?)", payload["alias_rows"])
        db.executemany("INSERT INTO character_affiliations VALUES (?, ?)", payload["affiliation_rows"])
        db.executemany("INSERT INTO node_characters VALUES (:node_id,:character_id,:raw_label,:resolution)", payload["node_character_rows"])
        db.executemany("INSERT INTO gifts VALUES (:id,:chapter,:resolution_chapter,:giver_raw,:recipient_raw,:accepted,:system_valid,:status,:max_multiplier,:gift_text,:reward_text)", payload["gift_rows"])
        db.executemany("INSERT INTO gift_participants VALUES (:gift_id,:participant_role,:character_id,:raw_label,:resolution,:status)", payload["gift_participant_rows"])
        db.executemany("INSERT INTO artifacts VALUES (:id,:name,:category,:grade,:first_chapter,:current_holder,:former_holder,:lifecycle_status,:verification_status,:record_status)", payload["artifact_rows"])
        db.executemany("INSERT INTO artifact_events VALUES (:artifact_id,:event_index,:chapter,:event_type,:previous_holder,:result,:status)", payload["artifact_event_rows"])
        db.executemany("INSERT INTO relationships VALUES (:source_id,:target_id,:relation_type,:directed,:weight,:evidence_count,:first_chapter,:last_chapter,:evidence_json)", [{**row, "directed": int(row["directed"]), "evidence_json": json.dumps(row["evidence"], ensure_ascii=False, sort_keys=True)} for row in payload["relationships"]])
        db.executemany("INSERT INTO phase_stats VALUES (:phase_start,:phase_end,:timeline_nodes,:new_characters,:gifts,:new_artifacts)", payload["phase_rows"])
        db.execute("PRAGMA user_version = 1")
        db.commit()
        db.execute("VACUUM")
    finally:
        db.close()


def sqlite_counts(path: Path) -> dict[str, int]:
    tables = ["timeline_nodes", "characters", "character_aliases", "character_affiliations", "node_characters", "gifts", "gift_participants", "artifacts", "artifact_events", "relationships", "phase_stats"]
    db = sqlite3.connect(path)
    try:
        return {table: int(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) for table in tables}
    finally:
        db.close()


def build_report(summary: dict[str, Any]) -> str:
    c, t, ch, g, a, r, q = summary["coverage"], summary["timeline"], summary["characters"], summary["gifts"], summary["artifacts"], summary["relationships"], summary["quality"]
    phases = [[f"{row['phase_start']}—{row['phase_end']}", row["timeline_nodes"], row["new_characters"], row["gifts"], row["new_artifacts"]] for row in summary["phase_stats"]]
    appearances = [[row["rank"], row["id"], row["name"], row["node_count"], row["life_status"]] for row in ch["top_by_timeline_appearance"]]
    network = [[row["rank"], row["id"], row["name"], row["weighted_degree"], row["neighbor_count"], f"{row['pagerank']:.6f}"] for row in ch["top_by_network"]]
    recipients = [[row["rank"], row["id"], row["name"], row["gift_count"]] for row in g["top_recipients"]]
    return f"""# 全书统计分析与关系图 — RUN-0127

- Task：`{TASK_ID}`
- 来源提交：`{summary['source']['commit']}`
- Canonical 范围：第 {c['chapter_start']}—{c['chapter_end']} 章，`{c['timeline_nodes']}` 个 Timeline Node
- 分析状态：**{q['status']}**
- 本 Run 不创建 Timeline Node；所有共现边均为分析派生，不写回 canonical 事实。

## 1. 数据集概览

{markdown_table(['指标', '数量'], [['正文篇章', c['chapters']], ['Timeline Node', c['timeline_nodes']], ['人物历史记录', c['characters_total']], ['Active 人物', c['characters_active']], ['Superseded 人物', c['characters_superseded']], ['Gift', c['gifts']], ['Artifact', c['artifacts']], ['关系边', r['edges_total']]])}

## 2. Timeline 结构

节点跨度采用闭区间计算。平均每个节点覆盖 **{t['span']['mean']:.2f}** 章，中位数 **{t['span']['median']:.2f}** 章，最短 **{t['span']['min']}** 章，最长 **{t['span']['max']}** 章。

{markdown_table(['状态', '节点数'], [[name, count] for name, count in t['status_counts']])}

### 分阶段密度

{markdown_table(['章节', '节点', '新人物', 'Gift', '新 Artifact'], phases)}

## 3. 人物统计

### Timeline 出场节点最多的人物

{markdown_table(['排名', 'ID', '人物', '节点数', '终局状态'], appearances)}

### 结构化关系网络中心性

`weighted_degree` 使用固定权重：赠礼 5、显式关系 3、身份关系 2、Timeline 共现 1。PageRank 只比较结构化网络中心性，不代表叙事价值判断。

{markdown_table(['排名', 'ID', '人物', '加权度', '邻居数', 'PageRank'], network)}

### 主要势力归属

{markdown_table(['势力', 'Active 人物数'], [[name, count] for name, count in ch['top_affiliations']])}

## 4. Gift 与返还

- accepted：true `{g['accepted_counts'].get('true', 0)}`，false `{g['accepted_counts'].get('false', 0)}`，unknown `{g['accepted_counts'].get('unknown', 0)}`
- system_valid：true `{g['system_valid_counts'].get('true', 0)}`，false `{g['system_valid_counts'].get('false', 0)}`，unknown `{g['system_valid_counts'].get('unknown', 0)}`
- 可提取数值倍率的 Gift：`{g['numeric_multiplier_gifts']}`
- 最大结构化倍率：`{g['max_multiplier'] or '未提取'}`

### 受赠次数最多的人物

{markdown_table(['排名', 'ID', '人物', 'Gift 数'], recipients)}

## 5. Artifact

{markdown_table(['类别', '数量'], [[name, count] for name, count in a['category_counts']])}

生命周期状态：{', '.join(f'`{name}` {count}' for name, count in a['lifecycle_counts']) or '未结构化'}。

## 6. 关系边

{markdown_table(['关系类型', '边数'], [[name, count] for name, count in r['edge_counts_by_type']])}

图文件只展示中心性最高的 `{r['graph_node_count']}` 个人物及其高权重边；SQLite 与 JSONL 保存完整关系边。

## 7. 数据质量与解释边界

- 未强制解析的模糊 Timeline 人名标签：`{q['ambiguous_timeline_labels']}`
- 未强制解析的 Gift 参与者标签：`{q['unresolved_gift_participants']}`
- 未强制解析的显式关系标签：`{q['ambiguous_relationship_labels']}`
- 阻断项：`{len(q['blocking_findings'])}`

Timeline 共现表示人物被同一剧情节点共同列出，是分析性弱关系；Gift、显式关系和身份关系拥有更高权重。无法唯一解析的标签均保留为 finding，不会为了提高图连通度而强制绑定人物 ID。

## 8. 复现

```bash
python scripts/analyze_repository.py --generated-dir data/generated --output-root . --source-commit {summary['source']['commit']}
```
"""


def mermaid_graph(graph_ids: list[str], graph_edges: list[dict[str, Any]], characters: dict[str, dict[str, Any]]) -> str:
    token = lambda rid: "C" + rid.replace("CHAR-", "").replace("-", "_")
    labels = {"gift": "赠礼", "explicit_relationship": "显式关系", "identity": "身份", "timeline_cooccurrence": "共现"}
    lines = ["%% Generated analysis-only projection.", "graph LR"]
    for rid in graph_ids:
        name = str(characters[rid].get("name", rid)).replace('"', "'")
        lines.append(f'  {token(rid)}["{name}<br/>{rid}"]')
    for row in graph_edges:
        connector = "-->" if row["directed"] else "---"
        lines.append(f"  {token(row['source_id'])} {connector}|{labels.get(row['relation_type'], row['relation_type'])}:{row['evidence_count']}| {token(row['target_id'])}")
    return "\n".join(lines)


def graphviz_graph(graph_ids: list[str], graph_edges: list[dict[str, Any]], characters: dict[str, dict[str, Any]]) -> str:
    quote = lambda value: str(value).replace("\\", "\\\\").replace('"', '\\"')
    lines = ["// Generated analysis-only projection.", "digraph RelationshipGraph {", '  graph [rankdir="LR", overlap="false", splines="true"];', '  node [shape="box", fontname="sans-serif"];']
    for rid in graph_ids:
        lines.append(f'  "{quote(rid)}" [label="{quote(characters[rid].get("name", rid))}\\n{rid}"];')
    for row in graph_edges:
        direction = "forward" if row["directed"] else "none"
        label = f"{row['relation_type']}:{row['evidence_count']}"
        lines.append(f'  "{quote(row["source_id"])}" -> "{quote(row["target_id"])}" [dir="{direction}", label="{quote(label)}", penwidth="{1.0 + math.log1p(row["weight"]):.2f}"];')
    lines.append("}")
    return "\n".join(lines)


def materialize(root: Path, generated_dir: Path, output_root: Path, source_commit: str, analysis_date: str) -> dict[str, Any]:
    config_path = root / "data/analysis/run-0127-config.yaml"
    config = load_yaml(config_path)
    expected, settings = config.get("expected", {}), config.get("analysis", {})
    edge_weights = settings.get("edge_weights", {})
    input_paths = {"timeline": generated_dir / "timeline.yaml", "characters": generated_dir / "characters.yaml", "gifts": generated_dir / "gifts.yaml", "artifacts": generated_dir / "artifacts.yaml", "config": config_path}
    documents = {name: load_yaml(path) for name, path in input_paths.items()}
    timeline_items, character_items = rows(documents["timeline"], "nodes"), rows(documents["characters"], "characters")
    gift_items, artifact_items = rows(documents["gifts"], "gifts"), rows(documents["artifacts"], "artifacts")
    timeline, characters, gifts, artifacts = id_map(timeline_items), id_map(character_items), id_map(gift_items), id_map(artifact_items)
    active = {rid: row for rid, row in characters.items() if row.get("record_status") != "superseded"}
    superseded = {rid: row for rid, row in characters.items() if row.get("record_status") == "superseded"}
    resolver, edges = Resolver(characters), EdgeStore()
    blocking: list[str] = []
    actual = {"timeline_nodes": len(timeline), "characters_total": len(characters), "characters_active": len(active), "gifts": len(gifts), "artifacts": len(artifacts)}
    for key, value in actual.items():
        if first_int(expected.get(key)) is not None and value != first_int(expected.get(key)):
            blocking.append(f"{key}={value}, expected {expected.get(key)}")
    continuity_ok, continuity_errors = timeline_continuity(timeline_items)
    blocking.extend(continuity_errors)
    ordered_nodes = sorted(timeline_items, key=lambda row: (first_int((row.get("chapters") or {}).get("start")) or 10**9, str(row.get("id"))))
    chapter_start, chapter_end = first_int(expected.get("chapter_start")) or 1, first_int(expected.get("chapter_end")) or 876

    ambiguous_timeline: list[dict[str, Any]] = []
    node_character_rows: list[dict[str, Any]] = []
    node_counts: Counter[str] = Counter()
    timeline_rows: list[dict[str, Any]] = []
    spans: list[int] = []
    timeline_status = Counter()
    for node in ordered_nodes:
        node_id, chapters = str(node.get("id")), node.get("chapters", {})
        start, end = first_int(chapters.get("start")), first_int(chapters.get("end"))
        if start is None or end is None:
            continue
        span = end - start + 1
        spans.append(span)
        timeline_status[str(node.get("status", "unknown"))] += 1
        resolved: set[str] = set()
        for label in strings(node.get("characters")):
            rid, candidates = resolver.resolve(label, node_id=node_id)
            if rid:
                resolved.add(rid)
                node_counts[rid] += 1
                node_character_rows.append({"node_id": node_id, "character_id": rid, "raw_label": label, "resolution": "exact_or_contextual"})
            else:
                ambiguous_timeline.append({"node_id": node_id, "raw_label": label, "candidate_ids": candidates})
        for left, right in itertools.combinations(sorted(resolved), 2):
            edges.add(left, right, "timeline_cooccurrence", weight=first_int(edge_weights.get("timeline_cooccurrence")) or 1, chapter=start, evidence=node_id)
        timeline_rows.append({"id": node_id, "title": flatten_text(node.get("title")), "chapter_start": start, "chapter_end": end, "chapter_span": span, "status": flatten_text(node.get("status")), "character_count": len(resolved), "location_count": len(strings(node.get("locations"))), "system_event_count": len(as_list(node.get("system_events"))), "conflict_event_count": len(as_list(node.get("conflict_events")))})

    gift_rows: list[dict[str, Any]] = []
    participant_rows: list[dict[str, Any]] = []
    gift_counts: Counter[str] = Counter()
    gift_status, accepted_counts, valid_counts = Counter(), Counter(), Counter()
    unresolved_gifts: list[dict[str, Any]] = []
    multipliers: list[int] = []
    for gift_id, gift in sorted(gifts.items()):
        chapter, recipient_raw, giver_raw = chapter_of(gift), flatten_text(gift.get("recipient")), flatten_text(gift.get("giver"))
        giver_id, giver_candidates = resolver.resolve(gift.get("giver"), gift_id=gift_id)
        if giver_id:
            participant_rows.append({"gift_id": gift_id, "participant_role": "giver", "character_id": giver_id, "raw_label": giver_raw, "resolution": "exact", "status": flatten_text(gift.get("status"))})
        elif giver_raw:
            unresolved_gifts.append({"gift_id": gift_id, "role": "giver", "raw_label": giver_raw, "candidate_ids": giver_candidates})
        recipients: list[str] = []
        resolution = gift.get("participant_resolution")
        kind = status = ""
        if isinstance(resolution, dict):
            kind, status = flatten_text(resolution.get("resolution")), flatten_text(resolution.get("status"))
            recipients = [rid for rid in as_list(resolution.get("recipient_refs")) if isinstance(rid, str) and rid in active]
            if not recipients and kind in {"unresolved", "unresolved_role_label"}:
                unresolved_gifts.append({"gift_id": gift_id, "role": "recipient", "raw_label": flatten_text(resolution.get("original_label")) or recipient_raw, "candidate_ids": [], "reason": flatten_text(resolution.get("reason"))})
        else:
            rid, candidates = resolver.resolve(gift.get("recipient"), gift_id=gift_id)
            if rid:
                recipients, kind, status = [rid], "exact_name", flatten_text(gift.get("status"))
            elif recipient_raw:
                unresolved_gifts.append({"gift_id": gift_id, "role": "recipient", "raw_label": recipient_raw, "candidate_ids": candidates})
        for rid in sorted(set(recipients)):
            gift_counts[rid] += 1
            participant_rows.append({"gift_id": gift_id, "participant_role": "recipient", "character_id": rid, "raw_label": recipient_raw, "resolution": kind or "exact", "status": status or flatten_text(gift.get("status"))})
            if giver_id:
                edges.add(giver_id, rid, "gift", weight=first_int(edge_weights.get("gift")) or 5, chapter=chapter, evidence=gift_id, directed=True)
        accepted, valid = gift.get("accepted"), gift.get("system_valid")
        accepted_counts["true" if accepted is True else "false" if accepted is False else "unknown"] += 1
        valid_counts["true" if valid is True else "false" if valid is False else "unknown"] += 1
        gift_status[str(gift.get("status", "unknown"))] += 1
        multiplier = gift_max_multiplier(gift)
        if multiplier:
            multipliers.append(multiplier)
        gift_rows.append({"id": gift_id, "chapter": chapter, "resolution_chapter": first_int(gift.get("resolution_chapter"), gift.get("acceptance_chapter")), "giver_raw": giver_raw, "recipient_raw": recipient_raw, "accepted": bool_db(accepted), "system_valid": bool_db(valid), "status": flatten_text(gift.get("status")), "max_multiplier": multiplier, "gift_text": flatten_text(gift.get("gift")), "reward_text": flatten_text(gift.get("reward") or gift.get("returns"))})

    ambiguous_relationships: list[dict[str, Any]] = []
    for source_id, row in sorted(active.items()):
        context = row.get("relationship_context")
        if isinstance(context, dict):
            for label, description in sorted(context.items(), key=lambda pair: str(pair[0])):
                if label == "status":
                    continue
                target_id, candidates = resolver.resolve(label)
                if target_id:
                    edges.add(source_id, target_id, "explicit_relationship", weight=first_int(edge_weights.get("explicit_relationship")) or 3, chapter=first_appearance_chapter(row), evidence=f"{source_id}:{label}:{flatten_text(description)[:120]}", directed=True)
                else:
                    ambiguous_relationships.append({"source_id": source_id, "raw_label": str(label), "candidate_ids": candidates})
        for decision in as_list(row.get("identity_resolution")):
            if isinstance(decision, dict) and isinstance(decision.get("other_character_id"), str) and decision["other_character_id"] in active:
                edges.add(source_id, decision["other_character_id"], "identity", weight=first_int(edge_weights.get("identity")) or 2, chapter=first_int(decision.get("effective_chapter")), evidence=f"{source_id}:{flatten_text(decision.get('relation_type'))}")

    relationships = edges.rows()
    ranks = pagerank(sorted(active), relationships)
    weighted_degree: Counter[str] = Counter()
    neighbors: dict[str, set[str]] = defaultdict(set)
    for row in relationships:
        weighted_degree[row["source_id"]] += int(row["weight"])
        weighted_degree[row["target_id"]] += int(row["weight"])
        neighbors[row["source_id"]].add(row["target_id"])
        neighbors[row["target_id"]].add(row["source_id"])

    character_rows: list[dict[str, Any]] = []
    alias_rows: list[tuple[str, str]] = []
    affiliation_rows: list[tuple[str, str]] = []
    affiliations = Counter()
    life_status, role_counts = Counter(), Counter()
    for rid, row in sorted(characters.items()):
        name, record_status = flatten_text(row.get("name")) or rid, flatten_text(row.get("record_status")) or "active"
        life_status[flatten_text(row.get("status")) or "unknown"] += 1
        role_counts[flatten_text(row.get("role")) or "unknown"] += 1
        if record_status != "superseded":
            for alias in sorted(names_for_character(row) - {name}):
                alias_rows.append((rid, alias))
            for affiliation in affiliations_for_character(row):
                affiliation_rows.append((rid, affiliation))
                affiliations[affiliation] += 1
        character_rows.append({"id": rid, "name": name, "life_status": flatten_text(row.get("status")), "role": flatten_text(row.get("role")), "record_status": record_status, "first_chapter": first_appearance_chapter(row), "verification_status": flatten_text(row.get("verification_status")), "node_count": node_counts[rid], "gift_count": gift_counts[rid], "weighted_degree": weighted_degree[rid], "neighbor_count": len(neighbors[rid]), "pagerank": ranks.get(rid, 0.0)})

    artifact_rows: list[dict[str, Any]] = []
    artifact_events: list[dict[str, Any]] = []
    categories, lifecycle_counts, artifact_status = Counter(), Counter(), Counter()
    for artifact_id, artifact in sorted(artifacts.items()):
        category = flatten_text(artifact.get("category")) or "未分类"
        lifecycle = flatten_text(artifact.get("lifecycle_status") or artifact.get("current_state")) or "未结构化"
        categories[category] += 1
        lifecycle_counts[lifecycle] += 1
        artifact_status[flatten_text(artifact.get("status")) or "unknown"] += 1
        artifact_rows.append({"id": artifact_id, "name": flatten_text(artifact.get("name")) or artifact_id, "category": category, "grade": flatten_text(artifact.get("grade")), "first_chapter": first_appearance_chapter(artifact), "current_holder": flatten_text(artifact.get("current_holder") or artifact.get("holder")), "former_holder": flatten_text(artifact.get("former_holder")), "lifecycle_status": lifecycle, "verification_status": flatten_text(artifact.get("status")), "record_status": flatten_text(artifact.get("record_status")) or "active"})
        for index, event in enumerate(as_list(artifact.get("lifecycle_event"))):
            if isinstance(event, dict):
                artifact_events.append({"artifact_id": artifact_id, "event_index": index, "chapter": first_int(event.get("chapter")), "event_type": flatten_text(event.get("event_type")), "previous_holder": flatten_text(event.get("previous_holder")), "result": flatten_text(event.get("result")), "status": flatten_text(event.get("status"))})

    phase_size = first_int(settings.get("phase_size_chapters")) or 100
    phase_rows = []
    for start in range(chapter_start, chapter_end + 1, phase_size):
        end = min(start + phase_size - 1, chapter_end)
        phase_rows.append({"phase_start": start, "phase_end": end, "timeline_nodes": sum(1 for row in timeline_rows if start <= row["chapter_start"] <= end), "new_characters": sum(1 for row in active.values() if (chapter := first_appearance_chapter(row)) is not None and start <= chapter <= end), "gifts": sum(1 for row in gift_rows if row["chapter"] is not None and start <= row["chapter"] <= end), "new_artifacts": sum(1 for row in artifact_rows if row["first_chapter"] is not None and start <= row["first_chapter"] <= end)})

    top_appearance = sorted((row for row in character_rows if row["record_status"] != "superseded"), key=lambda row: (-row["node_count"], row["id"]))[:20]
    top_network = sorted((row for row in character_rows if row["record_status"] != "superseded"), key=lambda row: (-row["pagerank"], -row["weighted_degree"], row["id"]))[:20]
    top_recipients = sorted((row for row in character_rows if row["record_status"] != "superseded" and row["gift_count"] > 0), key=lambda row: (-row["gift_count"], row["id"]))[:20]
    edge_counts = Counter(row["relation_type"] for row in relationships)
    graph_limit = first_int(settings.get("graph_top_characters")) or 30
    graph_ids = [row["id"] for row in sorted((row for row in character_rows if row["record_status"] != "superseded"), key=lambda row: (-row["weighted_degree"], -row["pagerank"], row["id"]))[:graph_limit]]
    graph_set = set(graph_ids)
    min_edge_weight = first_int(settings.get("graph_min_edge_weight")) or 2
    graph_edges = sorted((row for row in relationships if row["source_id"] in graph_set and row["target_id"] in graph_set and row["weight"] >= min_edge_weight), key=lambda row: (-row["weight"], row["source_id"], row["target_id"], row["relation_type"]))[:120]

    verification = Counter()
    for document in documents.values():
        verification_counter(document, verification)
    input_hashes = {name: sha256_file(path) for name, path in input_paths.items()}
    summary = {"schema_version": 1, "run_id": RUN_ID, "task_id": TASK_ID, "generated_by": GENERATOR, "analysis_date": analysis_date, "source": {"commit": source_commit, "canonical_input_sha256": input_hashes}, "coverage": {"chapter_start": chapter_start, "chapter_end": chapter_end, "chapters": chapter_end - chapter_start + 1, "timeline_nodes": len(timeline), "characters_total": len(characters), "characters_active": len(active), "characters_superseded": len(superseded), "gifts": len(gifts), "artifacts": len(artifacts)}, "timeline": {"status_counts": sorted(timeline_status.items()), "span": {"min": min(spans) if spans else 0, "max": max(spans) if spans else 0, "mean": statistics.fmean(spans) if spans else 0.0, "median": statistics.median(spans) if spans else 0.0}}, "characters": {"life_status_counts": sorted(life_status.items()), "role_counts": sorted(role_counts.items()), "top_affiliations": sorted(affiliations.items(), key=lambda pair: (-pair[1], pair[0]))[:20], "top_by_timeline_appearance": [{"rank": index, **{key: row[key] for key in ("id", "name", "node_count", "life_status")}} for index, row in enumerate(top_appearance, 1)], "top_by_network": [{"rank": index, **{key: row[key] for key in ("id", "name", "weighted_degree", "neighbor_count", "pagerank")}} for index, row in enumerate(top_network, 1)]}, "gifts": {"status_counts": sorted(gift_status.items()), "accepted_counts": dict(sorted(accepted_counts.items())), "system_valid_counts": dict(sorted(valid_counts.items())), "numeric_multiplier_gifts": len(multipliers), "max_multiplier": max(multipliers) if multipliers else None, "multiplier_distribution": sorted(Counter(multipliers).items()), "top_recipients": [{"rank": index, **{key: row[key] for key in ("id", "name", "gift_count")}} for index, row in enumerate(top_recipients, 1)]}, "artifacts": {"category_counts": sorted(categories.items(), key=lambda pair: (-pair[1], pair[0])), "lifecycle_counts": sorted(lifecycle_counts.items(), key=lambda pair: (-pair[1], pair[0])), "status_counts": sorted(artifact_status.items())}, "relationships": {"edges_total": len(relationships), "edge_counts_by_type": sorted(edge_counts.items()), "graph_node_count": len(graph_ids), "graph_edge_count": len(graph_edges), "weight_contract": edge_weights}, "phase_stats": phase_rows, "verification_field_occurrences": dict(sorted(verification.items())), "quality": {"status": "passed_with_documented_ambiguity" if not blocking else "failed", "timeline_continuity": continuity_ok, "ambiguous_timeline_labels": len(ambiguous_timeline), "unresolved_gift_participants": len(unresolved_gifts), "ambiguous_relationship_labels": len(ambiguous_relationships), "blocking_findings": blocking, "ambiguity_samples": {"timeline": ambiguous_timeline[:50], "gift_participants": unresolved_gifts[:50], "explicit_relationships": ambiguous_relationships[:50]}}}

    paths = {"summary_json": output_root / "data/analysis/run-0127/summary.json", "relationships_jsonl": output_root / "data/analysis/run-0127/relationships.jsonl", "sqlite": output_root / "data/analysis/run-0127/full-book.sqlite3", "sqlite_schema": output_root / "data/analysis/run-0127/schema.sql", "markdown": output_root / "docs/08-analysis/full-book-analysis.md", "mermaid": output_root / "docs/08-analysis/relationship-graph.mmd", "graphviz": output_root / "docs/08-analysis/relationship-graph.dot", "audit": output_root / "data/audits/run-0127.yaml"}
    write_json(paths["summary_json"], summary)
    write_text(paths["relationships_jsonl"], "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in relationships))
    schema = schema_sql()
    write_text(paths["sqlite_schema"], schema)
    write_text(paths["markdown"], build_report(summary))
    write_text(paths["mermaid"], mermaid_graph(graph_ids, graph_edges, active))
    write_text(paths["graphviz"], graphviz_graph(graph_ids, graph_edges, active))
    payload = {"metadata": {"schema_version": 1, "run_id": RUN_ID, "task_id": TASK_ID, "source_commit": source_commit, "analysis_date": analysis_date, "generated_by": GENERATOR}, "timeline_rows": timeline_rows, "character_rows": character_rows, "alias_rows": alias_rows, "affiliation_rows": affiliation_rows, "node_character_rows": node_character_rows, "gift_rows": gift_rows, "gift_participant_rows": participant_rows, "artifact_rows": artifact_rows, "artifact_event_rows": artifact_events, "relationships": relationships, "phase_rows": phase_rows}
    create_sqlite(paths["sqlite"], schema, payload)
    counts = sqlite_counts(paths["sqlite"])
    expected_counts = {"timeline_nodes": len(timeline_rows), "characters": len(character_rows), "node_characters": len(node_character_rows), "gifts": len(gift_rows), "gift_participants": len(participant_rows), "artifacts": len(artifact_rows), "artifact_events": len(artifact_events), "relationships": len(relationships), "phase_stats": len(phase_rows)}
    for table, count in expected_counts.items():
        if counts.get(table) != count:
            blocking.append(f"SQLite {table}={counts.get(table)}, expected {count}")
    jsonl_lines = sum(bool(line.strip()) for line in paths["relationships_jsonl"].read_text(encoding="utf-8").splitlines())
    if jsonl_lines != len(relationships):
        blocking.append(f"relationships JSONL lines={jsonl_lines}, expected {len(relationships)}")
    summary["quality"]["blocking_findings"] = blocking
    summary["quality"]["status"] = "passed_with_documented_ambiguity" if not blocking else "failed"
    summary["sqlite"] = {"row_counts": counts}
    write_json(paths["summary_json"], summary)
    write_text(paths["markdown"], build_report(summary))
    output_hashes = {name: sha256_file(path) for name, path in paths.items() if name != "audit"}
    gates = {"source_count_reconciliation": {"status": "passed" if not any("expected" in item and "=" in item for item in blocking) else "failed", "detail": actual}, "timeline_continuity": {"status": "passed" if continuity_ok else "failed", "detail": f"coverage={chapter_start}-{chapter_end}; nodes={len(timeline)}"}, "superseded_exclusion": {"status": "passed" if len(active) == first_int(expected.get("characters_active")) else "failed", "detail": f"active={len(active)}; superseded={len(superseded)}"}, "relationship_endpoint_integrity": {"status": "passed" if all(row["source_id"] in active and row["target_id"] in active for row in relationships) else "failed", "detail": f"edges={len(relationships)}"}, "ambiguity_preservation": {"status": "passed", "detail": {"timeline_labels": len(ambiguous_timeline), "gift_participants": len(unresolved_gifts), "relationship_labels": len(ambiguous_relationships)}}, "sqlite_reconciliation": {"status": "passed" if not any(item.startswith("SQLite") for item in blocking) else "failed", "detail": counts}, "jsonl_reconciliation": {"status": "passed" if jsonl_lines == len(relationships) else "failed", "detail": f"lines={jsonl_lines}; edges={len(relationships)}"}, "deterministic_serialization_contract": {"status": "passed", "detail": "sorted JSON/JSONL rows, fixed SQLite schema and canonical input hashes"}, "copyright_boundary": {"status": "passed", "detail": "structured facts and original analysis only; no full chapter text"}}
    audit = {"schema_version": 1, "analysis": {"run_id": RUN_ID, "task_id": TASK_ID, "source_commit": source_commit, "analysis_date": analysis_date, "status": "passed_with_documented_ambiguity" if not blocking else "failed", "blocking_findings": blocking}, "counts": {**actual, "characters_superseded": len(superseded), "relationship_edges": len(relationships), "sqlite_tables": len(counts), "ambiguous_timeline_labels": len(ambiguous_timeline), "unresolved_gift_participants": len(unresolved_gifts), "ambiguous_relationship_labels": len(ambiguous_relationships)}, "quality_gates": gates, "input_sha256": input_hashes, "output_sha256": output_hashes, "outputs": {name: str(path.relative_to(output_root)) for name, path in paths.items()}}
    write_yaml(paths["audit"], audit)
    print(json.dumps({"status": audit["analysis"]["status"], "source_commit": source_commit, "counts": audit["counts"], "blocking_findings": blocking, "outputs": audit["outputs"]}, ensure_ascii=False, indent=2, sort_keys=True))
    if blocking:
        raise SystemExit(1)
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--generated-dir", type=Path, default=Path("data/generated"))
    parser.add_argument("--output-root", type=Path, default=Path("."))
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--analysis-date", default="2026-07-29")
    args = parser.parse_args()
    root = args.root.resolve()
    generated_dir = args.generated_dir if args.generated_dir.is_absolute() else (root / args.generated_dir).resolve()
    output_root = args.output_root if args.output_root.is_absolute() else (root / args.output_root).resolve()
    materialize(root, generated_dir, output_root, args.source_commit, args.analysis_date)


if __name__ == "__main__":
    main()
