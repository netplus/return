#!/usr/bin/env python3
"""Add staged, append-only growth lines to generated character profiles."""
from __future__ import annotations
import argparse,re,sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml
import render_entity_docs as base
RUN_RE=re.compile(r"RUN-(\d+)")
GROWTH_KEYS=("growth_event_add","growth_events_add","growth_timeline_add")
META={"id","name","status","role","documents","document","verification_status","related_nodes","related_nodes_add","source_chapters","source_chapters_add","first_appearance",*GROWTH_KEYS}
ABILITY=("cultivation","power","ability","abilities","constitution","body","dao","hongmeng","array","tribulation","retained_spiritual_sense","condition","appearance","realm","essence")
OTHER=("affiliation","identity","identities","title","role","status","strategic_role","relationship","bond","attitude","enemy","conflict","protection","resource","accepted","artifact","gift","current_action","public_","travel_","reputation","strategic_","system_","major_","combat_","battle_")
@dataclass(frozen=True)
class Event:
 start:int; end:int; title:str; ability:str; impact:str; evidence:str; status:str
 @property
 def time(self): return f"第 {self.start} 章" if self.start==self.end else f"第 {self.start}—{self.end} 章"
def load(path:Path)->dict[str,Any]:
 try: v=yaml.safe_load(path.read_text(encoding="utf-8"))
 except (OSError,yaml.YAMLError) as e: raise RuntimeError(f"cannot read YAML {path}: {e}") from e
 if not isinstance(v,dict): raise RuntimeError(f"top-level YAML must be mapping: {path}")
 return v
def nodes(generated:Path)->dict[str,dict[str,Any]]:
 p=generated/"timeline.yaml"
 if not p.exists(): return {}
 return {str(x.get("id")):x for x in load(p).get("nodes",[]) if isinstance(x,dict) and x.get("id")}
def bounds(node:dict[str,Any]):
 c=node.get("chapters")
 return (c.get("start"),c.get("end")) if isinstance(c,dict) and isinstance(c.get("start"),int) and isinstance(c.get("end"),int) else None
def flatten(v:Any,limit=4)->str:
 if v is None:return "—"
 if isinstance(v,bool):return "是" if v else "否"
 if isinstance(v,dict):
  parts=[f"{base.label(str(k))}：{flatten(x,limit)}" for k,x in v.items() if x not in (None,"",[],{})]
  return "；".join(parts[:limit])+(f" 等 {len(parts)} 项" if len(parts)>limit else "")
 if isinstance(v,list):
  parts=[flatten(x,limit) for x in v if x not in (None,"",[],{})]
  return "；".join(parts[:limit])+(f" 等 {len(parts)} 项" if len(parts)>limit else "")
 return str(v)
def norm(k:str)->str:
 return k[:-4] if k.endswith("_add") else (k[:-4] if k.endswith("_set") else k)
def summary(update:dict[str,Any],prefixes:tuple[str,...],limit=4)->str:
 p=[]
 for k,v in update.items():
  n=norm(str(k))
  if k not in META and v not in (None,"",[],{}) and n.startswith(prefixes): p.append(f"{base.label(n)}：{flatten(v)}")
 return "；".join(p[:limit])+(f" 等 {len(p)} 项" if len(p)>limit else "")
def chapters(update:dict[str,Any])->list[int]:
 out=[]
 for k in ("source_chapters","source_chapters_add"):
  if isinstance(update.get(k),list):out += [x for x in update[k] if isinstance(x,int)]
 return sorted(set(out))
def related(update:dict[str,Any])->list[str]:
 out=[]
 for k in ("related_nodes","related_nodes_add"):
  if isinstance(update.get(k),list):out += [str(x) for x in update[k] if x]
 f=update.get("first_appearance")
 if isinstance(f,dict) and f.get("node"):out.append(str(f["node"]))
 return list(dict.fromkeys(out))
def event_from(update:dict[str,Any],run:str,node_id:str,node:dict[str,Any],new=False)->Event|None:
 b=bounds(node); ch=chapters(update)
 if not b and ch:b=(min(ch),max(ch))
 if not b:return None
 ability=summary(update,ABILITY) or "本阶段未记录新增核心能力"
 impact=summary(update,OTHER,5) or "该阶段未记录额外的身份、关系或资源变化"
 return Event(b[0],b[1],("首次登场：" if new else "")+str(node.get("title") or "角色成长与状态变化"),ability,impact," / ".join(x for x in (node_id,run) if x),base.status_text(node.get("status","partial")))
