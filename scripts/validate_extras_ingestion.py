#!/usr/bin/env python3
"""Validate RUN-0129 authorized extras source registration and isolated nodes."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "sources/extras/fanqienovel-7423641263695481880/manifest.yaml"
RUN_PATH = ROOT / "data/extras/run-0129.yaml"
AUDIT_PATH = ROOT / "data/audits/run-0129.yaml"
CHARACTERS_PATH = ROOT / "data/generated/characters.yaml"

EXPECTED_NODES = {
    "EXTRA-NODE-0001": (877, "7536463745459946046", "番外一，林嫣儿篇"),
    "EXTRA-NODE-0002": (878, "7538798715943780889", "番外二，凤溪篇"),
}
PROHIBITED_KEYS = {"full_text", "raw_text", "source_text", "chapter_text", "verbatim_text"}


def load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"expected mapping: {path}")
    return data


def walk(value: Any, path: str = "root") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in PROHIBITED_KEYS:
                errors.append(f"prohibited full-text field at {path}.{key}")
            errors.extend(walk(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(walk(child, f"{path}[{index}]"))
    return errors


def main() -> int:
    source = load(SOURCE_PATH)
    run = load(RUN_PATH)
    audit = load(AUDIT_PATH)
    characters_doc = load(CHARACTERS_PATH)
    character_ids = {
        row.get("id") for row in characters_doc.get("characters", []) if isinstance(row, dict)
    }
    errors: list[str] = []

    if source.get("source_id") != "EXTRA-SRC-0001":
        errors.append("source_id must be EXTRA-SRC-0001")
    work = source.get("work", {})
    if work.get("official_work_id") != "7423641263695481880":
        errors.append("official work ID mismatch")
    if work.get("catalog_entry_count") != 878 or work.get("main_story_chapter_count") != 876:
        errors.append("official catalog count must reconcile as 876 main + 2 extras")
    if source.get("copyright_boundary", {}).get("full_chapter_text_stored") is not False:
        errors.append("source manifest must prohibit full chapter text storage")

    chapters = source.get("chapters", [])
    chapter_map = {row.get("official_reader_id"): row for row in chapters if isinstance(row, dict)}
    if set(chapter_map) != {item[1] for item in EXPECTED_NODES.values()}:
        errors.append("official reader IDs do not exactly cover both extras")

    if run.get("scope") != "extras" or run.get("creates_main_timeline_node") is not False:
        errors.append("RUN-0129 must remain isolated from the main Timeline")
    if run.get("source_ref") != "EXTRA-SRC-0001":
        errors.append("RUN-0129 source_ref mismatch")
    nodes = run.get("nodes", [])
    node_map = {row.get("id"): row for row in nodes if isinstance(row, dict)}
    if set(node_map) != set(EXPECTED_NODES):
        errors.append("RUN-0129 must contain exactly EXTRA-NODE-0001 and EXTRA-NODE-0002")

    for node_id, (sequence, reader_id, title) in EXPECTED_NODES.items():
        row = node_map.get(node_id, {})
        if row.get("source_chapter_sequence") != sequence:
            errors.append(f"{node_id} source sequence mismatch")
        if row.get("official_reader_id") != reader_id or row.get("title") != title:
            errors.append(f"{node_id} official identity mismatch")
        if row.get("verification") != "partial":
            errors.append(f"{node_id} must remain partial until official full-content verification")
        summary = row.get("summary")
        if not isinstance(summary, str) or not summary.strip() or len(summary) > 240:
            errors.append(f"{node_id} summary missing or too long")
        facts = row.get("key_facts", [])
        if not isinstance(facts, list) or not facts or any(not isinstance(x, str) or len(x) > 140 for x in facts):
            errors.append(f"{node_id} key_facts invalid or too long")
        refs = row.get("main_story_character_refs", [])
        if not isinstance(refs, list) or any(ref not in character_ids for ref in refs):
            errors.append(f"{node_id} references unknown main-story Character ID")
        if not row.get("unresolved"):
            errors.append(f"{node_id} must preserve official-content verification debt")

    isolation = run.get("main_story_isolation", {})
    if isolation.get("main_story_chapter_range") != [1, 876]:
        errors.append("main-story chapter range changed")
    if isolation.get("main_story_last_node") != "NODE-0108":
        errors.append("main-story terminal node changed")
    if isolation.get("included_in_main_timeline") is not False:
        errors.append("extras cannot enter the main Timeline")
    if isolation.get("canonical_mutations") != []:
        errors.append("RUN-0129 must not mutate canonical main-story records")

    errors.extend(walk(source, "source"))
    errors.extend(walk(run, "run"))

    counts = audit.get("counts", {})
    if counts.get("registered_sources") != 1 or counts.get("extra_nodes") != 2:
        errors.append("RUN-0129 audit counts do not reconcile")
    gates = audit.get("quality_gates", {})
    if any(value.get("status") not in {"passed", "passed_with_qualification"}
           for value in gates.values() if isinstance(value, dict)):
        errors.append("RUN-0129 audit contains a failed quality gate")

    if errors:
        print("RUN-0129 extras validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("RUN-0129 extras validation passed: 1 authorized source, 2 isolated partial nodes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
