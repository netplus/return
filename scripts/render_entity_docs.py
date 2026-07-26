#!/usr/bin/env python3
"""Render complete character and artifact Markdown profiles from canonical indexes."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

MANIFEST_PATH = Path("docs/entity-docs-manifest.yaml")
INDEX_FILES = {
    "characters": ("characters.yaml", "characters", Path("docs/02-characters")),
    "artifacts": ("artifacts.yaml", "artifacts", Path("docs/06-artifacts")),
}
INVALID_FILENAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise RuntimeError(f"cannot read YAML {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"top-level YAML must be a mapping: {path}")
    return value


def dump_yaml(value: Any) -> str:
    return yaml.safe_dump(
        value,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    ).rstrip()


def safe_filename(name: str, record_id: str) -> str:
    cleaned = INVALID_FILENAME_RE.sub("＿", name).strip().rstrip(".")
    if not cleaned:
        cleaned = record_id
    return f"{cleaned}.md"


def explicit_document_path(record: dict[str, Any], group: str) -> str | None:
    candidate: Any = None
    if group == "characters":
        documents = record.get("documents")
        if isinstance(documents, dict):
            candidate = documents.get("profile")
        if candidate is None:
            candidate = record.get("document")
    else:
        candidate = record.get("document")

    if not isinstance(candidate, str) or not candidate.endswith(".md"):
        return None
    normalized = Path(candidate)
    expected_root = INDEX_FILES[group][2]
    try:
        normalized.relative_to(expected_root)
    except ValueError:
        return None
    return normalized.as_posix()


def choose_paths(records: list[dict[str, Any]], group: str) -> dict[str, str]:
    used: dict[str, str] = {}
    result: dict[str, str] = {}
    root = INDEX_FILES[group][2]
    for record in records:
        rid = str(record.get("id") or "")
        name = str(record.get("name") or rid)
        candidate = explicit_document_path(record, group)
        if candidate is None:
            candidate = (root / safe_filename(name, rid)).as_posix()
        key = candidate.casefold()
        if key in used and used[key] != rid:
            candidate = (root / f"{Path(candidate).stem}-{rid}.md").as_posix()
            key = candidate.casefold()
        used[key] = rid
        result[rid] = candidate
    return result


def scalar(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value)
    return f"`{dump_yaml(value).replace(chr(10), ' ')}`"


def summarize_sources(record: dict[str, Any]) -> str:
    chapters = record.get("source_chapters")
    if not isinstance(chapters, list):
        return "—"
    numbers = [item for item in chapters if isinstance(item, int)]
    if not numbers:
        return f"{len(chapters)} 项"
    return f"{len(numbers)} 章（{min(numbers)}—{max(numbers)}）"


def render_profile(record: dict[str, Any], group: str, source_updated_at: str) -> str:
    rid = str(record.get("id") or "UNKNOWN")
    name = str(record.get("name") or rid)
    lines = [
        f"# {name}",
        "",
        "<!-- AUTO-GENERATED FROM CANONICAL INDEX. DO NOT EDIT BY HAND. -->",
        "",
        "## Canonical 摘要",
        "",
        "| 字段 | 内容 |",
        "|---|---|",
        f"| ID | `{rid}` |",
    ]
    if group == "characters":
        summary_fields = [
            ("状态", record.get("status")),
            ("角色", record.get("role")),
            ("当前境界", record.get("cultivation")),
            ("年龄", record.get("age")),
            ("剩余寿命", record.get("lifespan")),
            ("所属势力", record.get("affiliations")),
            ("身份", record.get("identities")),
            ("核验状态", record.get("verification_status", record.get("status"))),
        ]
    else:
        summary_fields = [
            ("类别", record.get("category")),
            ("品阶", record.get("grade")),
            ("首次出现章节", record.get("first_chapter")),
            ("当前持有人", record.get("current_holder", record.get("holder"))),
            ("最终使用者", record.get("final_user")),
            ("当前状态", record.get("current_state")),
            ("核验状态", record.get("status")),
        ]

    for label, value in summary_fields:
        if value is not None:
            lines.append(f"| {label} | {scalar(value).replace('|', r'\|')} |")
    related_nodes = record.get("related_nodes")
    lines.extend(
        [
            f"| 关联节点数 | {len(related_nodes) if isinstance(related_nodes, list) else '—'} |",
            f"| 来源章节 | {summarize_sources(record)} |",
            f"| Canonical 索引更新时间 | {source_updated_at or '—'} |",
            "",
            "## 完整 Canonical 记录",
            "",
            "以下内容是当前基础索引与全部追加扩展合并后的完整记录；`pending`、`partial`、冲突说明和连续性警告均原样保留。",
            "",
            "```yaml",
            dump_yaml(record),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def render_index(records: list[dict[str, Any]], paths: dict[str, str], group: str) -> str:
    title = "人物档案索引" if group == "characters" else "物品档案索引"
    lines = [
        f"# {title}",
        "",
        "<!-- AUTO-GENERATED FROM CANONICAL INDEX. DO NOT EDIT BY HAND. -->",
        "",
        f"- Canonical 记录数：**{len(records)}**",
        "- 每个条目均包含可读摘要及完整 canonical YAML 记录。",
        "- 文档由 `scripts/render_entity_docs.py` 自动生成；应修改基础索引或追加扩展，而不是直接编辑生成文件。",
        "",
        "| ID | 名称 | 状态 | 文档 |",
        "|---|---|---|---|",
    ]
    root = INDEX_FILES[group][2]
    for record in records:
        rid = str(record.get("id") or "")
        name = str(record.get("name") or rid).replace("|", r"\|")
        status = scalar(record.get("verification_status", record.get("status"))).replace("|", r"\|")
        rel = Path(paths[rid]).relative_to(root).as_posix()
        lines.append(f"| `{rid}` | {name} | {status} | [{Path(rel).stem}]({rel}) |")
    lines.append("")
    return "\n".join(lines)


def expected_files(
    repo_root: Path,
    output_root: Path,
    generated_dir: Path,
) -> tuple[dict[Path, str], dict[str, Any]]:
    outputs: dict[Path, str] = {}
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "generator": "scripts/render_entity_docs.py",
        "source": generated_dir.relative_to(repo_root).as_posix()
        if generated_dir.is_relative_to(repo_root)
        else generated_dir.as_posix(),
        "groups": {},
    }
    for group, (filename, key, target_root) in INDEX_FILES.items():
        index = load_yaml(generated_dir / filename)
        records = index.get(key)
        if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
            raise RuntimeError(f"{generated_dir / filename}:{key} must be a list of mappings")
        records = sorted(records, key=lambda item: str(item.get("id") or ""))
        paths = choose_paths(records, group)
        source_updated_at = str(index.get("updated_at") or "")
        for record in records:
            rid = str(record.get("id") or "")
            outputs[output_root / paths[rid]] = render_profile(record, group, source_updated_at)
        outputs[output_root / target_root / "_INDEX.md"] = render_index(records, paths, group)
        index_path = generated_dir / filename
        manifest["groups"][group] = {
            "count": len(records),
            "index": index_path.relative_to(repo_root).as_posix()
            if index_path.is_relative_to(repo_root)
            else index_path.as_posix(),
            "index_document": (target_root / "_INDEX.md").as_posix(),
            "documents": [
                {"id": str(item.get("id") or ""), "path": paths[str(item.get("id") or "")]}
                for item in records
            ],
        }

    outputs[output_root / MANIFEST_PATH] = dump_yaml(manifest) + "\n"
    return outputs, manifest


def prior_managed_paths(output_root: Path) -> set[Path]:
    path = output_root / MANIFEST_PATH
    if not path.exists():
        return set()
    manifest = load_yaml(path)
    managed: set[Path] = {path}
    groups = manifest.get("groups")
    if not isinstance(groups, dict):
        return managed
    for group in groups.values():
        if not isinstance(group, dict):
            continue
        index_document = group.get("index_document")
        if isinstance(index_document, str):
            managed.add(output_root / index_document)
        documents = group.get("documents")
        if isinstance(documents, list):
            for item in documents:
                if isinstance(item, dict) and isinstance(item.get("path"), str):
                    managed.add(output_root / item["path"])
    return managed


def compare(outputs: dict[Path, str]) -> list[str]:
    errors: list[str] = []
    for path, expected in sorted(outputs.items()):
        if not path.exists():
            errors.append(f"missing generated entity document: {path}")
            continue
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            errors.append(f"stale generated entity document: {path}")
    return errors


def write(outputs: dict[Path, str], previous: set[Path]) -> None:
    expected = set(outputs)
    for stale in sorted(previous - expected):
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
    generated_dir = args.generated_dir
    if not generated_dir.is_absolute():
        generated_dir = root / generated_dir
    output_root = args.output_root
    if not output_root.is_absolute():
        output_root = root / output_root

    try:
        outputs, manifest = expected_files(root, output_root, generated_dir)
        if args.check:
            errors = compare(outputs)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print(
                "entity documents are current: "
                f"{manifest['groups']['characters']['count']} characters, "
                f"{manifest['groups']['artifacts']['count']} artifacts"
            )
            return 0

        write(outputs, prior_managed_paths(output_root))
        print(
            "rendered entity documents: "
            f"{manifest['groups']['characters']['count']} characters, "
            f"{manifest['groups']['artifacts']['count']} artifacts"
        )
    except (OSError, RuntimeError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
