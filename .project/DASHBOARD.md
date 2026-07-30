# Project dashboard

- **Story status:** Complete — main story covers Chapters 1—876
- **Project status:** Maintenance
- **Release status:** Preparing `v1.0.0`
- **Current milestone:** M23 — Authorized extras source registration and partial isolated ingestion
- **Workflow standard:** v2.6 — Evidence-based normalization and maintenance analysis
- **Canonical index mode:** Base indexes plus append-only extensions
- **Entity-document mode:** Reader-friendly canonical projection with staged growth lines and collapsed audit appendix
- **Canonical coverage through:** Chapter 876
- **Current evidence exploration through:** Chapter 876 plus 2 isolated extras
- **Direct official verification through:** Main story Chapter 16; extras metadata verified, content partial
- **Archive text and per-chapter hash coverage through:** Main story Chapter 876
- **Completed main-story timeline nodes:** 108
- **Isolated extras nodes:** 2 partial
- **Documented character records:** 235 historical / 233 active after normalization
- **Generated character profiles:** 235
- **Gift events:** 259
- **Artifact records:** 149
- **Generated artifact profiles:** 149
- **Last run:** `RUN-0129`
- **Last completed task:** `TASK-0115`
- **Last completed main-story node:** `NODE-0108`
- **Next unique pending task:** `TASK-0116` — 番外官方全文复核与 partial 提升
- **Extras content blocker:** `BLOCK-0007` — current tooling cannot read both official extras in full
- **Release blocker:** `BLOCK-0005` — authorized connector cannot create a tag or GitHub Release

## RUN-0129 — authorized extras source and isolated nodes

The user authorized public source discovery, evidence reading, original summaries and structured fact extraction. This authorization does not permit storing full chapter text.

### Official source registration

- Provider: 番茄小说
- Official work ID: `7423641263695481880`
- Official catalog: 878 entries
- Main story: 876 chapters
- Extras: 2 entries
- Registered source ID: `EXTRA-SRC-0001`

| Extras ID | Title | Official Reader ID | Verification |
|---|---|---|---|
| `EXTRA-NODE-0001` | 番外一，林嫣儿篇 | `7536463745459946046` | partial |
| `EXTRA-NODE-0002` | 番外二，凤溪篇 | `7538798715943780889` | partial |

Titles, order, IDs and publication metadata come from the official catalog. Content facts remain `partial` because the current tool cannot read both official chapters in full; public secondary indexes are corroboration only.

### Isolation and copyright results

- Main story remains Chapters 1—876 and ends at `NODE-0108`.
- No `CHAR-*`, `GIFT-*`, `ART-*` or main-story `NODE-*` record was mutated.
- Existing main-story Characters are referenced only by validated IDs.
- No full chapter text or long verbatim quote is stored.
- `BLOCK-0006` is resolved by the official source registration.
- `TASK-0116` may upgrade facts only after official full-content access or user-provided authorized text.

### Outputs

- `sources/extras/fanqienovel-7423641263695481880/manifest.yaml`
- `data/extras/run-0129.yaml`
- `data/audits/run-0129.yaml`
- `docs/09-extras/_INDEX.md`
- `docs/09-extras/extra-node-0001.md`
- `docs/09-extras/extra-node-0002.md`
- `scripts/validate_extras_ingestion.py`

## Frozen main-story analysis baseline

- 876 chapters represented by 108 continuous Timeline Nodes.
- 235 historical Character records, including 233 active and 2 superseded records.
- 259 Gift records and 149 Artifact records.
- 2,581 relationship edges retained in JSONL and SQLite.
- Visual projection: 30 Character nodes and 120 high-weight edges.
- SQLite snapshot: 11 reconciled tables.

The **三次暂存升级机会 remain `pending`**; the extras work makes no claim about their use.

The frozen v1 audit and `RELEASE_NOTES_v1.0.0.md` remain valid. Git tag and GitHub Release `v1.0.0` are **not created** because the authorized connector exposes no tag/Release creation action; this remains `BLOCK-0005` rather than a fabricated success.
