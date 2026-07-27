# 剧情知识库工作标准

版本：2.4  
生效范围：自第 4 章起；第 1—3 章既有节点保留，不回溯拆改。

## 1. 核心原则

- 正文章节是证据单元，不再默认等同于剧情节点。
- Timeline 以剧情阶段（story arc）为基本单元，一个节点通常覆盖约 5—10 章。
- 章节范围可伸缩；优先保证剧情闭环，不机械追求固定章数。
- 所有进入知识层的重要事实必须能追溯到官方正文来源。
- 不保存整章正文，只保存原创摘要、事实字段和来源索引。

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

当一个剧情阶段形成闭环后，生成一个 Timeline Node，并按需更新人物、系统、物品、世界观、境界或战斗档案。

## 3. 剧情节点边界

满足任一条件时，可结束当前节点：

- 一个主要冲突、任务或目标完成或发生明确转折；
- 主角进入新的地点、势力或行动阶段；
- 出现显著境界、身份、寿命、阵营或关系变化；
- 系统机制出现新的稳定规则；
- 发生对后续剧情有持续影响的重大赠送、返还、战斗或资源获取；
- 连续章节主题已明显切换。

不得仅因章节编号达到某个固定值而强制切分。

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
- 每条成长事件至少包含：时间（`node`、`chapter` 或 `chapter_range`）、关键事件 `event`，以及核心能力变化或长期影响之一。
- 推荐字段：`core_ability`、`ability_change`、`impact`、`result`、`status`。
- 新人物必须具有 `first_appearance.chapter` 和 `first_appearance.node`，其首次登场自动进入成长线。
- 历史 Run 不强制回写；生成器依据既有扩展字段、Timeline Node 和来源章节重建历史阶段事件。无法定位到精确单章时，只标注剧情节点章节范围，不伪造精确时间。

## 5. Task 与 Commit 标准

- 一个 Task 对应一个完整剧情阶段，而不是单章。
- 默认目标范围约 5—10 章，可根据剧情边界提前结束或继续扩展。
- 一个 Task 完成后产生一个完整 Git Commit。
- Commit 应同时包含：Timeline Node、必要的实体增量、结构化索引以及 Project OS 状态更新。
- 禁止为同一剧情阶段拆成大量仅更新单文件的碎片提交。
- “一个完整 Git Commit”约束的是目标分支最终历史，而不是中间传输方式。当 Git Data API 无法提供基础 Tree SHA 时，不得以 Commit SHA 冒充 Tree SHA；应从已核验的目标分支 HEAD 创建临时分支，完成全部文件写入后通过 squash merge 形成目标分支上的单一提交。
- 使用临时分支回退路径时，必须在合并前校验目标分支未产生冲突性 Project OS Run，并以预期 Head SHA 执行合并；失败则登记 blocker，不得强推覆盖。
- `data/generated/` 与实体 Markdown 是自动物化视图，GitHub Actions 的后续刷新提交不视为拆分业务 Task；其内容必须可由同一 Task 的 canonical 增量完全重建。

## 6. 输出要求

每个剧情阶段至少应包含：

1. 覆盖章节范围；
2. 原创剧情摘要；
3. 关键因果链；
4. 主要人物与状态变化；
5. 系统、物品、境界、势力或战斗的重要增量；
6. 官方正文来源与核验状态；
7. 未决问题与禁止推断字段。

## 7. 质量门禁

提交前检查：

- Source traceability：重要事实可追溯到具体章节；
- Arc coherence：节点形成完整或合理阶段；
- Materiality：只登记具有长期价值的变化；
- Cross-index consistency：Markdown 与 YAML 索引一致；
- Duplicate-work check：避免重复节点和重复实体记录；
- Entity-document freshness：人物与物品 Markdown 能从最新 canonical 索引完整重建，数量、ID 和完整记录不得缺失；
- Entity-document readability：读者首先看到简洁概览和按主题组织的事实；复杂机器字段不得压缩为单行代码；长来源列表和完整 YAML 必须默认折叠；摘要应优先采用最新 `*_change` 当前值；
- Character identity alignment：具有显式人物档案路径的 canonical 记录，其 `name` 必须与档案文件名一致；不允许一个 ID 的名称被另一人物覆盖；
- Character growth continuity：人物档案必须包含时间化成长线；自 `RUN-0082` 起，每个实质人物更新必须追加结构化成长事件；阶段画像和持续记录必须可从 append-only 扩展重建；
- Copyright boundary：不保存大段或整章原文。

