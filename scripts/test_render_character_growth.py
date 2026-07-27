#!/usr/bin/env python3
"""Tests for staged character growth lines and continuity validation."""
from __future__ import annotations
import tempfile
from pathlib import Path
import yaml
import render_character_growth as growth
import render_entity_docs as base

def write(path:Path,value:object)->None:
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(yaml.safe_dump(value,allow_unicode=True,sort_keys=False),encoding="utf-8")

def test_growth_rendering()->None:
 with tempfile.TemporaryDirectory() as t:
  root=Path(t); generated=root/"data/generated"; out=root/"output"
  write(generated/"timeline.yaml",{"nodes":[{"id":"NODE-0001","title":"首次返还","chapters":{"start":1,"end":3},"status":"verified"},{"id":"NODE-0002","title":"宗门成长","chapters":{"start":45,"end":52},"status":"partial"},{"id":"NODE-0066","title":"仙塔突破","chapters":{"start":500,"end":508},"status":"partial"}]})
  write(generated/"characters.yaml",{"updated_at":"2026-07-27","characters":[{"id":"CHAR-0001","name":"徐霄","status":"alive","role":"protagonist","documents":{"profile":"docs/02-characters/徐霄.md"},"first_appearance":{"chapter":1,"title":"万倍返还系统","node":"NODE-0001"},"cultivation":{"current":"炼气境"},"cultivation_change":"大乘三重","affiliations":["缥缈宗"],"source_chapters":[1,2,45,50,500,508],"related_nodes":["NODE-0001","NODE-0002","NODE-0066"]}]})
  write(generated/"artifacts.yaml",{"artifacts":[]})
  write(root/"data/extensions/characters/run-0002.yaml",{"run_id":"RUN-0002","character_updates":[{"id":"CHAR-0001","update":{"cultivation_change":"筑基境","power_change_add":["掌握地火之道"],"relationship_change_add":["成为宗门核心人物"],"related_nodes_add":["NODE-0002"],"source_chapters_add":[45,46,50,52]}}]})
  write(root/"data/extensions/characters/run-0080.yaml",{"run_id":"RUN-0080","character_updates":[{"id":"CHAR-0001","update":{"growth_event_add":[{"node":"NODE-0066","event":"打通天元仙塔一百层","core_ability":["大乘三重","三十二道鸿蒙真气","渡劫六重级肉身"],"impact":"形成渡劫后期级战略威慑","status":"partial"}],"cultivation_change":"大乘三重","related_nodes_add":["NODE-0066"],"source_chapters_add":list(range(500,509))}}]})
  outputs,manifest=growth.expected_files(root,out,generated); base.write(outputs,set())
  assert manifest["schema_version"]==3
  assert manifest["growth_line"]["temporal_accuracy"]=="no_backfill_from_merged_current_snapshot"
  profile=(out/"docs/02-characters/徐霄.md").read_text(encoding="utf-8")
  for value in ("## 成长线","### 阶段性画像","### 持续记录","首次登场时核心能力未形成独立历史快照","第 45—52 章","宗门成长","掌握地火之道","第 500—508 章","打通天元仙塔一百层","三十二道鸿蒙真气","NODE-0066 / RUN-0080"):
   assert value in profile
  first_block=profile[profile.index("首次登场：万倍返还系统"):profile.index("第 45—52 章")]
  assert "大乘三重" not in first_block
  assert profile.index("## 成长线")<profile.index("## 来源与核验")
  assert base.compare(outputs)==[]

def test_continuity_gate()->None:
 with tempfile.TemporaryDirectory() as t:
  root=Path(t)
  write(root/"data/extensions/timeline/run-0083.yaml",{"run_id":"RUN-0083","nodes":[{"id":"NODE-0067","chapters":{"start":509,"end":516}}]})
  path=root/"data/extensions/characters/run-0083.yaml"
  write(path,{"run_id":"RUN-0083","character_updates":[{"id":"CHAR-0001","update":{"cultivation_change":"大乘四重","related_nodes_add":["NODE-0067"],"source_chapters_add":[509,510]}}]})
  assert any("requires growth_event_add" in x for x in growth.validate(root))
  write(path,{"run_id":"RUN-0083","character_updates":[{"id":"CHAR-0001","update":{"cultivation_change":"大乘四重","growth_event_add":[{"node":"NODE-0067","event":"完成幽冥天绝阵反击","core_ability":"大乘四重与神魂能力强化","impact":"形成新的阴灵克制手段"}],"related_nodes_add":["NODE-0067"],"source_chapters_add":[509,510]}}]})
  assert growth.validate(root)==[]

def main()->int:
 test_growth_rendering(); test_continuity_gate(); print("character growth-line tests passed"); return 0
if __name__=="__main__":raise SystemExit(main())
