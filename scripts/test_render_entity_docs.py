#!/usr/bin/env python3
"""Unit tests for the canonical entity-document renderer."""

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
                        "documents": {"profile": "docs/02-characters/徐霄.md"},
                        "cultivation": {"current": "大乘境"},
                        "source_chapters": [1, 493],
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
                        "name": "寿元丹",
                        "category": "丹药",
                        "status": "verified",
                        "first_chapter": 1,
                    }
                ],
            },
        )

        outputs, manifest = renderer.expected_files(root, output, generated)
        renderer.write(outputs, set())

        assert manifest["groups"]["characters"]["count"] == 3
        assert manifest["groups"]["artifacts"]["count"] == 1
        assert (output / "docs/02-characters/徐霄.md").exists()
        assert (output / "docs/06-artifacts/寿元丹.md").exists()
        assert (output / "docs/02-characters/A＿B.md").exists()
        assert (output / "docs/02-characters/A＿B-CHAR-0003.md").exists()
        assert renderer.compare(outputs) == []

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
