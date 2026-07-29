# 核验债务清单 — v1.0.0

基线：`cd24ac05347e6d1aad5bff3ae3d48373cac1d7af`。

| 状态 | 字段出现次数 | 涉及记录数 |
|---|---|---|
| verified | 579 | 265 |
| partial | 1404 | 577 |
| pending | 59 | 54 |
| conflict | 0 | 0 |
| inferred | 1 | 1 |

统计只计算核验语义字段，不混入人物生死、Task 或物品生命周期状态。官方直接核验、归档正文阅读、逐章哈希、镜像交叉核验、单一来源、推断和正文冲突必须分别理解。第 17—876 章并非“未读”。

### partial

- `NODE-0005` — `timeline.NODE-0005.status`
- `NODE-0006` — `timeline.NODE-0006.status`
- `NODE-0007` — `timeline.NODE-0007.status`
- `NODE-0007` — `timeline.NODE-0007.conflict_events[0].status`
- `NODE-0007` — `timeline.NODE-0007.conflict_events[1].status`
- `NODE-0007` — `timeline.NODE-0007.conflict_events[2].status`
- `NODE-0007` — `timeline.NODE-0007.system_events[0].status`
- `NODE-0007` — `timeline.NODE-0007.system_events[1].status`
- `NODE-0008` — `timeline.NODE-0008.status`
- `NODE-0008` — `timeline.NODE-0008.conflict_events[0].status`
- `NODE-0008` — `timeline.NODE-0008.conflict_events[1].status`
- `NODE-0008` — `timeline.NODE-0008.system_events[0].status`
- `NODE-0008` — `timeline.NODE-0008.system_events[1].status`
- `NODE-0008` — `timeline.NODE-0008.system_events[2].status`
- `NODE-0008` — `timeline.NODE-0008.protagonist_state.status`
- `NODE-0009` — `timeline.NODE-0009.status`
- `NODE-0009` — `timeline.NODE-0009.conflict_events[0].status`
- `NODE-0009` — `timeline.NODE-0009.conflict_events[1].status`
- `NODE-0009` — `timeline.NODE-0009.system_events[0].status`
- `NODE-0009` — `timeline.NODE-0009.protagonist_state.status`
### pending

- `NODE-0082` — `timeline.NODE-0082.system_events[1].status`
- `NODE-0085` — `timeline.NODE-0085.system_events[1].redemption_status`
- `CHAR-0002` — `characters.CHAR-0002.cultivation.status`
- `CHAR-0006` — `characters.CHAR-0006.cultivation.status`
- `CHAR-0019` — `characters.CHAR-0019.luck_grade.status`
- `CHAR-0025` — `characters.CHAR-0025.luck_grade.status`
- `CHAR-0025` — `characters.CHAR-0025.base_return_multiplier.status`
- `CHAR-0028` — `characters.CHAR-0028.system_profile.status`
- `CHAR-0030` — `characters.CHAR-0030.cultivation.status`
- `CHAR-0034` — `characters.CHAR-0034.cultivation.status`
- `CHAR-0035` — `characters.CHAR-0035.cultivation.status`
- `CHAR-0035` — `characters.CHAR-0035.conflict.life_status`
- `CHAR-0044` — `characters.CHAR-0044.realm.status`
- `CHAR-0046` — `characters.CHAR-0046.status`
- `CHAR-0048` — `characters.CHAR-0048.cultivation.status`
- `CHAR-0050` — `characters.CHAR-0050.cultivation.status`
- `CHAR-0051` — `characters.CHAR-0051.cultivation.status`
- `CHAR-0052` — `characters.CHAR-0052.cultivation.status`
- `CHAR-0053` — `characters.CHAR-0053.system_profile.status`
- `CHAR-0058` — `characters.CHAR-0058.system_profile.status`
### conflict

- 无
### inferred

- `CHAR-0014` — `characters.CHAR-0014.possible_external_affiliation.status`

`TASK-0112` 不得通过无证据推断降低 pending；结局三次暂存升级机会继续保持 pending。
