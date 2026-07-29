# return

《万倍返还，年迈的我去当舔狗》结构化剧情知识库。

正文第 1—876 章已完成结构化覆盖。仓库现处于 `maintenance / audit / analysis / release` 阶段，继续维护人物身份、赠送与返还、物品流转、最终状态、核验债务和自动派生分析；正文完成不等于项目停止维护。

## 项目状态

- `story_status: complete`
- `project_status: maintenance`
- `release_status: preparing_v1`
- 正文 Timeline 截止第 876 章；不得虚构第 877 章后的主线。
- 番外使用独立 `scope: extras`，不进入正文节点连续性和正文完成统计。
- 实时状态、唯一下一项 Task 和 blocker 以 `.project/STATE.yaml`、`.project/TASKS.yaml` 与 `.project/DASHBOARD.md` 为准。

## 知识库目标

- 以剧情阶段而非单章为主线，建立稳定、可维护的 Timeline。
- 建立章节证据、人物、系统、境界、势力、物品和战斗之间的交叉索引。
- 区分正文事实、上下文推断、来源冲突和待核实内容。
- 从 canonical generated indexes 自动生成实体档案、审计报告、终局快照和后续统计分析，避免手工维护第二份事实。
- 不保存整章正文，只保存原创摘要、结构化事实、来源元数据、哈希和核验状态。

## 工作标准

- 章节是证据单元，不默认一章一个 Timeline Node。
- `story_arc` Task 以冲突闭环、目标转换或重大状态变化为边界。
- 维护阶段支持 `audit`、`data_quality`、`normalization`、`analysis`、`release` 和隔离的 `extras` Task。
- 每次 Run 只执行唯一下一项 pending Task，并使用新的 Run ID。
- 人物、物品和系统档案只在出现长期有效的实质变化时增量更新。
- `data/generated/`、人物档案、物品档案和 manifest 是自动物化视图，不是手工事实源。
- 修正必须进入基础索引或 append-only extensions。
- 重复人物 ID 通过 `record_status: superseded` 保留历史审计链；不得因名字相似删除或合并。
- Gift 的人物解析与资源组件分类分开处理；普通资源批次不强制创建 Artifact。
- 消耗或损毁 Artifact 不得继续保留 active `current_holder`。
- Timeline 共现关系仅是分析派生边，不得反向写成 canonical 人物关系事实。
- 详细规范见 `docs/00-project/WORKFLOW.md`。

## 目录

- `docs/00-project/`：项目规范、路线图与术语表
- `docs/01-timeline/`：正文剧情节点与总时间线
- `docs/02-characters/`：自动物化的人物档案
- `docs/03-system/`：系统与返还记录
- `docs/04-world/`：世界观、地点与势力
- `docs/05-realms/`：境界体系与成长轨迹
- `docs/06-artifacts/`：自动物化的法宝、丹药、功法与神通档案
- `docs/07-battles/`：战斗记录
- `docs/08-analysis/`：审计、规范化与自动派生分析
- `data/`：结构化 YAML 数据
- `data/extensions/`：不可变追加记录与增量补丁
- `data/generated/`：由脚本生成的完整 canonical indexes 与终局快照
- `data/audits/`：机器可读审计、规范化和分析门禁结果
- `data/normalization/`：证据化规范化决策账本
- `data/analysis/`：统计摘要、完整关系边和 SQLite 查询快照
- `scripts/`：索引聚合、渲染、身份校验、成长连续性、全库审计、规范化和分析工具
- `sources/`：来源索引、归档哈希与核验说明

## Canonical 索引

仓库采用三层索引模型：

1. `data/timeline/`、`data/characters/`、`data/system/`、`data/artifacts/` 保存周期性压缩后的基础索引；
2. `data/extensions/` 保存每次 Run 的追加记录和对既有实体的增量更新；
3. `data/generated/` 将基础索引与全部扩展合并，是外部程序默认应读取的完整索引。

本地生成和校验：

```bash
python -m pip install PyYAML==6.0.2
python scripts/test_knowledge_base.py
python scripts/test_render_entity_docs.py
python scripts/test_validate_entity_identity.py
python scripts/test_render_character_growth.py
python scripts/knowledge_base.py validate
python scripts/knowledge_base.py build --output-dir data/generated
python scripts/knowledge_base.py validate --generated-dir data/generated
python scripts/validate_entity_identity.py --generated-dir data/generated
python scripts/render_character_growth.py --validate-continuity --effective-run 82
python scripts/render_character_growth.py --generated-dir data/generated --check
python scripts/normalize_repository.py --generated-dir data/generated --output-root .
```

