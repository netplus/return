# Changelog

## RUN-0082 — 2026-07-27

- Read Workflow v2.4, state, task queue, quality rules, metrics, changelog and dashboard before execution.
- Reviewed the post-merge character growth projection and found a temporal-accuracy defect: the synthetic first-appearance event summarized fields from the fully merged current character record, which could display late cultivation or abilities at an early chapter.
- Changed first-appearance rendering to record only the confirmed entrance time and title; when no independent historical capability snapshot exists, the profile explicitly states that limitation.
- Prohibited backfilling early growth events from merged current-state fields.
- Added a regression test ensuring a late `cultivation_change` such as 大乘三重 does not appear inside the first-appearance event block.
- Added manifest and Project OS metadata for `no_backfill_from_merged_current_snapshot`.
- Preserved Chapters through 508, `NODE-0066`, 104 characters, 109 gifts and 69 artifacts; no new story facts were added.
- Left `TASK-0069` as the next unique pending story task beginning at Chapter 509.

## RUN-0081 — 2026-07-27

- Added a first-class character growth-line projection with 50-chapter staged summaries and a continuous chronological event log.
- Historical events are reconstructed from append-only character extensions and Timeline nodes; future material character updates require structured timed growth events.
- Preserved Chapters through 508 and left `TASK-0069` pending.

## RUN-0080 — 2026-07-27

- Created `NODE-0066`, covering Chapters 500—508; completed `TASK-0068` and queued `TASK-0069`.

## RUN-0079 — 2026-07-27

- Repaired five historical canonical character identity collisions and added a permanent identity-to-profile-path validator.

## RUN-0078 — 2026-07-27

- Redesigned generated character and artifact profiles into reader-friendly semantic sections with collapsed canonical audit appendices.

## Audit history

Full changelog details through `RUN-0077` remain immutable and auditable in Git history, prior Project OS commits, task metadata and append-only extension files.
