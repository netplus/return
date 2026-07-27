#!/usr/bin/env python3
"""Unit tests for canonical character identity alignment."""
from __future__ import annotations

import validate_entity_identity as validator


def test_accepts_matching_name_and_profile() -> None:
    index = {
        "characters": [
            {
                "id": "CHAR-0001",
                "name": "徐霄",
                "documents": {"profile": "docs/02-characters/徐霄.md"},
            },
            {"id": "CHAR-0002", "name": "新人物", "document": None},
        ]
    }
    assert validator.validate(index) == []


def test_rejects_mismatched_name_and_profile() -> None:
    index = {
        "characters": [
            {
                "id": "CHAR-0005",
                "name": "段红绫",
                "documents": {"profile": "docs/02-characters/紫韵.md"},
            }
        ]
    }
    errors = validator.validate(index)
    assert len(errors) == 1
    assert "CHAR-0005" in errors[0]
    assert "紫韵" in errors[0]


def test_rejects_missing_name() -> None:
    errors = validator.validate({"characters": [{"id": "CHAR-0001"}]})
    assert errors == ["missing canonical name: CHAR-0001"]


def main() -> int:
    test_accepts_matching_name_and_profile()
    test_rejects_mismatched_name_and_profile()
    test_rejects_missing_name()
    print("character identity alignment tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