## 8. 当前迁移规则

- `NODE-0001` 至 `NODE-0003` 作为早期细粒度历史节点保留。
- 自 `TASK-0006` 起采用本标准。
- 下一任务覆盖第 4 章起的首个完整剧情阶段，暂定探索窗口为第 4—10 章；最终结束章节由剧情边界决定。

## 9. Canonical index maintenance

结构化数据采用三层模型：基础索引、追加扩展和生成索引。

- 每个剧情 Task 继续把新增记录和既有实体更新写入 `data/extensions/`。
- `data/generated/` 是基础索引与全部扩展合并后的机器可消费完整视图，不得手工修改。
- 提交前必须运行：

```bash
python scripts/knowledge_base.py validate
python scripts/knowledge_base.py build
python scripts/knowledge_base.py validate --generated-dir data/generated
python scripts/validate_entity_identity.py --generated-dir data/generated
python scripts/render_character_growth.py --validate-continuity --effective-run 82
```

- 校验必须覆盖 YAML 解析、ID 唯一性、Timeline 区间、文档和证据引用、跨索引节点引用、人物名称与显式档案路径一致性、人物成长事件持续性，以及 `.project/STATE.yaml` / `.project/METRICS.yaml` 统计一致性。
- GitHub Actions 在 `main` 更新后刷新生成索引，并每周将扩展合并回基础索引。
- compaction 不删除扩展文件；扩展文件继续作为每次 Run 的不可变审计记录。

## 10. Entity document materialization

`docs/02-characters/` 和 `docs/06-artifacts/` 是 canonical 索引的人类可读完整投影，不再作为独立手工事实源。

- 每个 canonical 人物和物品记录必须对应一个 Markdown 文档。
- 人物档案应依次呈现：一览、身份与阵营、修为/能力/成长、关系与立场、资源与物品、关键经历、成长线、来源与核验、未决与注意事项。
- 成长线包含两层：阶段性画像和持续记录。
  - 阶段性画像默认按 50 章窗口聚合，展示阶段关键事件、核心能力演进与长期影响。
  - 持续记录按时间排序，至少展示时间、关键事件、核心能力与成长、身份/关系/资源影响、证据与核验状态。
  - 记录超过 8 条时，较早记录默认折叠，最近记录直接展示。
- 物品档案应依次呈现：一览、获取/持有/流转、能力与效果、使用与战斗记录、数量与当前状态、来源与核验、未决与注意事项。
- 概览只放当前关键结论，复杂字典和长列表必须转换为分层 Markdown，不得以反引号包裹的单行 YAML 代替读者文本。
- 当前境界、年龄、寿命等摘要字段应优先采用最新 `cultivation_change`、`age_change`、`lifespan_change` 等变更值，再回退到基础字段。
- 来源章节与关联节点在正文中只显示数量和范围，完整列表放入折叠区。
- 完整 canonical YAML 仅作为文末默认折叠的审计附录；日常阅读不应被机器记录打断。
- `_INDEX.md` 应展示人物当前境界和主要势力，或物品类别、品阶和持有状态，方便读者快速筛选。
- 基础读者文档由 `scripts/render_entity_docs.py` 生成；成长线由 `scripts/render_character_growth.py` 在同一物化过程中插入。事实修正应写入基础索引或追加扩展，不得直接修改自动生成档案。
- `docs/entity-docs-manifest.yaml` 记录生成器、呈现模式、成长线统计、canonical 来源、记录数量和 ID 到文档路径的映射。
- 生成与复验命令：

```bash
python scripts/render_character_growth.py --generated-dir data/generated
python scripts/render_character_growth.py --generated-dir data/generated --check
```

- PR CI 必须从临时 canonical 索引生成并复验实体文档及成长线产物；`main` 刷新任务必须将生成索引、人物档案、物品档案和 manifest 一并提交。
- 自动刷新提交必须通过路径忽略避免递归触发工作流。
