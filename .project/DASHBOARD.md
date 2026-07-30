# Project dashboard

- **Story status:** Complete — main story covers Chapters 1—876
- **Project status:** Maintenance
- **Release status:** Preparing `v1.0.0`
- **Current milestone:** M22 — Extras scope isolation and source inventory
- **Workflow standard:** v2.6 — Evidence-based normalization and maintenance analysis
- **Canonical index mode:** Base indexes plus append-only extensions
- **Entity-document mode:** Reader-friendly canonical projection with staged growth lines and collapsed audit appendix
- **Canonical coverage through:** Chapter 876
- **Current evidence exploration through:** Chapter 876
- **Direct official verification through:** Chapter 16
- **Archive text and per-chapter hash coverage through:** Chapter 876
- **Completed timeline nodes:** 108
- **Draft timeline nodes:** 0
- **Documented character records:** 235 historical / 233 active after normalization
- **Generated character profiles:** 235
- **Gift events:** 259
- **Artifact records:** 149
- **Generated artifact profiles:** 149
- **Last run:** `RUN-0128`
- **Last completed task:** `TASK-0114`
- **Last completed node:** `NODE-0108`
- **Next unique pending task:** None
- **Extras ingestion status:** Blocked by `BLOCK-0006` pending an authorized source
- **Release blocker:** `BLOCK-0005` — authorized connector cannot create a tag or GitHub Release

## RUN-0128 — extras scope inventory

`TASK-0114` inventories only tracked repository material, initializes an isolated namespace contract and verifies that no extras fact enters the completed main-story Timeline.

### Inventory results

- 1,066 tracked files inspected deterministically.
- 114 files occur under configured source roots; all remain classified as main-story evidence.
- 0 tracked files qualify as an extras source corpus.
- 7 files are classified only as scope-control mentions.
- The `额外传送仙台` substring and the source-index question about whether extras exist were reviewed and excluded as false positives.
- No chapter boundary was invented because there is no qualifying source.

### Namespace contract

| Data type | Isolated namespace |
|---|---|
| Source | `EXTRA-SRC-NNNN` |
| Timeline | `EXTRA-NODE-NNNN` |
| Character | `EXTRA-CHAR-NNNN` |
| Gift | `EXTRA-GIFT-NNNN` |
| Artifact | `EXTRA-ART-NNNN` |

Extras-only facts must not mutate `NODE-*`, `CHAR-*`, `GIFT-*` or `ART-*` main-story final state. Existing main-story entity IDs may be referenced only when direct evidence establishes identity.

### Outputs

- `data/extras/run-0128-config.yaml`
- `data/audits/run-0128.yaml`
- `data/extras/run-0128-scope.yaml`
- `data/extras/run-0128-task-plan.yaml`
- `docs/08-analysis/extras-scope-inventory.md`
- `scripts/inventory_extras.py`
- `.github/workflows/extras-scope-inventory.yml`

## RUN-0127 — full-book analysis baseline

The frozen main-story analysis remains unchanged:

- 876 chapters represented by 108 continuous Timeline Nodes.
- 235 historical Character records, including 233 active and 2 superseded records.
- 259 Gift records and 149 Artifact records.
- 2,581 relationship edges, retained completely in JSONL and SQLite.
- Visual projection: 30 Character nodes and 120 high-weight edges.
- SQLite snapshot: 11 reconciled tables.

Ambiguous labels remain findings rather than forced bindings: 53 Timeline labels, 14 Gift participant labels and 14 explicit relationship labels.

## Quality gates — RUN-0128

| Gate | Result |
|---|---|
| Tracked-file inventory | Passed — 1,066 files |
| Candidate classification | Passed — 0 source candidates |
| Chapter-boundary inventory | Passed — no invented boundary |
| Namespace uniqueness | Passed — 0 collisions |
| Main-story isolation | Passed — Chapters 1—876 / `NODE-0108` unchanged |
| Deterministic serialization | Passed |
| Copyright boundary | Passed — metadata only |
| Existing Knowledge Base CI | Passed in PR validation |

## Current boundary

There is no pending repository Task. An isolated ingestion Task can be created only after an authorized extras source is added or identified; this is `BLOCK-0006`, not an inferred story continuation.

The **三次暂存升级机会 remain `pending`**; RUN-0128 makes no claim about their use.

The frozen v1 audit and `RELEASE_NOTES_v1.0.0.md` remain valid. Git tag and GitHub Release `v1.0.0` are **not created** because the authorized connector exposes no tag/Release creation action; this remains `BLOCK-0005` rather than a fabricated success.
