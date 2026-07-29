# Project dashboard

- **Story status:** Complete — main story covers Chapters 1—876
- **Project status:** Maintenance
- **Release status:** Preparing `v1.0.0`
- **Current milestone:** M21 — Full-book statistics, graph and query dataset
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
- **Last run:** `RUN-0127`
- **Last completed task:** `TASK-0113`
- **Last completed node:** `NODE-0108`
- **Next unique pending task:** `TASK-0114` — 番外 scope 盘点与独立命名空间初始化
- **Release blocker:** `BLOCK-0005` — authorized connector cannot create a tag or GitHub Release

## RUN-0127 — full-book analysis

`TASK-0113` derives a frozen analysis snapshot from the four canonical generated indexes. It creates no Timeline Node, changes no story fact and does not merge ambiguous labels. Timeline co-occurrence is explicitly marked as an analysis-only weak relation.

### Dataset results

- 876 chapters represented by 108 continuous Timeline Nodes.
- Node span: mean 8.11 chapters, median 8, minimum 1, maximum 23.
- 235 historical Character records, including 233 active and 2 superseded records.
- 259 Gift records and 149 Artifact records.
- 2,581 relationship edges:
  - 2,376 Timeline co-occurrence edges;
  - 103 explicit relationship edges;
  - 98 Gift edges;
  - 4 identity edges.
- Visual projection: 30 Character nodes and 120 high-weight edges.

### Query outputs

- `data/analysis/run-0127/summary.json`
- `data/analysis/run-0127/relationships.jsonl`
- `data/analysis/run-0127/full-book.sqlite3`
- `data/analysis/run-0127/schema.sql`
- `docs/08-analysis/full-book-analysis.md`
- `docs/08-analysis/relationship-graph.mmd`
- `docs/08-analysis/relationship-graph.dot`
- `data/audits/run-0127.yaml`

The SQLite snapshot contains 11 tables. Core row counts reconcile to 108 Timeline Nodes, 235 Characters, 259 Gifts, 149 Artifacts and 2,581 relationships.

## Analysis boundaries

- 53 Timeline labels could not be uniquely mapped to canonical Character IDs.
- 14 Gift participant labels remain unresolved or non-atomic.
- 14 explicit relationship labels remain ambiguous or refer to non-Character entities.
- These labels are retained as findings; none were forced into the graph.
- Timeline co-occurrence means only that two resolved Characters are listed in the same story-arc node.

## Quality gates — RUN-0127

| Gate | Result |
|---|---|
| Canonical source-count reconciliation | Passed |
| Timeline continuity | Passed — Chapters 1—876 |
| Superseded-record exclusion | Passed — 233 active / 2 superseded |
| Relationship endpoint integrity | Passed — 2,581 edges |
| Ambiguity preservation | Passed — no forced ambiguous bindings |
| SQLite integrity and row reconciliation | Passed — 11 tables |
| JSONL reconciliation | Passed — 2,581 lines |
| Deterministic serialization contract | Passed |
| Existing Knowledge Base CI | Passed |
| Copyright boundary | Passed |

## Next boundary

The next task is an inventory and namespace-design pass for extras. Extras remain isolated from the completed Chapter 1—876 main-story Timeline and must not reuse `NODE-*` main-story numbering.

The frozen v1 audit and `RELEASE_NOTES_v1.0.0.md` remain valid. Git tag and GitHub Release `v1.0.0` are **not created** because the authorized connector exposes no tag/Release creation action; this remains `BLOCK-0005` rather than a fabricated success.
