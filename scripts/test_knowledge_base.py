#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import yaml

from knowledge_base import build, compact, load


class KnowledgeBaseCompactionTests(unittest.TestCase):
    def test_compaction_is_idempotent_and_skips_compacted_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_base_indexes(root)
            self._write_yaml(
                root / "data/extensions/characters/run-0001.yaml",
                {
                    "run_id": "RUN-0001",
                    "characters": [
                        {
                            "id": "CHAR-0001",
                            "name": "徐霄",
                            "related_nodes": ["NODE-0001"],
                        }
                    ],
                },
            )

            before = build(root)
            self.assertEqual(len(before["characters"]["characters"]), 1)
            self.assertEqual(compact(root), "RUN-0001")

            compacted_base = load(root / "data/characters/characters.yaml")
            self.assertEqual(compacted_base["compacted_through_run"], "RUN-0001")
            self.assertEqual(len(compacted_base["characters"]), 1)

            after = build(root)
            self.assertEqual(
                before["characters"]["characters"],
                after["characters"]["characters"],
            )
            self.assertEqual(
                after["characters"]["materialized_from"]["extension_files"],
                0,
            )
            self.assertEqual(
                after["characters"]["materialized_from"]["compacted_through_run"],
                "RUN-0001",
            )

            # Re-running compaction must not change the resolved records.
            self.assertEqual(compact(root), "RUN-0001")
            repeated = build(root)
            self.assertEqual(
                after["characters"]["characters"],
                repeated["characters"]["characters"],
            )

    def test_newer_extensions_apply_after_watermark(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_base_indexes(root)
            self._write_yaml(
                root / "data/extensions/characters/run-0001.yaml",
                {
                    "run_id": "RUN-0001",
                    "characters": [{"id": "CHAR-0001", "name": "徐霄"}],
                },
            )
            compact(root)
            self._write_yaml(
                root / "data/extensions/characters/run-0002.yaml",
                {
                    "run_id": "RUN-0002",
                    "characters": [
                        {
                            "id": "CHAR-0001",
                            "update": {"related_nodes_add": "NODE-0001"},
                        }
                    ],
                },
            )

            materialized = build(root)["characters"]
            character = materialized["characters"][0]
            self.assertEqual(character["related_nodes"], "NODE-0001")
            self.assertEqual(materialized["materialized_from"]["extension_files"], 1)

    def test_invalid_watermark_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_base_indexes(root)
            characters = load(root / "data/characters/characters.yaml")
            characters["compacted_through_run"] = "RUN-latest"
            self._write_yaml(root / "data/characters/characters.yaml", characters)
            with self.assertRaisesRegex(RuntimeError, "invalid compacted_through_run"):
                build(root)

    def _write_base_indexes(self, root: Path) -> None:
        self._write_yaml(
            root / "data/timeline/nodes.yaml",
            {
                "schema_version": 2,
                "nodes": [
                    {
                        "id": "NODE-0001",
                        "chapters": {"start": 1, "end": 1},
                    }
                ],
            },
        )
        self._write_yaml(
            root / "data/characters/characters.yaml",
            {"schema_version": 2, "characters": []},
        )
        self._write_yaml(
            root / "data/system/gifts.yaml",
            {"schema_version": 2, "gifts": []},
        )
        self._write_yaml(
            root / "data/artifacts/artifacts.yaml",
            {"schema_version": 2, "artifacts": []},
        )
        (root / "data/extensions").mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _write_yaml(path: Path, value: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(value, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
