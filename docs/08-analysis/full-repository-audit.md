# 全库审计报告 — v1.0.0

- Run：`RUN-0125`；Task：`TASK-0111` (`audit`)
- 基线业务提交：`cd24ac05347e6d1aad5bff3ae3d48373cac1d7af`；审计日期：2026-07-29
- 范围：正文第 1—876 章及全部 canonical、extensions、generated views、实体文档和 Project OS 控制面。

## 结论

阻断项 **0** 个。正文仍以第 876 章为终点；本 Run 不创建 Timeline Node，也不接入番外。

| 指标 | 值 |
|---|---|
| 章节覆盖 | 1—876 |
| Timeline Nodes | 108 |
| 人物 | 235 |
| 赠送事件 | 259 |
| 物品 | 149 |
| Extension 文件 | 385 |
| 人物/物品文档 | 384 |

## 质量门禁

| Gate | 结果 | 摘要 |
|---|---|---|
| yaml_structure | passed | parsed_yaml_files=511 |
| canonical_rebuild | passed | four generated indexes compared to deterministic rebuild |
| global_id_uniqueness | passed | canonical_ids=751 |
| timeline_continuity | passed | nodes=108; coverage=1-876 |
| cross_index_consistency | passed | reference_errors=0 |
| extension_append_only_shape | warning | legacy_root_extension_filenames=21；legacy_multi_file_runs=17；accepted by historical extension contract: run_id ordering, deterministic rebuild and immutable retention are authoritative |
| project_os_metrics | passed | pending_tasks=['TASK-0112'] |
| entity_document_freshness | passed | documents=384 |
| character_identity_alignment | warning | focus identities not directly resolved: ['雪瑶仙帝', '天羽']；duplicate canonical names for review=7；focus matching uses canonical name and alias/identity fields only; name similarity never proves identity |
| character_growth_continuity | passed | — |
| dead_character_active_state | passed | — |
| gift_artifact_linkage | warning | gift party identity candidates=18；rows without exact Artifact-name match=25；links={'gift': 197, 'reward': 192}; pending_gift_rows=79 |
| artifact_ownership_lifecycle | warning | consumed/destroyed holder candidates=3；duplicate artifact names for review=3 |
| final_state_consistency | passed | main story remains closed at Chapter 876; extras excluded；three retained upgrade opportunities remain explicitly pending |
| verification_debt | passed | non-verified field occurrences=1464 |
| copyright_boundary | passed | reports contain structured facts, summaries, metadata and hashes only |
| audit_reproducibility | passed | extensions=0f36bd7e59cb9a0e59125432af14775b0d24ea04432477b0aff4fd8e47848169; canonical=d8bbe15fa8cb4d3145331e8c6979610bac13656224ae3988e65323d593d9d718; entity_docs=260f5d7437614453929c348a14f5beefcc9808ca874226afe15fc803345791eb |

## 重点人物

只按 canonical name、别名和身份字段直接匹配，绝不因名字相似自动合并。

| 身份 | 匹配 |
|---|---|
| 徐霄 | CHAR-0001 徐霄 (alive) |
| 姬雪 | CHAR-0002 姬雪 (alive) |
| 刘爱花 | CHAR-0032 刘爱花 (dead) |
| 雪瑶仙帝 | 未直接匹配，转入规范化复核 |
| 凤青玄 | CHAR-0045 凤青玄 (alive)；CHAR-0052 凤青玄 (alive)；CHAR-0055 凤青玄 (dead)；CHAR-0056 凤青玄 (dead) |
| 天羽 | 未直接匹配，转入规范化复核 |
| 天翎 | CHAR-0172 天翎 (alive) |
| 玄雪 | CHAR-0170 玄雪 (alive) |
| 凤溪 | CHAR-0199 凤溪 (alive) |
| 初殷 | CHAR-0222 初殷 (alive) |
| 龙九天 | CHAR-0198 龙九天 (alive) |
| 诸葛青天 | CHAR-0149 诸葛青天 (dead) |
| 独孤惊云 | CHAR-0156 独孤惊云 (dead) |
| 孔青 | CHAR-0177 孔青 (被徐霄击杀) |
| 天穹 | CHAR-0189 天穹 (被万妖仙宗高层击杀) |
| 黑神 | CHAR-0225 黑神 (dead) |
| 破玄 | CHAR-0226 破玄 (dead) |
| 冥法 | CHAR-0227 冥法 (dead) |
| 神无机 | CHAR-0235 神无机 (dead) |

## 主要发现

- 人物同名记录 7 组；死亡人物 active/current 字段候选 0 条。
- Gift 参与者身份候选 18 条；未能以自由文本直接匹配 Artifact 名称的 Gift 25 条。
- 同名 Artifact 3 组；生命周期候选 3 条。
- Timeline 空洞 0；重叠 0。

“官方页面直接核验至第 16 章”只描述一种证据渠道，不等于第 17—876 章未经正文阅读。仓库还使用用户归档正文、逐章 SHA-256、可读镜像、单一来源、上下文推断和正文冲突等证据类型。

## 可复现性

```text
extension_tree_sha256 = 0f36bd7e59cb9a0e59125432af14775b0d24ea04432477b0aff4fd8e47848169
canonical_tree_sha256 = d8bbe15fa8cb4d3145331e8c6979610bac13656224ae3988e65323d593d9d718
entity_docs_tree_sha256 = 260f5d7437614453929c348a14f5beefcc9808ca874226afe15fc803345791eb
```

唯一下一项 pending Task 为 `TASK-0112`；`TASK-0113` 保持 planned 并依赖 `TASK-0112`。
