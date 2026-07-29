# 剧情知识库工作标准

版本：2.6  
生效范围：自第 4 章起；第 1—3 章既有节点保留，不回溯拆改。正文第 876 章结束后，项目进入 maintenance / audit / analysis / release 模式。

## 1. 核心原则

- 正文章节是证据单元，不再默认等同于剧情节点。
- Timeline 以剧情阶段（story arc）为基本单元，一个节点通常覆盖约 5—10 章。
- 章节范围可伸缩；优先保证剧情闭环，不机械追求固定章数。
- 所有进入知识层的重要事实必须能追溯到正文或明确标注的证据渠道。
- 不保存整章正文，只保存原创摘要、事实字段、来源索引和哈希。
- 正文完成后不得虚构后续主线；番外必须使用独立 scope，不进入正文 Timeline 连续性统计。

## 2. 两层处理模型

### 2.1 Evidence 层

逐章阅读并核验，提取：

- 新人物与身份
- 关键行动与因果
- 境界、寿命、状态变化
- 系统规则与赠送/返还事件
- 法宝、丹药、功法的重要变化
- 地点、势力与关系变化
- 冲突、战斗及其结果

普通章节事实可只进入结构化证据记录或节点来源列表，不要求每章建立独立 Markdown。

### 2.2 Knowledge 层

当一个剧情阶段形成闭环后，生成一个 Timeline Node，并按需更新人物、系统、物品、世界观、境界或战斗档案。维护阶段的 audit、normalization、analysis 和 release Task 不得为了交付而创建空洞 Timeline Node。

## 3. 剧情节点边界

满足任一条件时，可结束当前节点：

- 一个主要冲突、任务或目标完成或发生明确转折；
- 主角进入新的地点、势力或行动阶段；
- 出现显著境界、身份、寿命、阵营或关系变化；
- 系统机制出现新的稳定规则；
- 发生对后续剧情有持续影响的重大赠送、返还、战斗或资源获取；
- 连续章节主题已明显切换。

不得仅因章节编号达到固定值强制切分。正文第 876 章后的内容不得继续使用正文 `NODE-*` 编号；番外使用 Workflow 约定的独立 extras scope。

## 4. 实体档案更新阈值

人物、物品、系统等档案采用增量更新。仅在出现长期有效的实质变化时更新，例如：

- 人物：首次登场、身份/阵营变化、境界变化、寿命变化、关键关系变化、长期能力变化；
- 物品：首次出现、获得或易主、品阶/能力确认、损毁或消耗、剧情功能显著改变；
- 系统：新增规则、倍率机制、触发条件、限制条件或已验证例外；
- 世界：新势力、新地点、权力结构或稳定世界规则；
- 战斗：影响人物状态、势力格局、关键资源或后续主线的战斗。

纯重复描述、短暂情绪、普通对话和一次性动作不单独更新实体档案。

### 4.1 人物成长事件持续记录

- 人物成长线采用“追加事件 + 阶段聚合”模型，不在 Markdown 中手工维护第二份事实。
- 自 `RUN-0082` 起，剧情 Run 中每个具有实质变化的人物更新必须追加 `growth_event_add`。
- 每条成长事件至少包含时间（`node`、`chapter` 或 `chapter_range`）、关键事件 `event`，以及核心能力变化或长期影响之一。
- 推荐字段：`core_ability`、`ability_change`、`impact`、`result`、`status`。
- 新人物必须具有 `first_appearance.chapter` 和 `first_appearance.node`，其首次登场自动进入成长线。
- 历史 Run 不强制回写；生成器依据既有扩展字段、Timeline Node 和来源章节重建历史阶段事件。无法定位精确单章时，只标注节点范围，不伪造精确时间。

## 5. Task、Run 与 Commit 标准

