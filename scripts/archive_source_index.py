#!/usr/bin/env python3
"""Download a supplied novel source transiently and emit auditable metadata.

The repository stores only source manifests, per-chapter hashes, titles and
location metadata. Requested full chapter text is written exclusively to an
artifact directory for temporary evidence review and is not committed.

Some archive exports contain a table-of-contents sequence followed by the full
chapter sequence. The parser therefore splits headings whenever chapter numbers
reset and selects the unique sequence that completely covers the requested
review window. All detected sequence ranges remain recorded in the manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
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


@dataclass(frozen=True)
class ChapterSequence:
    index: int
    chapters: tuple[Chapter, ...]

    @property
    def first(self) -> int:
        return self.chapters[0].number

    @property
    def last(self) -> int:
        return self.chapters[-1].number

    @property
    def total_chars(self) -> int:
        return sum(len(chapter.text) for chapter in self.chapters)

    @property
    def median_chapter_chars(self) -> int:
        return int(statistics.median(len(chapter.text) for chapter in self.chapters))

    def covers(self, start: int, end: int) -> bool:
        numbers = {chapter.number for chapter in self.chapters}
        return all(number in numbers for number in range(start, end + 1))

    def review_window_chars(self, start: int, end: int) -> int:
        return sum(
            len(chapter.text)
            for chapter in self.chapters
            if start <= chapter.number <= end
        )


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


def parse_chapter_sequences(text: str) -> list[ChapterSequence]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    matches = list(CHAPTER_RE.finditer(normalized))
    if not matches:
        raise ValueError("no chapter headings matched expected 第N章 format")

    parsed: list[Chapter] = []
    for index, match in enumerate(matches):
        number = int(match.group(1))
        title = match.group(2).strip()
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        chapter_text = normalized[start:end].rstrip() + "\n"
        start_line = normalized.count("\n", 0, start) + 1
        end_line = start_line + chapter_text.count("\n") - 1
        parsed.append(
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

    grouped: list[list[Chapter]] = []
    current: list[Chapter] = []
    for chapter in parsed:
        if current and chapter.number <= current[-1].number:
            grouped.append(current)
            current = []
        current.append(chapter)
    if current:
        grouped.append(current)

    sequences: list[ChapterSequence] = []
    for sequence_index, chapters in enumerate(grouped, start=1):
        numbers = [chapter.number for chapter in chapters]
        if len(numbers) != len(set(numbers)):
            raise ValueError(f"sequence {sequence_index} contains duplicate chapter numbers")
        if numbers != sorted(numbers):
            raise ValueError(f"sequence {sequence_index} is not monotonically increasing")
        sequences.append(ChapterSequence(sequence_index, tuple(chapters)))
    return sequences


def select_sequence(
    sequences: list[ChapterSequence], review_start: int, review_end: int
) -> ChapterSequence:
    candidates = [
        sequence for sequence in sequences if sequence.covers(review_start, review_end)
    ]
    if not candidates:
        ranges = [f"{sequence.first}-{sequence.last}" for sequence in sequences]
        raise ValueError(
            f"no chapter sequence fully covers {review_start}-{review_end}; "
            f"detected ranges: {ranges}"
        )
    if len(candidates) == 1:
        return candidates[0]

    ranked = sorted(
        candidates,
        key=lambda sequence: (
            sequence.review_window_chars(review_start, review_end),
            sequence.median_chapter_chars,
            sequence.total_chars,
        ),
        reverse=True,
    )
    first_score = (
        ranked[0].review_window_chars(review_start, review_end),
        ranked[0].median_chapter_chars,
        ranked[0].total_chars,
    )
    second_score = (
        ranked[1].review_window_chars(review_start, review_end),
        ranked[1].median_chapter_chars,
        ranked[1].total_chars,
    )
    if first_score == second_score:
        raise ValueError(
            f"multiple indistinguishable sequences cover {review_start}-{review_end}: "
            f"{[sequence.index for sequence in ranked]}"
        )
    return ranked[0]


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def write_manifest(
    output_root: Path,
    source_id: str,
    url: str,
    raw: bytes,
    encoding: str,
    sequences: list[ChapterSequence],
    selected_sequence: ChapterSequence,
    chunk_size: int,
) -> None:
    root = output_root / source_id
    root.mkdir(parents=True, exist_ok=True)
    chapters = list(selected_sequence.chapters)
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
        f"detected_sequence_count: {len(sequences)}",
        f"selected_sequence: {selected_sequence.index}",
        "selection_rule: complete_review_window_then_largest_text_payload",
        "detected_sequences:",
    ]
    for sequence in sequences:
        manifest.extend(
            [
                f"  - index: {sequence.index}",
                f"    chapter_first: {sequence.first}",
                f"    chapter_last: {sequence.last}",
                f"    chapter_count: {len(sequence.chapters)}",
                f"    total_chars: {sequence.total_chars}",
                f"    median_chapter_chars: {sequence.median_chapter_chars}",
            ]
        )
    manifest.extend(
        [
            f"chapter_count: {len(chapters)}",
            f"chapter_first: {first}",
            f"chapter_last: {last}",
            f"chapter_chunk_size: {chunk_size}",
            "chapter_index_files:",
        ]
    )

    chunk_files: list[str] = []
    for chunk_start in range(
        ((first - 1) // chunk_size) * chunk_size + 1, last + 1, chunk_size
    ):
        chunk_end = chunk_start + chunk_size - 1
        selected = [
            chapter for chapter in chapters if chunk_start <= chapter.number <= chunk_end
        ]
        if not selected:
            continue
        filename = f"chapters-{chunk_start:04d}-{chunk_end:04d}.yaml"
        chunk_files.append(filename)
        lines = [
            "schema_version: 1",
            f"source_id: {source_id}",
            f"selected_sequence: {selected_sequence.index}",
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


def write_artifact(
    artifact_dir: Path, chapters: Iterable[Chapter], start: int, end: int
) -> None:
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
    sequences = parse_chapter_sequences(text)
    selected_sequence = select_sequence(
        sequences, args.artifact_start, args.artifact_end
    )
    chapters = list(selected_sequence.chapters)
    write_manifest(
        Path(args.output_root),
        args.source_id,
        args.url,
        raw,
        encoding,
        sequences,
        selected_sequence,
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
                "detected_sequence_count": len(sequences),
                "selected_sequence": selected_sequence.index,
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
