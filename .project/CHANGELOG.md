# Changelog

## RUN-0126 — 2026-07-29

- Re-read Workflow, State, Tasks, Metrics, Dashboard, Changelog, the frozen RUN-0125 audit, canonical generators, CI and current `main` before execution; confirmed `TASK-0112` was the only pending Task and no concurrent normalization PR existed.
- Created no Timeline Node and did not change the closed Chapter 1—876 main-story boundary or process extras.
- Added append-only Character, Gift and Artifact normalization extensions plus `data/normalization/run-0126.yaml` as the machine-readable decision ledger.
- Corrected four directly evidenced Character name assignments: `CHAR-0052` to 程双, `CHAR-0056` to 黑风, `CHAR-0111` to 司空浩南 and `CHAR-0140` to 丁静.
- Resolved `雪瑶仙帝` as the restored reincarnation identity of `CHAR-0002` and `天羽` as the inherited identity of `CHAR-0045`; retained chapter ranges and did not use name similarity as proof.
- Preserved legal same-name records for 凤青玄、玉冰 and 黑无忌. Marked the later duplicate 阴萱 and 云花海 records as superseded while retaining their IDs and migrating their later facts to the primary records.
- Removed misapplied growth fields from the dead 猿族族长刘爱花, the dead 玉石宗掌门凤青玄 and 黑风, and migrated the supported growth facts to `CHAR-0002` or `CHAR-0045`.
- Added structured participant resolutions for all 18 Gift candidates. Exact people, multi-person recipients and collectives are distinguished; `GIFT-0110`, `GIFT-0160` and `GIFT-0257` remain explicitly unresolved with reasons.
- Replaced the old whole-row Gift—Artifact heuristic with a frozen component-disposition ledger covering all 25 candidates. Generic pills, currency, equipment groups and mixed bundles are classified without inventing Artifact IDs.
- Corrected `ART-0017` to 九火琉璃罩, `ART-0018` to 流光星陨戒 and `ART-0044` to 九天神莲戒 from direct document, ability and event evidence.
- Added lifecycle events to `ART-0017`, `ART-0023` and `ART-0026`, cleared their active holders after destruction or consumption, and preserved 徐霄 as former holder.
- Classified `ART-0055` and `ART-0099` as the same Artifact type with distinct batch IDs rather than merging their acquisition pools.
- Added `scripts/normalize_repository.py` to validate alias identities, duplicate-name dispositions, Gift participants, Gift component coverage, Artifact lifecycle conservation and final-state consistency from temporary canonical builds.
- Added automatic outputs `data/audits/run-0126.yaml`, `data/generated/final-state.yaml`, `docs/08-analysis/entity-normalization.md` and `docs/08-analysis/final-state-snapshot.md` to PR validation and post-merge materialization.
- Upgraded Workflow to v2.6 with explicit identity-relation, Gift participant/component and append-only Artifact lifecycle rules.
- Completed `TASK-0112`; queued only `TASK-0113` as pending. `BLOCK-0005` remains open because the authorized connector still has no tag/GitHub Release creation action.

## RUN-0125 — 2026-07-29

