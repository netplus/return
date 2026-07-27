#!/usr/bin/env python3
"""Validate canonical character identity against explicit profile paths."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise RuntimeError(f"cannot read YAML {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"top-level YAML must be a mapping: {path}")
    return value


def explicit_profile(record: dict[str, Any]) -> str | None:
    documents = record.get("documents")
    candidate = documents.get("profile") if isinstance(documents, dict) else None
    if candidate is None:
        candidate = record.get("document")
    if not isinstance(candidate, str) or not candidate.endswith(".md"):
        return None
    return candidate


def validate(index: dict[str, Any]) -> list[str]:
    records = index.get("characters")
    if not isinstance(records, list):
        return ["characters index must contain a list named characters"]

    errors: list[str] = []
    for record in records:
        if not isinstance(record, dict):
            errors.append("character record must be a mapping")
            continue
        rid = str(record.get("id") or "UNKNOWN")
        name = record.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"missing canonical name: {rid}")
            continue
        profile = explicit_profile(record)
        if profile is None:
            continue
        stem = Path(profile).stem
        if stem != name:
            errors.append(
                f"character identity mismatch: {rid} name={name!r}, profile_stem={stem!r}, path={profile}"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-dir", type=Path, default=Path("data/generated"))
    args = parser.parse_args()
    try:
        index = load_yaml(args.generated_dir / "characters.yaml")
        errors = validate(index)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        count = len(index.get("characters", []))
        print(f"character identity alignment passed: {count} records")
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