- 支持的 Task 类型：`story_arc`、`audit`、`data_quality`、`normalization`、`analysis`、`release`、`extras`。
- 一个 `story_arc` Task 对应一个完整剧情阶段，而不是单章；维护 Task 对应一个边界清晰、可复验的维护交付。
- 每次 Run 只执行唯一下一项 `pending` Task。后续 Task 可设为 `planned` 并通过 `depends_on` 排队。
- 每个 Run 使用新的 Run ID；不得复用已完成的 Task、Run、Timeline Node 或实体 ID。
- 一个 Task 完成后在目标分支形成一个完整业务 Git Commit。
- 剧情 Commit 应同时包含 Timeline Node、必要实体增量、结构化索引和 Project OS 状态；维护 Commit 应包含审计/修复、门禁、控制面和可复验产物定义。
- 禁止为同一任务拆成大量仅更新单文件的目标分支提交。
- “一个完整 Git Commit”约束目标分支最终历史。应从已核验的 `main` HEAD 建立临时分支，经 PR 全门禁后 squash merge。
- 合并前必须再次校验 Base SHA、目标分支和并发 Project OS Run；失败则登记 blocker，不得强推覆盖。
- `data/generated/` 与实体 Markdown 是自动物化视图，GitHub Actions 的后续刷新提交不视为拆分业务 Task；其内容必须可由同一 Task 的 canonical 增量完整重建。

## 6. 输出要求

剧情阶段至少包含：覆盖章节、原创摘要、关键因果、人物状态、系统/物品/势力/战斗增量、来源核验、未决问题。维护任务至少包含：范围、方法、机器可读结果、主要发现、修复、门禁、blocker、下一唯一 pending Task 和复现命令。

## 7. 质量门禁

提交前检查：

- Source traceability
- Arc or audit coherence
- Materiality
- Cross-index consistency
- Duplicate-work check
- YAML structure
- Entity-document freshness
- Entity-document readability
- Character identity alignment
- Character growth continuity
- Growth temporal accuracy
- Copyright boundary
- Project OS metrics consistency
- Audit reproducibility
- Final-state consistency
- Pending/conflict accounting

审计和规范化阶段还应检查 alias identity consistency、dead-character active-state consistency、artifact ownership conservation、gift participant resolution、gift component disposition、gift-to-artifact linkage completeness、relationship state transition validity、cultivation chronology 和 system-capability chronology。启发式候选必须作为 findings，不得无证据自动改写事实。

失败的门禁必须修复或写入 blocker；不得跳过、强制合并或把部分检查描述为全部通过。

## 8. 当前迁移规则

- `NODE-0001` 至 `NODE-0003` 作为早期细粒度历史节点保留。
- 自 `TASK-0006` 起采用剧情阶段标准。
- 正文主线已完成至第 876 章；后续默认进入 maintenance 模式。
- 番外采用独立 `scope: extras` 和独立 Task/Run/Node 命名空间，且在 v1.0 审计完成前不优先处理。

## 9. Canonical index maintenance

结构化数据采用基础索引、追加扩展和生成索引三层模型。

- 每个剧情 Task 继续把新增记录和既有实体更新写入 `data/extensions/`。
- `data/generated/` 是基础索引与全部扩展合并后的机器可消费完整视图，不得手工修改。
- 修正必须进入基础索引或 append-only extension；不得把自动生成文档作为事实源。
- 提交前必须运行：

```bash
python scripts/knowledge_base.py validate
python scripts/knowledge_base.py build
python scripts/knowledge_base.py validate --generated-dir data/generated
python scripts/validate_entity_identity.py --generated-dir data/generated
python scripts/render_character_growth.py --validate-continuity --effective-run 82
python scripts/normalize_repository.py --generated-dir data/generated --output-root .
```

- 校验覆盖 YAML、ID、Timeline、文档和证据路径、跨索引引用、人物名称/档案路径、成长事件、规范化处置和 Project OS 统计。
- GitHub Actions 在 `main` 更新后刷新生成索引，并每周将扩展合并回基础索引。
- compaction 不删除扩展文件；扩展继续作为不可变 Run 审计记录。

## 10. Entity document materialization

`docs/02-characters/` 和 `docs/06-artifacts/` 是 canonical 索引的人类可读完整投影，不是独立手工事实源。

