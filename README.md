# return

《万倍返还，年迈的我去当舔狗》结构化知识库。

本仓库用于管理全书剧情时间线、人物成长、系统返还、境界变化、势力演化、法宝神通、战斗记录与来源核验。

## 项目目标

- 以剧情阶段而非单章为主线，建立稳定、可维护的剧情节点。
- 第一阶段第 1—50 章预计整理为约 8—12 个剧情阶段节点；后续按实际剧情密度动态调整。
- 建立章节证据、人物、系统、境界、势力和物品之间的交叉索引。
- 所有重要结论均保留来源与核验状态。
- 区分正文事实、上下文推断、来源冲突和待核实内容。

## 工作标准

- 章节是证据单元，不默认一章一个 Timeline Node。
- 一个剧情节点通常覆盖约 5—10 章，以冲突闭环、目标转换或重大状态变化为边界。
- 人物、物品和系统档案只在出现长期有效的实质变化时增量更新。
- 一个 Task 对应一个完整剧情阶段，并以一个完整 Git Commit 交付。
- 详细规范见 `docs/00-project/WORKFLOW.md`。

## 目录

- `docs/00-project/`：项目规范、路线图与术语表
- `docs/01-timeline/`：剧情节点与总时间线
- `docs/02-characters/`：人物档案
- `docs/03-system/`：系统与返还记录
- `docs/04-world/`：世界观、地点与势力
- `docs/05-realms/`：境界体系与成长轨迹
- `docs/06-artifacts/`：法宝、丹药、功法与神通
- `docs/07-battles/`：战斗记录
- `docs/08-analysis/`：专题分析
- `data/`：结构化 YAML 数据
- `data/extensions/`：不可变追加记录与增量补丁
- `data/generated/`：由脚本生成的完整 canonical indexes
- `scripts/`：索引聚合与一致性校验工具
- `templates/`：统一文档模板
- `sources/`：来源索引与核验说明

## 结构化索引

仓库采用三层索引模型：

1. `data/timeline/`、`data/characters/`、`data/system/`、`data/artifacts/` 保存周期性压缩后的基础索引；
2. `data/extensions/` 保存每次 Run 的追加记录和对既有实体的增量更新；
3. `data/generated/` 将基础索引与全部扩展实时合并，是外部程序默认应读取的完整索引。

本地生成和校验：

```bash
python -m pip install PyYAML==6.0.2
python scripts/knowledge_base.py build
python scripts/knowledge_base.py validate --generated-dir data/generated
```

`Knowledge Base CI` 会检查 YAML、全局 ID、跨索引引用、Timeline 区间及 Project OS 统计，并在 `main` 更新后刷新 `data/generated/`。任何改变 canonical data 的 `main` 提交都会触发这一重建流程。`Compact Base Indexes` 每周将扩展安全合并回基础索引；扩展文件继续保留为增量审计记录。

## 核验状态

- `verified`：正文直接确认
- `partial`：仅部分字段得到确认
- `inferred`：根据上下文推断
- `conflict`：来源之间存在冲突
- `pending`：尚未核实

## 当前阶段

项目进度以 `.project/STATE.yaml` 和 `.project/DASHBOARD.md` 为准；README 不再手工复制易过期的章节进度数字。