- Read Workflow, State, Tasks, Metrics, Dashboard, Changelog, CI, generators, validators, extension rules, latest `main` and the latest generated-view commit before execution.
- Confirmed the recovery baseline from the repository itself: `RUN-0124`, `TASK-0110`, `NODE-0108`, Chapters 1—876, 108 Timeline nodes, 235 characters, 259 Gift events, 149 Artifacts, no pending Task and no pre-existing blocker.
- Created only the new audit task `TASK-0111`; did not create or modify any main-story Timeline Node and did not process extras.
- Added deterministic full-repository audit tooling and PR/main CI integration. The audit parses all YAML, rebuilds canonical indexes, validates IDs, Timeline continuity, references, Project OS metrics, generated entity documents, character growth, final state, verification debt, copyright boundary and reproducibility hashes.
- The first audit CI run failed with 44 reported blocking lines. Diagnostics showed that 41 lines came from an invalid assumption that historical extension filenames must equal Run IDs and that each Run may have only one root extension file; the historical extension contract permits those layouts. The audit policy now treats them as compatibility warnings while continuing to enforce deterministic rebuild and retention.
- The same failed run exposed a real cross-index defect: `GIFT-0027` was anchored to `NODE-0019` although its gift chapter is 116 and belongs to `NODE-0018`. Added append-only `data/extensions/system/run-0125.yaml` to set `node: NODE-0018` and `resolution_node: NODE-0019`.
- A later PR audit correctly reported tracked `data/generated/gifts.yaml` as stale after the canonical correction. The policy now permits that drift only on canonical-changing PRs after temporary rebuild validation; the post-merge `main` refresh must rebuild the tracked generated view before freezing the v1 baseline.
- Corrected audit identity matching to use canonical name/alias/identity fields rather than arbitrary relationship text, and corrected final life-status reporting to prefer the latest time-based `status_change` over historical snapshot fields.
- Full PR gates then passed: knowledge-base tests, entity renderer tests, identity tests, growth tests, base/extension validation, growth continuity, temporary canonical build and validation, entity-document rendering, full-repository audit, whitespace check and artifact uploads.
- Audit baseline: 511 YAML files, 385 extension files, 751 canonical IDs, continuous Chapters 1—876, 108 Timeline nodes, 235 characters, 259 Gift events, 149 Artifacts and 384 generated entity documents.
- Verification-field accounting: 579 `verified`, 1404 `partial`, 59 `pending`, 0 `conflict` and 1 `inferred`. These counts distinguish evidence states and do not imply that Chapters 17—876 were unread.
- Queued evidence-based normalization findings for `TASK-0112`: seven duplicate character-name groups, unresolved exact identity labels `雪瑶仙帝` and `天羽`, eighteen Gift participant candidates, twenty-five Gift rows without exact Artifact-name matches, three duplicate Artifact-name groups and three Artifact lifecycle candidates.
- Upgraded Workflow to v2.5 and transitioned Project OS to `story_status: complete`, `project_status: maintenance`, `release_status: preparing_v1`.
- Completed `TASK-0111`; created `TASK-0112` as the single pending Task and `TASK-0113` as planned behind it.
- Prepared full audit reports, a machine-readable audit and `RELEASE_NOTES_v1.0.0.md` for post-merge automatic materialization.
- Squash-merged PR #95 as business commit `cd24ac05347e6d1aad5bff3ae3d48373cac1d7af` after the final complete PR CI passed.
- Post-merge verification found that the push-triggered materialization produced no generated-view commit: `data/audits/run-0125.yaml` and `RELEASE_NOTES_v1.0.0.md` were absent, while `data/generated/gifts.yaml` still showed `GIFT-0027.node: NODE-0019`. The connector exposed no push-run record or failure log, so no unverified root cause was asserted.
- Added a merged-PR `closed` fallback, serialized the refresh job across trigger types, and pinned v1 audit generation to the verified business commit from `.project/STATE.yaml`. This recovery remains part of `RUN-0125` / `TASK-0111`, not a new Task.
- Registered `BLOCK-0005`: the authorized GitHub connector exposes no tag or GitHub Release creation action. `v1.0.0` is not claimed as created.

## RUN-0124 — 2026-07-29

- Read Workflow v2.4, state, task queue, quality rules, metrics, changelog and dashboard before execution.
- Resumed only the unique pending `TASK-0110`; no completed task, Timeline node or entity ID was intentionally duplicated.
- Reused the unexpired Chapters 827—876 evidence artifact and matched Chapters 864—876 against archived per-chapter SHA-256 values.
- Extended the provisional Chapter 872 boundary through Chapter 876 because Chapters 873—876 complete the same炼神鼎 crisis,神煞界覆灭,九大仙域重组 and正文终局.
- Created `NODE-0108`, covering Chapters 864—876.
- Added `CHAR-0235` 神无机 and updated the principal combatants,救援关系人物 and仙帝终局角色 with timed growth events.
- Added `GIFT-0252`—`GIFT-0259` and `ART-0147`—`ART-0149`.
- Recorded丹药返还库提升至鸿蒙仙、羁绊度上限提升至3、三级羁绊十倍增量、三次暂存升级机会 and徐霄晋升大罗并成为至尊仙帝.
- Completed `TASK-0110`;正文主线已覆盖至第876章终章，无后续 pending task.

## RUN-0123 — 2026-07-29

- Created `NODE-0107`, covering Chapters 854—863; completed `TASK-0109` and queued `TASK-0110`.

## Audit history

Full earlier changelog details remain immutable and auditable in Git history, prior Project OS commits, task metadata and append-only extension files.