- 每个 canonical 人物和物品必须对应一个 Markdown 文档。
- 人物档案依次呈现：一览、身份与阵营、修为/能力/成长、关系与立场、资源与物品、关键经历、成长线、来源与核验、未决事项。
- 成长线包含按 50 章窗口聚合的阶段画像，以及按时间排序的持续记录。
- 物品档案依次呈现：一览、获取/持有/流转、能力、使用与战斗、数量与当前状态、来源与核验、未决事项。
- 当前境界、年龄、寿命等摘要优先采用最新 `*_change` 值。
- 完整来源和 canonical YAML 放入默认折叠的审计附录。
- `_INDEX.md` 提供人物当前境界/势力和物品类别/品阶/持有状态。
- `scripts/render_entity_docs.py` 生成基础文档，`scripts/render_character_growth.py` 插入成长线。
- `docs/entity-docs-manifest.yaml` 记录生成器、模式、统计、canonical 来源和 ID→路径映射。

## 11. Maintenance、audit 与 release

- 正文完成状态拆分为 `story_status`、`project_status` 和 `release_status`；新增字段保持对既有 Schema 的向后兼容。
- 全库审计由 `scripts/full_repository_audit.py` 从 canonical indexes 自动生成，至少产出：
  - `docs/08-analysis/full-repository-audit.md`
  - `docs/08-analysis/verification-debt.md`
  - `docs/08-analysis/v1-baseline-statistics.md`
  - `data/audits/run-0125.yaml`
  - `RELEASE_NOTES_v1.0.0.md`
- v1 基线记录业务 Commit、内容树 SHA-256、统计、门禁和核验债务；冻结后不随后续维护自动改写。
- `verified`、`partial`、`pending`、`conflict`、`inferred` 必须分开统计；“官方直接核验至第 16 章”不得被误解为后续章节未经正文阅读。
- GitHub Release 只有在所有门禁通过且通过 GitHub 实际验证后才能标记创建成功。连接器没有 tag/release 写能力时，必须登记 blocker 并保留完整 Release Notes，不得虚构发布。
- 合并后必须验证 generated canonical indexes、人物/物品档案、manifest、审计基线、规范化报告和终局快照的自动物化提交。

## 12. Identity、Gift 与 Artifact 规范化

### 12.1 Identity relation

- 人物身份关系使用 `identity_resolution` 追加记录表达，不再只依赖“合并/不合并”二元判断。
- 支持 `same_person`、`alias`、`reincarnation_identity`、`inherited_identity`、`distinct_same_name` 和 `unresolved`。
- 关系记录必须包含对端 ID 或原始 label、关系类型、证据状态；时间化身份应包含 `effective_chapter` 或 `effective_chapter_range`。
- 重复建档不得删除历史 ID；使用 `record_status: superseded` 和 `canonical_character_id` 指向主记录，生成分析时默认排除 superseded 记录。
- 名字相似、称号相近或剧情猜测不能单独证明身份关系。

### 12.2 Gift participant and component disposition

- Gift 保留原始 `recipient` 文本，同时使用 `participant_resolution` 保存 `recipient_refs`、解析类型、状态及未决原因。
- 群体受赠者可使用 `collective` 或 `partially_resolved_collective`，不得为未知成员伪造人物 ID。
- 赠礼和返还按组件处置：唯一命名物品可链接 Artifact；丹药批次、货币、灵石、泛化法器组和综合礼单可分类为资源，不强制创建 Artifact。
- “完成处置”表示每个候选都有明确分类或未决原因，不等同于全部建立 Artifact 链接。

### 12.3 Artifact lifecycle ledger

- Artifact 的获得、转移、使用、消耗和损毁使用 append-only `lifecycle_event` 表达。
- 记录进入 `consumed` 或 `destroyed` 后，不得继续保留 active `current_holder`；历史持有人写入 `former_holder` 或事件的 `previous_holder`。
- 同名消耗品可通过 `artifact_type_key` 与不同 `batch_id` 表达同类型不同批次，不因同名强制合并。
- `data/generated/final-state.yaml` 由 canonical indexes 派生，不得作为新的手工事实源。
