# Generated canonical indexes

此目录由 `scripts/knowledge_base.py` 自动生成，不应手工编辑。

它将历史基础索引与 `data/extensions/` 中的所有追加记录、增量更新合并为四份可直接消费的完整索引：

- `timeline.yaml`
- `characters.yaml`
- `gifts.yaml`
- `artifacts.yaml`

生成命令：

```bash
python -m pip install PyYAML==6.0.2
python scripts/knowledge_base.py build
python scripts/knowledge_base.py validate --generated-dir data/generated
```

GitHub Actions 会在 `main` 更新后重新生成并提交这些文件。基础索引仍可通过定期 compaction 刷新，扩展文件作为不可变的增量审计记录继续保留。
