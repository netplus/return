# Working process

This directory stores the minimum project-management state needed to resume work reliably.

Every run should:

1. Read `STATE.yaml`.
2. Read `TASKS.yaml` and select the first `pending` task whose dependencies are complete.
3. Perform the task and update the relevant knowledge-base files.
4. Mark the task complete or blocked.
5. Update `STATE.yaml`.
6. Append a brief entry to `CHANGELOG.md`.
7. Refresh `DASHBOARD.md`.

Keep the process lightweight. Prefer useful content over process expansion. Facts added to the knowledge base must be supported by the source text; uncertain claims remain pending.
