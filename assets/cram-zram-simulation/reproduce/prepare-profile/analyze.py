from pathlib import Path
import re,json,csv,statistics,hashlib
R=Path(__file__).resolve().parent;s=(R/'guest-boot.log').read_text();t=(R/'move.trace').read_text()
assert 'PREPARE_DATA_PASS' in s and 'PREPARE_EXIT_0' in s
assert (R/'guest-exit-status.txt').read_text().strip()=='0'
assert not re.search(r'BUG:|WARNING:|lockup|Kernel panic|MOVE_FAIL|DATA_FAIL',s)
stack=[];entries=[];case=None
for line in t.splitlines():
 if 'MOVE_BEGIN ' in line:case=int(re.search(r'MOVE_BEGIN (\d+)',line)[1]);assert not stack
 if '|' not in line:continue
 call=line.rsplit('|',1)[1].strip()
 duration=re.search(r'(\d+\.\d+) us',line)
 if call.endswith('() {'):
  stack.append(call[:-4])
 elif call=='}':
  assert stack,line
  name=stack.pop();assert duration,line
  entries.append({'case':case,'name':name,'inclusive_us':float(duration[1]),'depth':len(stack)})
 elif call.endswith('();') and duration:
  entries.append({'case':case,'name':call[:-3],'inclusive_us':float(duration[1]),'depth':len(stack)})
assert not stack
# Names have an opening '(' retained by suffix slicing; normalize.
for e in entries:e['name']=e['name'].rstrip('(')
roots=[e for e in entries if e['name']=='__x64_sys_move_pages'];assert len(roots)==40
assert len(set(e['case'] for e in roots))==40
summary={}
for name in ['__x64_sys_move_pages','kernel_move_pages','lru_cache_disable','synchronize_rcu_expedited','lru_add_drain_all','cram_migrate_to','migrate_pages','folio_mc_copy']:
 vals=[e['inclusive_us'] for e in entries if e['name']==name]
 summary[name]={'n':len(vals),'median_us':statistics.median(vals),'max_us':max(vals)}
samples=[{'traced':int(a),'attempt':int(b),'wall_ns':int(c)} for a,b,c in re.findall(r'PREPARE_SAMPLE traced=(\d) attempt=(\d+) ns=(\d+)',s)]
assert sum(x['traced']==0 for x in samples)==200 and sum(x['traced']==1 for x in samples)==40
wall={str(i):{'n':len(v:=[x['wall_ns']/1000 for x in samples if x['traced']==i]),'median_us':statistics.median(v),'max_us':max(v)} for i in [0,1]}
result={'pass':True,'wall':wall,'inclusive_function_durations':summary,'inputs':{n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in ['prepare.c','move.trace','guest-boot.log']}}
(R/'results.json').write_text(json.dumps(result,indent=2))
for name,rows in [('functions.csv',entries),('samples.csv',samples)]:
 with (R/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps(result,indent=2))
