# Changelog

## RUN-0081 — 2026-07-27

- Read Workflow v2.3, state, task queue, quality rules, metrics, changelog and dashboard before execution.
- Audited generated character profiles after the user required a growth line containing at least time, key events and core abilities, presented through continuous recording plus staged structure.
- Preserved the concurrent completed `RUN-0080` story arc, Chapters 500—508, `NODE-0066`, all 104 character records and all 69 artifact records; `TASK-0069` remains the next pending story task.
- Added `scripts/render_character_growth.py`, which wraps the canonical reader renderer and inserts a first-class `成长线` section into each character profile.
- Historical growth events are reconstructed from append-only character extension files and canonical Timeline nodes; time is expressed as an exact chapter only when recorded, otherwise as the verified node chapter range.
- Added a stage summary grouped by 50-chapter windows, showing stage events, core ability evolution and long-term effects.
- Added a continuous chronological log with time, key event, core ability/growth, identity/relationship/resource impact, node/run evidence and verification status; older records collapse after eight events while recent records remain visible.
- Added an append-only continuity rule effective from `RUN-0082`: every material character update in a story Run must include a structured `growth_event_add`; new characters must include timed `first_appearance` data.
- Added renderer and continuity unit tests, and updated CI to validate and materialize growth-line documents both in PRs and on `main` refresh.
- Upgraded the workflow standard to v2.4 and added the Character growth continuity quality gate.
- Added no new story facts and did not consume or duplicate `TASK-0069`.

## RUN-0080 — 2026-07-27

- Read Workflow v2.3, state, task queue, quality rules, metrics, changelog and dashboard before execution.
- Resumed only `TASK-0068`; no completed task, node or entity ID was duplicated.
- Extended the adaptive boundary through Chapter 508 so the天元仙塔百层挑战、极致肉身展示、跨宗道侣安排 and赠送返还 remain one coherent arc; Chapter 509 begins幽冥天绝阵 and a new system-return conflict.
- Created `NODE-0066`: 天元仙塔百层、极致肉身与跨宗结缘, covering Chapters 500—508.
- Added 紫霄 and 血葵 as `CHAR-0103` and `CHAR-0104`; updated 徐霄、云心月、陆雪瑶、叶尘、独孤浩 and楚霄.
- Recorded徐霄大乘三重、三十二道鸿蒙真气、百层通关、渡劫六重肉身对抗 and渡劫后期级公开战略威慑.
- Added `GIFT-0108` and `GIFT-0109`, recording four high-level recipient gifts and six matchmaker thank-you gifts.
- Added `ART-0069` 四柄仙器神剑（逐件名称待确认） and expanded三千大道丹、鸿蒙一气丹、雷灵丹 records.
- Preserved三火大道精确构成、完整圆满大道清单、百层金龙机制、仙器神剑逐件映射、紫霄血葵完整面板 and `GIFT-0109` return as pending.
- Source traceability passed with qualifications; all other gates including entity-document freshness, readability and character identity alignment passed.
- Completed `TASK-0068`, advanced to milestone M11 and queued `TASK-0069` beginning at Chapter 509.

## RUN-0079 — 2026-07-27

- Repaired five historical canonical character identity collisions and added a permanent identity-to-profile-path validator.
- Preserved Chapters through 499, 65 nodes, 102 characters, 107 gifts and 68 artifacts.

## RUN-0078 — 2026-07-27

- Redesigned generated character and artifact profiles into reader-friendly semantic sections with collapsed canonical audit appendices.

## RUN-0077 — 2026-07-27

- Created `NODE-0065`, covering Chapters 494—499; completed `TASK-0067` and queued `TASK-0068`.

## Audit history

Full changelog details through `RUN-0076` remain immutable and auditable in Git history, prior Project OS commits, task metadata and append-only extension files.