def explicit(update:dict[str,Any],run:str,nd:dict[str,dict[str,Any]])->list[Event]:
 raw=[]
 for k in GROWTH_KEYS:
  v=update.get(k); raw += v if isinstance(v,list) else ([v] if isinstance(v,dict) else [])
 out=[]
 for x in raw:
  if not isinstance(x,dict):continue
  nid=str(x.get("node") or ""); n=nd.get(nid,{})
  b=None
  if isinstance(x.get("chapter"),int):b=(x["chapter"],x["chapter"])
  elif isinstance(x.get("chapter_range"),dict):
   r=x["chapter_range"]
   if isinstance(r.get("start"),int) and isinstance(r.get("end"),int):b=(r["start"],r["end"])
  b=b or bounds(n)
  if not b:
   ch=chapters(update); b=(min(ch),max(ch)) if ch else None
  if not b:continue
  out.append(Event(b[0],b[1],str(x.get("event") or n.get("title") or "成长事件"),flatten(x.get("core_ability",x.get("ability_change"))) if x.get("core_ability",x.get("ability_change")) not in (None,"",[],{}) else "本阶段未记录新增核心能力",flatten(x.get("impact",x.get("result"))) if x.get("impact",x.get("result")) not in (None,"",[],{}) else (summary(update,OTHER,5) or "该阶段未记录额外影响")," / ".join(y for y in (nid,run) if y),base.status_text(x.get("status",n.get("status","partial")))))
 return out
def all_events(root:Path,generated:Path)->dict[str,list[Event]]:
 nd=nodes(generated); result={}; ext=root/"data/extensions/characters"
 for p in sorted(ext.glob("*.yaml")) if ext.exists() else []:
  d=load(p); run=str(d.get("run_id") or p.stem)
  entries=[]
  for x in d.get("characters",[]):
   if isinstance(x,dict): entries.append((dict(x.get("update") or x),not isinstance(x.get("update"),dict),x.get("id")))
  for x in d.get("character_updates",[]):
   if isinstance(x,dict) and isinstance(x.get("update"),dict):entries.append((dict(x["update"]),False,x.get("id")))
  for u,new,rid in entries:
   u.setdefault("id",rid); rid=str(u.get("id") or "")
   if not rid:continue
   ev=explicit(u,run,nd)
   if not ev:
    for nid in related(u):
     e=event_from(u,run,nid,nd.get(nid,{}),new)
     if e:ev.append(e)
   result.setdefault(rid,[]).extend(ev)
 return result
def first(record:dict[str,Any],nd:dict[str,dict[str,Any]])->Event|None:
 f=record.get("first_appearance")
 if not isinstance(f,dict) or not isinstance(f.get("chapter"),int):return None
 nid=str(f.get("node") or "")
 title=f"首次登场：{f.get('title') or nd.get(nid,{}).get('title') or record.get('name')}"
 ability="首次登场时核心能力未形成独立历史快照；不得使用后期合并字段倒推"
 impact="仅确认角色在该时间点进入剧情；身份、关系与资源变化从后续阶段记录读取"
 return Event(f["chapter"],f["chapter"],title,ability,impact,nid or "canonical first_appearance",base.status_text(record.get("verification_status",record.get("status","partial"))))
def esc(s:str)->str:return s.replace("|",r"\|").replace("\n","<br>")
def short(s:str,n=180)->str:return s if len(s)<=n else s[:n-1]+"…"
def table(events:list[Event])->list[str]:
 out=["| 时间 | 关键事件 | 核心能力与成长 | 身份、关系与资源影响 | 证据 / 状态 |","|---|---|---|---|---|"]
 for e in events:out.append(f"| {esc(e.time)} | {esc(short(e.title))} | {esc(short(e.ability))} | {esc(short(e.impact))} | {esc(e.evidence)}<br>{esc(e.status)} |")
 return out
