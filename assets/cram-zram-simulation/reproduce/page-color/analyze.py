from pathlib import Path
import re,json,csv,hashlib
ROOT=Path(__file__).resolve().parent
runs={}
for name in ['observed','control']:
 text=(ROOT/(name+'-guest.log')).read_text(errors='replace')
 assert 'DATA_PASS' in text and 'COLOR_EXIT_0' in text and 'COLOR_DONE' in text,name
 assert (ROOT/(name+'-qemu-exit.txt')).read_text().strip()=='0',name
 assert 'DATA_FAIL' not in text and 'Kernel panic' not in text,name
 assert not re.search(r'BUG:|WARNING:|soft lockup|hard LOCKUP|Out of memory:',text),name
 writes=[dict(stage=m[0],round=int(m[1]),start_page=int(m[2]),pages=int(m[3]),ns=int(m[4]),begin=int(m[5]),end=int(m[6])) for m in re.findall(r'WRITE (\w+) round=(\d+) start_page=(\d+) pages=(\d+) ns=(\d+) begin=(\d+) end=(\d+)',text)]
 maps=[(int(a),int(b),''.join(c*int(n) for c,n in re.findall(r'([DCSU])(\d+),',m))) for a,b,m in re.findall(r'RLE (\d+) (\d+) ([DCSU0-9,]+)',text)]
 assert len(maps)==int(re.search(r'OBSERVER active=\d snapshots=(\d+)',text)[1])
 assert len(writes)==25 and maps and all(len(m)==1920 for _,_,m in maps)
 assert all(a<=b for a,b,_ in maps)
 unknown=sum(m.count('U') for _,_,m in maps)
 runs[name]={'writes':writes,'snapshots':len(maps),'unknown':unknown,'total_sample_states':len(maps)*1920,'snapshot_duration_ns':{'median':sorted(b-a for a,b,_ in maps)[len(maps)//2],'max':max(b-a for a,b,_ in maps)},'data_pass':True}
 if name=='observed':timeline=maps
# Count only observed adjacent states; unknown gaps break chains.
def stats(maps):
 per=[];edges={a+b:0 for a in 'DCS' for b in 'DCS' if a!=b}
 for i in range(1920):
  transitions=[];chain=[];cycles=0
  for start,end,m in maps:
   state=m[i]
   if state=='U':chain=[];continue
   if chain and state!=chain[-1]:
    edges[chain[-1]+state]+=1;transitions.append((end,chain[-1],state))
   if not chain or state!=chain[-1]:
    chain.append(state)
    if len(chain)>=3 and chain[-3:]==['C','D','C']:cycles+=1
  per.append({'sample_id':i,'logical_page':i*64,'offset_mib':i/4,'C_D_C_cycles':cycles,'C_to_D':sum(a=='C' and b=='D' for _,a,b in transitions),'D_to_C':sum(a=='D' and b=='C' for _,a,b in transitions),'transitions':transitions})
 return {'transitions':edges,'pages_with_C_D_C':sum(p['C_D_C_cycles']>0 for p in per),'observed_C_D_C_cycles':sum(p['C_D_C_cycles'] for p in per),'sample_pages':1920},per
allstats,per=stats(timeline)
original_end=runs['observed']['writes'][1]['begin']
original=[m for m in timeline if m[1]<=original_end]
originalstats,origper=stats(original)
originalstats['target_first64MiB_pages_with_C_D_C']=sum(p['C_D_C_cycles']>0 for p in origper[:256])
result={'scope':'RAM-backed CRAM; sampled logical-page state transitions, not PFN identity or exhaustive migration tracing','original_phase':originalstats,'all_phases':allstats,'runs':runs,'inputs':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['color.c','observed-guest.log','control-guest.log']}}
(ROOT/'results.json').write_text(json.dumps(result,indent=2))
with (ROOT/'page-transitions.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['logical_page','offset_mib','time_ns','from','to'])
 for p in per:
  for t,a,b in p['transitions']:w.writerow([p['logical_page'],p['offset_mib'],t,a,b])
with (ROOT/'timeline.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['start_ns','end_ns','states_D_C_S_U'])
 w.writerows(timeline)
with (ROOT/'writes.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['run']+list(runs['observed']['writes'][0]));w.writeheader()
 for name,r in runs.items():
  for row in r['writes']:w.writerow({'run':name,**row})
print(json.dumps({k:result[k] for k in ['original_phase','all_phases']},indent=2))
print('observed/control original ms',*[runs[n]['writes'][0]['ns']/1e6 for n in ['observed','control']])
print('snapshots',runs['observed']['snapshots'],'unknown',runs['observed']['unknown'])
