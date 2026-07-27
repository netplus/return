#!/usr/bin/env python3
"""Download a supplied novel source transiently and emit auditable metadata.

The repository stores only source manifests, per-chapter hashes, titles and
location metadata. Requested full chapter text is written exclusively to an
artifact directory for temporary evidence review and is not committed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


CHAPTER_RE = re.compile(
    r"(?m)^[\t \u3000]*第[\t \u3000]*(\d+)[\t \u3000]*章[\t \u3000]*(.*?)[\t \u3000]*$"
)


@dataclass(frozen=True)
class Chapter:
    number: int
    title: str
    start_char: int
    end_char: int
    start_line: int
    end_line: int
    text: str

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def download(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 Project-OS source verifier/1.0",
            "Accept": "text/plain,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def decode_source(raw: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError("source is not valid UTF-8, UTF-8-SIG, or GB18030")


def parse_chapters(text: str) -> list[Chapter]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    matches = list(CHAPTER_RE.finditer(normalized))
    if not matches:
        raise ValueError("no chapter headings matched expected 第N章 format")

    chapters: list[Chapter] = []
    for index, match in enumerate(matches):
        number = int(match.group(1))
        title = match.group(2).strip()
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        chapter_text = normalized[start:end].rstrip() + "\n"
        start_line = normalized.count("\n", 0, start) + 1
        end_line = start_line + chapter_text.count("\n") - 1
        chapters.append(
            Chapter(
                number=number,
                title=title,
                start_char=start,
                end_char=end,
                start_line=start_line,
                end_line=end_line,
                text=chapter_text,
            )
        )

    numbers = [chapter.number for chapter in chapters]
    duplicates = sorted({number for number in numbers if numbers.count(number) > 1})
    if duplicates:
        raise ValueError(f"duplicate chapter numbers: {duplicates}")
    if numbers != sorted(numbers):
        raise ValueError("chapter numbers are not monotonically increasing")
    return chapters


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def write_manifest(
    output_root: Path,
    source_id: str,
    url: str,
    raw: bytes,
    encoding: str,
    chapters: list[Chapter],
    chunk_size: int,
) -> None:
    root = output_root / source_id
    root.mkdir(parents=True, exist_ok=True)
    first = chapters[0].number
    last = chapters[-1].number
    manifest = [
        "schema_version: 1",
        f"source_id: {source_id}",
        f"source_url: {yaml_quote(url)}",
        "storage_policy: metadata_only_no_full_chapter_text",
        f"download_sha256: {sha256_bytes(raw)}",
        f"download_bytes: {len(raw)}",
        f"decoded_encoding: {encoding}",
        f"chapter_count: {len(chapters)}",
        f"chapter_first: {first}",
        f"chapter_last: {last}",
        f"chapter_chunk_size: {chunk_size}",
        "chapter_index_files:",
    ]

    chunk_files: list[str] = []
    for chunk_start in range(((first - 1) // chunk_size) * chunk_size + 1, last + 1, chunk_size):
        chunk_end = chunk_start + chunk_size - 1
        selected = [chapter for chapter in chapters if chunk_start <= chapter.number <= chunk_end]
        if not selected:
            continue
        filename = f"chapters-{chunk_start:04d}-{chunk_end:04d}.yaml"
        chunk_files.append(filename)
        lines = [
            "schema_version: 1",
            f"source_id: {source_id}",
            f"chapter_range: {{start: {chunk_start}, end: {chunk_end}}}",
            f"records_present: {len(selected)}",
            "chapters:",
        ]
        for chapter in selected:
            lines.extend(
                [
                    f"  - chapter: {chapter.number}",
                    f"    title: {yaml_quote(chapter.title)}",
                    f"    sha256: {chapter.sha256}",
                    f"    source_line_range: {{start: {chapter.start_line}, end: {chapter.end_line}}}",
                    f"    source_char_range: {{start: {chapter.start_char}, end: {chapter.end_char}}}",
                ]
            )
        (root / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest.extend(f"  - {filename}" for filename in chunk_files)
    (root / "manifest.yaml").write_text("\n".join(manifest) + "\n", encoding="utf-8")


def write_artifact(artifact_dir: Path, chapters: Iterable[Chapter], start: int, end: int) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    selected = [chapter for chapter in chapters if start <= chapter.number <= end]
    expected = set(range(start, end + 1))
    present = {chapter.number for chapter in selected}
    missing = sorted(expected - present)
    if missing:
        raise ValueError(f"requested artifact range has missing chapters: {missing}")

    combined = []
    metadata = {"range": {"start": start, "end": end}, "chapters": []}
    for chapter in selected:
        combined.append(chapter.text)
        metadata["chapters"].append(
            {"chapter": chapter.number, "title": chapter.title, "sha256": chapter.sha256}
        )
    (artifact_dir / f"chapters-{start:04d}-{end:04d}.txt").write_text(
        "\n".join(combined), encoding="utf-8"
    )
    (artifact_dir / f"chapters-{start:04d}-{end:04d}.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--output-root", default="sources/archive")
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--artifact-start", type=int, required=True)
    parser.add_argument("--artifact-end", type=int, required=True)
    parser.add_argument("--chunk-size", type=int, default=50)
    args = parser.parse_args()

    if args.chunk_size <= 0:
        parser.error("--chunk-size must be positive")
    if args.artifact_start > args.artifact_end:
        parser.error("artifact start must not exceed artifact end")

    raw = download(args.url)
    text, encoding = decode_source(raw)
    chapters = parse_chapters(text)
    write_manifest(
        Path(args.output_root),
        args.source_id,
        args.url,
        raw,
        encoding,
        chapters,
        args.chunk_size,
    )
    write_artifact(
        Path(args.artifact_dir), chapters, args.artifact_start, args.artifact_end
    )
    print(
        json.dumps(
            {
                "source_sha256": sha256_bytes(raw),
                "source_bytes": len(raw),
                "encoding": encoding,
                "chapter_count": len(chapters),
                "chapter_first": chapters[0].number,
                "chapter_last": chapters[-1].number,
                "artifact_start": args.artifact_start,
                "artifact_end": args.artifact_end,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"archive source indexing failed: {exc}", file=sys.stderr)
        raise