def growth(events:list[Event])->str:
 events=sorted({(e.start,e.end,e.title,e.ability,e.impact,e.evidence,e.status):e for e in events}.values(),key=lambda e:(e.start,e.end,e.evidence))
 buckets={}
 for e in events:buckets.setdefault((max(e.start,1)-1)//50,[]).append(e)
 lines=["## 成长线","","> 采用“阶段性画像 + 持续记录”：阶段画像总结长期变化，持续记录按每次 Project OS Run 追加关键事件、核心能力变化与时间证据。历史能力只在对应 Run 或节点有明确记录时进入时间线。","","### 阶段性画像","","| 时间 | 阶段关键事件 | 核心能力演进 | 阶段影响 |","|---|---|---|---|"]
 for items in buckets.values():
  s,e=min(x.start for x in items),max(x.end for x in items); title="<br>".join(dict.fromkeys(short(x.title,100) for x in items[-3:])); ab="<br>".join(dict.fromkeys(short(x.ability,120) for x in items[-4:] if not x.ability.startswith("本阶段未记录"))) or "—"; imp="<br>".join(dict.fromkeys(short(x.impact,120) for x in items[-3:]))
  lines.append(f"| 第 {s}—{e} 章 | {esc(title)} | {esc(ab)} | {esc(imp)} |")
 lines += ["","### 持续记录",""]
 if len(events)>8: lines += ["<details>",f"<summary>查看较早成长记录（{len(events)-8} 条）</summary>","",*table(events[:-8]),"","</details>","","#### 最近记录","",*table(events[-8:])]
 else: lines += table(events)
 return "\n".join(lines)+"\n"
def expected_files(root:Path,out:Path,generated:Path):
 outputs,manifest=base.expected_files(root,out,generated); chars=load(generated/"characters.yaml").get("characters",[]); nd=nodes(generated); by=all_events(root,generated); paths={str(x.get("id")):str(x.get("path")) for x in manifest["groups"]["characters"]["documents"]}; count=total=0
 for r in chars:
  if not isinstance(r,dict):continue
  rid=str(r.get("id") or ""); ev=list(by.get(rid,[])); f=first(r,nd)
  if f:ev.append(f)
  if not ev:continue
  p=out/paths[rid]; outputs[p]=outputs[p].replace("## 来源与核验",growth(ev)+"\n## 来源与核验",1); count+=1; total+=len(ev)
 manifest.update(schema_version=3,generator="scripts/render_character_growth.py",presentation="reader_friendly_with_staged_growth_line_and_collapsed_canonical_appendix",growth_line={"mode":"stage_summary_plus_append_only_run_history","stage_window_chapters":50,"characters_with_growth_line":count,"growth_events":total,"temporal_accuracy":"no_backfill_from_merged_current_snapshot","source":"data/extensions/characters + data/generated/timeline.yaml"}); outputs[out/base.MANIFEST_PATH]=base.dump_yaml(manifest)+"\n"; return outputs,manifest
def meaningful(u:dict[str,Any])->bool:return any(k not in META and v not in (None,"",[],{}) for k,v in u.items())
def validate(root:Path,effective=83)->list[str]:
 errors=[]; cr=root/"data/extensions/characters"; tr=root/"data/extensions/timeline"
 for p in sorted(cr.glob("run-*.yaml")) if cr.exists() else []:
  d=load(p); m=RUN_RE.search(str(d.get("run_id") or p.name)); n=int(m.group(1)) if m else -1
  if n<effective or not (tr/p.name).exists():continue
  for group in ("character_updates","characters"):
   for i,x in enumerate(d.get(group,[])):
    if not isinstance(x,dict):continue
    u=x.get("update") if isinstance(x.get("update"),dict) else x
    if group=="characters" and not isinstance(x.get("update"),dict):
     f=x.get("first_appearance")
     if not isinstance(f,dict) or not isinstance(f.get("chapter"),int) or not f.get("node"):errors.append(f"{p}:{group}[{i}] new character requires first_appearance.chapter and node")
    elif meaningful(u) and not any(u.get(k) not in (None,"",[],{}) for k in GROWTH_KEYS):errors.append(f"{p}:{group}[{i}]({x.get('id','UNKNOWN')}): material story update requires growth_event_add")
  for group in ("character_updates","characters"):
   for i,x in enumerate(d.get(group,[])):
    if not isinstance(x,dict):continue
    u=x.get("update") if isinstance(x.get("update"),dict) else x
    for k in GROWTH_KEYS:
     v=u.get(k); items=v if isinstance(v,list) else ([v] if isinstance(v,dict) else [])
     for j,item in enumerate(items):
      if not isinstance(item,dict) or not (isinstance(item.get("chapter"),int) or item.get("node") or item.get("chapter_range")):errors.append(f"{p}:{group}[{i}].{k}[{j}] requires time")
      if not isinstance(item,dict) or not isinstance(item.get("event"),str) or not item.get("event").strip():errors.append(f"{p}:{group}[{i}].{k}[{j}] requires event")
      if isinstance(item,dict) and not any(item.get(q) not in (None,"",[],{}) for q in ("core_ability","ability_change","impact","result")):errors.append(f"{p}:{group}[{i}].{k}[{j}] requires core ability or impact")
 return errors
def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",type=Path,default=Path.cwd()); ap.add_argument("--generated-dir",type=Path,default=Path("data/generated")); ap.add_argument("--output-root",type=Path,default=Path(".")); ap.add_argument("--check",action="store_true"); ap.add_argument("--validate-continuity",action="store_true"); ap.add_argument("--effective-run",type=int,default=83); a=ap.parse_args(); root=a.repo_root.resolve()
 try:
  if a.validate_continuity:
   errors=validate(root,a.effective_run)
   if errors:
    for e in errors:print("ERROR:",e,file=sys.stderr)
    return 1
   print(f"character growth continuity is valid from RUN-{a.effective_run:04d}"); return 0
  generated=a.generated_dir if a.generated_dir.is_absolute() else root/a.generated_dir; out=a.output_root if a.output_root.is_absolute() else root/a.output_root; outputs,m=expected_files(root,out,generated)
  if a.check:
   errors=base.compare(outputs)
   if errors:
    for e in errors:print("ERROR:",e,file=sys.stderr)
    return 1
  else:base.write(outputs,base.prior_managed_paths(out))
  print(f"growth-line entity documents current: {m['growth_line']['characters_with_growth_line']} characters, {m['growth_line']['growth_events']} events"); return 0
 except (OSError,RuntimeError,yaml.YAMLError) as e:print("ERROR:",e,file=sys.stderr); return 1
if __name__=="__main__":raise SystemExit(main())
