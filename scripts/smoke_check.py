"""Static export integrity checks used before shipping."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
p=Path('web/public/demo/results.json'); data=json.loads(p.read_text(encoding='utf8'))
required={'aggregated','paired_comparisons','demo_scenarios','note','config'}
missing=required-set(data)
if missing: raise SystemExit(f'missing keys: {sorted(missing)}')
for row in data['aggregated']:
    metrics=row['metrics']
    if not {'total_distance','customers_served','evaluations','compute_time_s'} <= set(metrics): raise SystemExit('missing required metric')
    if row['strategy'] in {'greedy_insertion','insertion_2opt_star'} and metrics['evaluations']['mean'] <= 0: raise SystemExit('zero greedy or 2-opt* evaluations')
for dyn in sorted({x['dynamism'] for x in data['aggregated']}):
    served={x['metrics']['customers_served']['mean'] for x in data['aggregated'] if x['dynamism']==dyn}
    if len(served)>1: raise SystemExit(f'served counts differ at dynamism {dyn}; results table must display them')
result=subprocess.run(['rg','-rniE','placeholder|todo|would render|lorem','web/src'],capture_output=True,text=True)
if result.returncode==0: raise SystemExit(result.stdout)
if result.returncode not in (0,1): raise SystemExit(result.stderr)
print(f'smoke_check: PASS; aggregates={len(data["aggregated"])} paired_cells={len(data["paired_comparisons"])}')
