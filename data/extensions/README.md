# Canonical extension indexes

历史 canonical indexes 保存在：

- `data/timeline/nodes.yaml`
- `data/characters/characters.yaml`
- `data/system/gifts.yaml`
- `data/artifacts/artifacts.yaml`

从 `RUN-0021` 起，新记录和对既有记录的增量更新可以写入 `data/extensions/`，避免每小时任务频繁重写大型历史 YAML。基础索引与尚未 compact 的扩展记录共同构成 canonical structured index。

## 写入规则

1. 每条扩展记录必须具有全局唯一的实体或事件 ID。
2. 新实体使用完整记录；既有实体优先使用 `update` 增量补丁。
3. 增量字段使用以下约定：
   - `field_add`：追加唯一值；
   - `field_remove`：删除指定值；
   - `field_set`：显式覆盖字段；
   - 嵌套 mapping：递归合并。
4. Markdown 档案、Timeline、证据文件与 YAML 必须引用相同 ID 和 verification state。
5. `.project/STATE.yaml` 与 `.project/METRICS.yaml` 的统计必须按物化后的完整索引计算。
6. 扩展文件是不可变增量审计记录；compaction 后仍保留，不得删除或改写。

## 读取规则

外部消费者不应只读取基础索引。默认读取 `data/generated/` 下的完整索引，或在本地运行：

```bash
python scripts/knowledge_base.py build
```

聚合器按 `run_id` 顺序应用扩展，按 ID 合并新记录与增量补丁。基础索引可包含：

```yaml
compacted_through_run: RUN-0042
```

出现该水位线时，聚合器跳过不晚于此 RUN 的扩展文件，只应用后续增量，防止 compact 后重复执行历史补丁。

生成结果随后通过：

```bash
python scripts/knowledge_base.py validate --generated-dir data/generated
```

## 自动维护

- `Knowledge Base CI`：PR 只执行测试、验证与临时物化，不修改 PR 分支；`main` 更新、手工触发和每小时校验时刷新 `data/generated/`。
- `Compact Base Indexes`：每周运行一次，也可手工触发。它生成带水位线的四份基础索引，验证后创建或刷新 `automation/base-index-compaction` PR，不直接推送 `main`。
- compaction PR 不包含 `data/generated/`。合并后由 `Knowledge Base CI` 基于新基础索引和水位线之后的扩展重新生成，因而不会覆盖 PR 等待期间新增的 RUN。
- compaction 是幂等操作：相同水位线重复执行不会再次应用已经 compact 的历史扩展。
