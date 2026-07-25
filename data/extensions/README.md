# Canonical extension indexes

历史 canonical indexes 保存在：

- `data/timeline/nodes.yaml`
- `data/characters/characters.yaml`
- `data/system/gifts.yaml`
- `data/artifacts/artifacts.yaml`

从 `RUN-0021` 起，新记录和对既有记录的增量更新可以写入 `data/extensions/`，避免每小时任务频繁重写大型历史 YAML。基础索引与全部扩展记录共同构成 canonical structured index。

## 写入规则

1. 每条扩展记录必须具有全局唯一的实体或事件 ID。
2. 新实体使用完整记录；既有实体优先使用 `update` 增量补丁。
3. 增量字段使用以下约定：
   - `field_add`：追加唯一值；
   - `field_remove`：删除指定值；
   - `field_set`：显式覆盖字段；
   - 嵌套 mapping：递归合并。
4. Markdown 档案、Timeline、证据文件与 YAML 必须引用相同 ID 和 verification state。
5. `.project/STATE.yaml` 与 `.project/METRICS.yaml` 的统计必须按基础索引与扩展索引合并后的结果计算。
6. 扩展文件是增量审计记录；compaction 后仍保留，不得因基础索引已合并而删除。

## 读取规则

外部消费者不应只读取基础索引。默认读取 `data/generated/` 下的完整索引，或在本地运行：

```bash
python scripts/knowledge_base.py build
```

聚合器按 `run_id` 顺序应用扩展，按 ID 合并新记录与增量补丁。生成结果随后通过：

```bash
python scripts/knowledge_base.py validate --generated-dir data/generated
```

## 自动维护

- `Knowledge Base CI`：每次 PR 和 `main` 更新时进行独立一致性校验；`main` 更新后自动刷新 `data/generated/`。
- `Compact Base Indexes`：每周运行一次，将完整合并结果写回四份基础索引；也可通过 `workflow_dispatch` 手工执行。
- compaction 是幂等操作：扩展文件保留后再次聚合不会重复创建记录，而是按 ID 合并。
