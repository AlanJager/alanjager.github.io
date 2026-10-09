from pathlib import Path
import re,json,csv,hashlib
root=Path(__file__).resolve().parent;src=root/'traces';rows=[]
for case in ['cram_readwrite','zram_readwrite','cram_direct','zram_direct']:
 for phase in ['enter','read','write']:
  p=src/f'{case}-{phase}-trace.txt'
  if not p.exists():continue
  stacks={};seq=0
  for line in p.read_text().splitlines():
   if '|' not in line:continue
   m=re.match(r'\s*(\d+)\)',line)
   if not m:continue
   cpu=int(m[1]);stack=stacks.setdefault(cpu,[]);call=line.rsplit('|',1)[1].strip();dt=re.search(r'(\d+\.\d+) us',line)
   if call.endswith('() {'):
    stack.append((call[:-4].rstrip('('),seq));seq+=1
   elif call=='}':
    assert stack,(p,line)
    name,order=stack.pop();assert dt,(p,line)
    rows.append(dict(case=case,phase=phase,cpu=cpu,name=name,inclusive_us=float(dt[1]),depth=len(stack),order=order))
   elif call.endswith('();') and dt:
    rows.append(dict(case=case,phase=phase,cpu=cpu,name=call[:-3].rstrip('('),inclusive_us=float(dt[1]),depth=len(stack),order=seq));seq+=1
  assert all(not st for st in stacks.values()),p
with (root/'functions.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
selected=['cram_migrate_to','__swap_writepage','handle_mm_fault','cram_handle_fault','migrate_pages','alloc_cram_folio','alloc_cram_promote_folio','folio_mc_copy','do_swap_page','swap_read_folio','zram_submit_bio','zcomp_compress','zcomp_decompress','lz4_compress','lz4_decompress','remove_migration_ptes','try_to_migrate','lru_add_drain_all']
summaries={}
for case in ['cram_readwrite','zram_readwrite','cram_direct','zram_direct']:
 for phase in ['enter','read','write']:
  key=case+'_'+phase;summaries[key]={}
  for name in selected:
   rs=[r for r in rows if r['case']==case and r['phase']==phase and r['name']==name]
   if rs:summaries[key][name]={'count':len(rs),'sum_us':round(sum(r['inclusive_us'] for r in rs),3),'calls_us':[r['inclusive_us'] for r in sorted(rs,key=lambda r:r['order'])]}
(root/'summary.json').write_text(json.dumps(summaries,indent=2));print(json.dumps(summaries,indent=2))
