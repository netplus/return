#!/usr/bin/env python3
"""Unit tests for the reader-friendly canonical entity-document renderer."""
from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

import render_entity_docs as renderer


def write_yaml(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def test_render_and_check() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        generated = root / "data/generated"
        output = root / "output"
        write_yaml(
            generated / "characters.yaml",
            {
                "updated_at": "2026-07-27",
                "characters": [
                    {
                        "id": "CHAR-0001",
                        "name": "徐霄",
                        "status": "alive",
                        "role": "protagonist",
                        "documents": {"profile": "docs/02-characters/徐霄.md"},
                        "cultivation": {"current": "合体境", "status": "partial"},
                        "cultivation_change": "大乘境",
                        "affiliations": ["无妄仙宗", "灵霄仙宗"],
                        "identities": ["内门大师兄", "荣誉太上长老"],
                        "relationship_change": ["与玉冰结为公开道侣"],
                        "combat_record": ["击杀萧彭春"],
                        "pending_fields": ["完整系统面板"],
                        "source_chapters": [1, 2, 3, 5, 493],
                        "related_nodes": ["NODE-0001", "NODE-0064"],
                        "unmapped_note": "应出现在补充信息",
                    },
                    {"id": "CHAR-0002", "name": "A/B", "status": "partial"},
                    {"id": "CHAR-0003", "name": "A:B", "status": "pending"},
                ],
            },
        )
        write_yaml(
            generated / "artifacts.yaml",
            {
                "updated_at": "2026-07-27",
                "artifacts": [
                    {
                        "id": "ART-0001",
                        "name": "山河灵图",
                        "category": "仙器",
                        "grade": "仙器",
                        "status": "partial",
                        "first_chapter": 424,
                        "current_holder": "徐霄",
                        "abilities": ["内含山河小世界", "可收纳活体目标"],
                        "combat_record": ["收纳东海龙族千人军团"],
                        "continuity_warning": "完整空间规则待确认",
                        "source_chapters": [424, 435, 436],
                    }
                ],
            },
        )

        outputs, manifest = renderer.expected_files(root, output, generated)
        renderer.write(outputs, set())
        assert manifest["schema_version"] == 2
        assert manifest["presentation"] == "reader_friendly_with_collapsed_canonical_appendix"
        assert manifest["groups"]["characters"]["count"] == 3
        assert manifest["groups"]["artifacts"]["count"] == 1
        assert (output / "docs/02-characters/A＿B.md").exists()
        assert (output / "docs/02-characters/A＿B-CHAR-0003.md").exists()
        assert renderer.compare(outputs) == []

        character = (output / "docs/02-characters/徐霄.md").read_text(encoding="utf-8")
        assert "## 一览" in character
        assert "| 当前境界 | 大乘境 |" in character
        assert "## 身份与阵营" in character
        assert "## 修为、能力与成长" in character
        assert "## 关系与立场" in character
        assert "## 关键经历" in character
        assert "## 补充信息" in character
        assert "## 未决与注意事项" in character
        assert "<summary>结构化数据附录（供维护与审计）</summary>" in character
        assert "## 完整 Canonical 记录" not in character
        assert "`current: 合体境 status: partial`" not in character
        assert "1—3、5、493" in character

        artifact = (output / "docs/06-artifacts/山河灵图.md").read_text(encoding="utf-8")
        assert "## 获取、持有与流转" in artifact
        assert "## 能力与效果" in artifact
        assert "## 使用与战斗记录" in artifact
        assert "完整空间规则待确认" in artifact

        profile = output / "docs/02-characters/徐霄.md"
        profile.write_text("stale\n", encoding="utf-8")
        errors = renderer.compare(outputs)
        assert any("stale generated entity document" in item for item in errors)
        renderer.write(outputs, renderer.prior_managed_paths(output))
        assert renderer.compare(outputs) == []


def test_removes_only_previously_managed_files() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        generated = root / "data/generated"
        output = root / "output"
        write_yaml(
            generated / "characters.yaml",
            {"characters": [{"id": "CHAR-0001", "name": "甲", "status": "alive"}]},
        )
        write_yaml(generated / "artifacts.yaml", {"artifacts": []})
        outputs, _manifest = renderer.expected_files(root, output, generated)
        renderer.write(outputs, set())

        managed = output / "docs/02-characters/甲.md"
        unmanaged = output / "docs/02-characters/人工备注.md"
        unmanaged.write_text("keep\n", encoding="utf-8")
        assert managed.exists()

        write_yaml(generated / "characters.yaml", {"characters": []})
        next_outputs, _manifest = renderer.expected_files(root, output, generated)
        renderer.write(next_outputs, renderer.prior_managed_paths(output))

        assert not managed.exists()
        assert unmanaged.exists()


def main() -> int:
    test_render_and_check()
    test_removes_only_previously_managed_files()
    print("entity-document renderer tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
