import re,json,sys
from pathlib import Path
p=Path(sys.argv[1]);s=p.read_text().replace('\r','');out=p.parent.parent if p.parent.name=='logs' else p.parent
phases={}
for name in ['disabled','enabled','blocked']:
 part=s.split('PHASE_BEGIN_'+name,1)[1].split('PHASE_END_'+name,1)[0]
 dist={}
 for m in re.finditer(r'DISTRIBUTION (\w+) bytes=(\d+) stride_pages=64 node0=(\d+) node2=(\d+) swapped=(\d+) other=(\d+)',part):
  dist[m[1]]={'bytes':int(m[2]),'node0_samples':int(m[3]),'node2_samples':int(m[4]),'swap_samples':int(m[5]),'other_samples':int(m[6])}
 snapshots={}
 for label in ['cold','warm']:
  m=re.search('SNAPSHOT_BEGIN '+label+r' /proc/vmstat\n(.*?)SNAPSHOT_END',part,re.S)
  if m:snapshots[label]={k:int(v) for k,v in re.findall(r'^(\S+) (\d+)$',m[1],re.M) if k.startswith(('pgdemote','pgpromote','pswp','pgscan','pgsteal'))}
 wm=re.search(r'WARM_WRITE ns=(\d+) bytes=(\d+)',part)
 phases[name]={'pass':f'WORKLOAD_EXIT_{name} 0' in part and 'WORKLOAD_DATA_PASS' in part,'distributions':dist,'vmstat':snapshots,'warm_write_ns':int(wm[1]) if wm else None}
probes={}
for name in ['initial','blocked','resumed']:
 part=s.split('PROBE_BEGIN_'+name,1)[1].split('PROBE_END_'+name,1)[0]
 m=re.search(r'MIGRATION_PROBE rc=(-?\d+) errno=(\d+) status=(-?\d+) node=(-?\d+)',part)
 probes[name]=dict(zip(['rc','errno','status','node'],map(int,m.groups()))) if m else {}
checks={'completed':'LAB_GUEST_DONE' in s,'no_oom':'Out of memory:' not in s,'workloads_pass':all(x['pass'] for x in phases.values()),'demotion_off':phases['disabled']['distributions'].get('cold',{}).get('node2_samples')==0,'automatic_cram':phases['enabled']['distributions'].get('cold',{}).get('node2_samples',0)>0,'blocked_fallback':phases['blocked']['distributions'].get('cold',{}).get('node2_samples')==0 and phases['blocked']['distributions'].get('cold',{}).get('swap_samples',0)>0,'initial_migrate':probes['initial'].get('node')==2,'blocked_migrate':probes['blocked'].get('node')!=2 and probes['blocked'].get('errno')==28,'resumed_migrate':probes['resumed'].get('node')==2,'pressure_irq':'lthresh watermark: pressuring node 2' in s,'resume_irq':'hthresh watermark: resuming node 2' in s}
checks['warm_target']=all(v['distributions'].get('warm_target',{}).get('node0_samples')==256 and v['distributions'].get('warm_target',{}).get('node2_samples')==0 and v['distributions'].get('warm_target',{}).get('swap_samples')==0 for v in phases.values())
checks['private_to_hot']=phases['enabled']['distributions'].get('cold_target',{}).get('node2_samples')==256
res={'pass':all(checks.values()),'checks':checks,'phases':phases,'probes':probes,'sampling':'one per 64 pages, point-in-time observation; sampled nodes are not complete totals'}
print(json.dumps(res,indent=2));sys.exit(0 if res['pass'] else 1)
