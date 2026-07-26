# 剧情知识库工作标准

版本：2.1  
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
```

- 校验必须覆盖 YAML 解析、ID 唯一性、Timeline 区间、文档和证据引用、跨索引节点引用，以及 `.project/STATE.yaml` / `.project/METRICS.yaml` 统计一致性。
- GitHub Actions 在 `main` 更新后刷新生成索引，并每周将扩展合并回基础索引。
- compaction 不删除扩展文件；扩展文件继续作为每次 Run 的不可变审计记录。

## 10. Entity document materialization

`docs/02-characters/` 和 `docs/06-artifacts/` 是 canonical 索引的人类可读完整投影，不再作为独立手工事实源。

- 每个 canonical 人物和物品记录必须对应一个 Markdown 文档。
- 每份文档必须包含可读摘要和完整 canonical YAML 记录，确保追加扩展中的后续身份、境界、关系、持有状态、能力、来源章节、`pending` 字段和连续性警告不会遗漏。
- 文档由 `scripts/render_entity_docs.py` 生成；事实修正应写入基础索引或追加扩展，不得直接修改自动生成档案。
- `docs/entity-docs-manifest.yaml` 记录生成器、canonical 来源、记录数量和 ID 到文档路径的映射。
- 生成与复验命令：

```bash
python scripts/render_entity_docs.py --generated-dir data/generated
python scripts/render_entity_docs.py --generated-dir data/generated --check
```

- PR CI 必须从临时 canonical 索引生成并复验实体文档产物；`main` 刷新任务必须将生成索引、人物档案、物品档案和 manifest 一并提交。
- 自动刷新提交必须通过路径忽略避免递归触发工作流。
