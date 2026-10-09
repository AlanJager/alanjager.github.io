import csv,json,math,re,sys
from pathlib import Path
p=Path(sys.argv[1]);s=p.read_text().replace('\r','');out=p.parent.parent if p.parent.name=='logs' else p.parent
headers=['backend','mode','attempt','prepare_ns','read_ns','repeat_read_ns','write_ns','repeat_write_ns','pageout_attempts','entered_node','read_node','write_node']
rows=[];clocks=[];fails=[]
for line in s.splitlines():
 if line.startswith('SAMPLE,'):
  vals=line.split(',')[1:]
  if len(vals)!=len(headers):raise ValueError('Truncated sample: '+line)
  rows.append(dict(zip(headers,vals)))
 elif line.startswith('CLOCK,'):clocks.append(line.split(',')[1:])
 elif line.startswith('FAIL,'):fails.append(line.split(',')[1:])
with (out/'samples.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=headers);w.writeheader();w.writerows(rows)
with (out/'clock.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['backend','mode','sample','ns']);w.writerows(clocks)
with (out/'failures.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['backend','mode','attempt','reason','pageout_attempts']);w.writerows(fails)
def stats(values):
 v=sorted(values)
 return {'n':len(v),'p50':v[math.ceil(len(v)*.5)-1],'p95':v[math.ceil(len(v)*.95)-1],'p99':v[math.ceil(len(v)*.99)-1],'min':min(v),'max':max(v)}
results={};checks={'completed':'LAB_GUEST_DONE' in s,'config_count':len(re.findall(r'CONFIG .*cpu=0 .*tracer=nop events=0',s))==9,'row_count':len(rows)==9000,'clock_count':len(clocks)==9000}
for b in ['dram','cram','zram']:
 for m in ['direct','readwrite','readrepeat']:
  key=b+'_'+m;rs=[r for r in rows if r['backend']==b and r['mode']==m];fs=[r for r in fails if r[:2]==[b,m]]
  checks[key]=len(rs)==1000 and f'BENCH_EXIT {key} 0' in s and f'SUMMARY {b} {m} success=1000 failed={len(fs)}' in s
  stages=['prepare_ns']+(['write_ns','repeat_write_ns'] if m=='direct' else ['read_ns','write_ns','repeat_write_ns'] if m=='readwrite' else ['read_ns','repeat_read_ns'])
  results[key]={'successful':len(rs),'failed':len(fs),'phases':{x:stats([int(r[x]) for r in rs]) for x in stages} if rs else {},'pageout_attempts':stats([int(r['pageout_attempts']) for r in rs]) if b=='zram' and rs else None}
  checks[key+'_states']=all(int(r['entered_node'])==({'dram':0,'cram':2,'zram':-2}[b]) and (m=='direct' or int(r['read_node'])==(2 if b=='cram' else 0)) and (m=='readrepeat' or int(r['write_node'])==0) for r in rs)
clock_stats=stats([int(r[3]) for r in clocks]) if clocks else None
res={'pass':all(checks.values()),'checks':checks,'results':results,'clock_overhead_ns':clock_stats,'failed_total':len(fails),'quantile_method':'nearest rank','unit':'ns'}
print(json.dumps(res,indent=2));sys.exit(0 if res['pass'] else 1)
