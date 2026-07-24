# Canonical extension indexes

The historical canonical indexes remain in the top-level YAML files:

- `data/timeline/nodes.yaml`
- `data/characters/characters.yaml`
- `data/system/gifts.yaml`
- `data/artifacts/artifacts.yaml`

From `RUN-0021`, append-only extension records may be stored under `data/extensions/` when rewriting a large historical index would risk accidental data loss. The base index and every extension record together form the canonical structured index.

Rules:

1. Each extension record must identify its node, entity or event ID.
2. IDs must remain globally unique across base and extension indexes.
3. Markdown knowledge artifacts must reference the same IDs and verification states.
4. Project metrics count base and extension records together.
5. A future compaction task may merge extensions into the base files only after full structural validation.