## v1 全库审计

`RUN-0125` 增加可复现审计：

```bash
python scripts/run_full_repository_audit.py \
  --run-id RUN-0125 \
  --task-id TASK-0111 \
  --version v1.0.0 \
  --output-root build/audit
```

物化产物包括：

- `docs/08-analysis/full-repository-audit.md`
- `docs/08-analysis/verification-debt.md`
- `docs/08-analysis/v1-baseline-statistics.md`
- `data/audits/run-0125.yaml`
- `RELEASE_NOTES_v1.0.0.md`

审计明确区分官方页面直接核验、用户归档正文、逐章 SHA-256、可读镜像、单一来源、上下文推断和正文冲突。“官方直接核验至第 16 章”不表示第 17—876 章未经正文阅读。

## RUN-0126 实体规范化

`TASK-0112` 对审计 findings 进行证据化处置，不以减少 pending 数量为目标：

- 人物 alias、转世身份、继承身份、合法同名和 superseded 记录分开表达；
- Gift 保留原始受赠文本，并增加精确人物、群体或未决解析；
- 25 条 Gift—Artifact 候选按资源组件分类，只有证据充分的唯一物品才绑定 Artifact ID；
- Artifact 使用 append-only lifecycle event 表达转移、消耗和损毁；
- `data/generated/final-state.yaml` 由 canonical indexes 自动派生。

对应产物：

- `data/normalization/run-0126.yaml`
- `data/audits/run-0126.yaml`
- `data/generated/final-state.yaml`
- `docs/08-analysis/entity-normalization.md`
- `docs/08-analysis/final-state-snapshot.md`

## RUN-0127 全书统计与关系图

`TASK-0113` 从 canonical generated indexes 构建冻结的统计与查询快照，不修改正文事实：

```bash
python scripts/analyze_repository.py \
  --generated-dir data/generated \
  --output-root . \
  --source-commit "$(git rev-parse HEAD)" \
  --analysis-date 2026-07-29
```

主要产物：

- `data/analysis/run-0127/summary.json`：全书统计摘要；
- `data/analysis/run-0127/relationships.jsonl`：完整关系边；
- `data/analysis/run-0127/full-book.sqlite3`：11 表查询数据库；
- `data/analysis/run-0127/schema.sql`：SQLite Schema；
- `docs/08-analysis/full-book-analysis.md`：人类可读分析；
- `docs/08-analysis/relationship-graph.mmd`：Mermaid 关系图；
- `docs/08-analysis/relationship-graph.dot`：Graphviz 关系图；
- `data/audits/run-0127.yaml`：机器门禁、输入哈希和输出哈希。

关系边分为 Gift、显式关系、身份关系和 Timeline 共现。Timeline 共现只是同一剧情节点中的共同出现；无法唯一解析的人名或关系标签保留为 finding，不强制绑定 Character ID。

SQLite 示例：

```bash
sqlite3 data/analysis/run-0127/full-book.sqlite3 \
  "SELECT name, weighted_degree, neighbor_count FROM characters WHERE record_status != 'superseded' ORDER BY weighted_degree DESC LIMIT 10;"
```

## 核验状态

- `verified`：正文直接确认
- `partial`：仅部分字段得到确认
- `inferred`：根据上下文推断
- `conflict`：来源之间存在冲突
- `pending`：尚未核实

不得为了减少 pending 数量进行无证据推断，也不得因名字相似擅自合并人物或物品。

## 自动化与发布边界

`Knowledge Base CI` 在 PR 中运行全部测试、临时 canonical 重建、实体文档校验、全库审计和规范化门禁；`Full Book Analysis` 生成并验证 JSON、JSONL、SQLite、Mermaid 和 Graphviz 产物。合并后，分析快照在 canonical refresh 完成后冻结，避免两个工作流竞争写入 `main`。

当前授权连接器不能创建 Git tag 或 GitHub Release，因此仓库内 Release Notes 可以完成，但 `v1.0.0` Release 在 GitHub 实际创建前始终保持 blocker，不会被虚构为已发布。

## 版权边界

本仓库不保存整章正文，仅保存原创摘要、结构化事实、来源元数据、哈希和核验状态。原作品版权归原作者及相关权利人所有。
