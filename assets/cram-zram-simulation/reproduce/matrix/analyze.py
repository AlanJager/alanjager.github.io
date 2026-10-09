import json,re,sys
from pathlib import Path
p=Path(sys.argv[1]);s=p.read_text().replace('\r','');out=p.parent.parent if p.parent.name=="logs" else p.parent
results={}
for b in ['cram','zram']:
 for mode in ['direct','readwrite','readrepeat']:
  name=f'{b}_{mode}'
  part=s.split('CASE_BEGIN_'+name+'\n',1)[1].split('TRACE_END_'+name,1)[0]
  trace=part.split('TRACE_BEGIN_'+name+'\n',1)[1]
  (out/(name+'-trace.txt')).write_text(trace)
  phases={}
  for phase in ['ENTER','READ','WRITE','REPEAT_WRITE','REPEAT_READ']:
   m=re.search(r'/\* '+phase+r'_BEGIN \*/(.*?)/\* '+phase+r'_END \*/',trace,re.S)
   if m:
    t=m.group(1);(out/(name+'-'+phase.lower()+'-trace.txt')).write_text(t)
    phases[phase]={'faults':len(re.findall('page_fault_user:',t)),'cram_fault':bool(re.search(r'cram_handle_fault\(\)',t)),'swapin':bool(re.search(r'do_swap_page\(\)',t)),'decompress':bool(re.search(r'zcomp_decompress\(\)',t)),'migrate_to':bool(re.search(r'cram_migrate_to\(\)',t)),'compress':bool(re.search(r'zcomp_compress\(\)',t))}
  states=re.findall(r'STATE .*',part)
  entered=re.search(r'STATE entered .*present=(\d) swapped=(\d) node=(-?\d+)',part)
  checks={'exit':f'CASE_EXIT_{name} 0' in part,'data':'DATA_PASS' in part,'entry':bool(entered) and (entered.group(1,2)==('1','0') if b=='cram' else entered.group(1,2)==('0','1')),'loss':bool(re.search(r'overrun: 0',part)) and not re.search(r'(?:overrun|dropped events): [1-9]',part) and 'LOST' not in trace}
  checks['enter_path']=phases.get('ENTER',{}).get('migrate_to' if b=='cram' else 'compress',False)
  required=['ENTER']+(['WRITE','REPEAT_WRITE'] if mode=='direct' else ['READ','WRITE','REPEAT_WRITE'] if mode=='readwrite' else ['READ','REPEAT_READ'])
  checks['markers']=all(x in phases for x in required)
  checks['roots']=all('GRAPH_ROOT '+x in part for x in ['cram_handle_fault','handle_mm_fault','cram_migrate_to','do_swap_page','__swap_writepage','zcomp_compress','zcomp_decompress'])
  if mode!='direct':
   r=phases.get('READ',{});checks['read']=r.get('faults')==0 if b=='cram' else r.get('swapin',False) and r.get('decompress',False)
  if mode!='readrepeat':
   w=phases.get('WRITE',{});checks['write']=w.get('cram_fault',False) if b=='cram' else (w.get('swapin',False) and w.get('decompress',False) if mode=='direct' else w.get('faults')==0 and not w.get('swapin',True))
   checks['repeat_write']=phases.get('REPEAT_WRITE',{}).get('faults')==0
  else:checks['repeat_read']=phases.get('REPEAT_READ',{}).get('faults')==0
  results[name]={'checks':checks,'states':states,'phases':phases,'pass':all(checks.values())}
res={'completed':'LAB_GUEST_DONE' in s,'cases':results}
res['pass']=res['completed'] and all(r['pass'] for r in results.values())
print(json.dumps(res,indent=2));sys.exit(0 if res['pass'] else 1)
