# 编写与核验规范

## 1. 基本原则

1. 不把推断写成事实。
2. 不依赖单一搜索摘要代替正文。
3. 每个关键结论必须关联章节或可追溯来源。
4. 节点编号一经发布保持稳定。
5. 摘要使用原创表述，避免大段复制正文。

## 2. 节点编号

统一使用四位编号：

- `NODE-0001`
- `NODE-0002`
- `NODE-0002A`：仅用于后续插入且不能重排既有编号的情况

## 3. 核验状态

- `verified`：相关字段由正文直接确认
- `partial`：事件存在，但章节、数值或细节未完全确认
- `inferred`：基于上下文的合理推断
- `conflict`：不同版本或来源相互矛盾
- `pending`：尚未检查正文

核验状态应精确到字段；不能因为一个节点中部分内容已确认，就把整个节点全部标为 `verified`。

## 4. 来源格式

每条来源至少记录：

- 章节号
- 章节标题（如可确认）
- 支持的具体字段
- 来源类型
- 核验日期

不在仓库中保存未经授权的整章正文。

## 5. Git 提交规范

推荐格式：

- `docs(timeline): add nodes 0001-0005`
- `data(gifts): record returns from chapters 1-20`
- `verify(chapters): validate chapters 21-30`
- `fix(character): correct first appearance of <name>`
- `refactor(schema): normalize source references`

## 6. 内容边界

事实层和分析层分离：

- `docs/01-timeline` 等目录记录可核验事实。
- `docs/08-analysis` 可包含解释、评价和推演，但必须清楚标明分析性质。
