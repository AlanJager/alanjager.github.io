from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
root=Path(__file__).resolve().parent;data=json.loads((root/'summary.json').read_text())
font=FontProperties(fname='/System/Library/Fonts/STHeiti Light.ttc')
plt.rcParams['svg.fonttype']='none'
colors={'cram':'#32866b','zram':'#4d70aa'}
specs=[('enter','页进入目标层','readwrite','enter'),('first-read','首次读 8 字节','readwrite','read'),('direct-write','直接首次写 8 字节（此前未读）','direct','write'),('read-then-write','首次读后，应用修改 8 字节','readwrite','write')]
for slug,title,mode,phase in specs:
 fig,axes=plt.subplots(1,2,figsize=(15,5.2),dpi=160);fig.patch.set_facecolor('white');fig.suptitle(title,fontproperties=font,fontsize=19,y=.97)
 lists={}
 for backend in ['cram','zram']:
  key=f'{backend}_{mode}_{phase}';ds=data[key];rs=[]
  if phase=='enter':names=['cram_migrate_to','migrate_pages','alloc_cram_folio','try_to_migrate','folio_mc_copy','lru_add_drain_all'] if backend=='cram' else ['__swap_writepage','zram_submit_bio','zcomp_compress','lz4_compress']
  else:names=['handle_mm_fault','cram_handle_fault','migrate_pages','alloc_cram_promote_folio','try_to_migrate','folio_mc_copy'] if backend=='cram' else ['handle_mm_fault','do_swap_page','swap_read_folio','zram_submit_bio','zcomp_decompress','lz4_decompress']
  for name in names:
   if name not in ds:continue
   calls=ds[name]['calls_us'];label=name
   if name=='handle_mm_fault' and len(calls)>1:label+=' [1]';val=calls[0]
   else:val=ds[name]['sum_us']
   depth={'handle_mm_fault':0,'cram_migrate_to':0,'__swap_writepage':0,'cram_handle_fault':1,'do_swap_page':1,'migrate_pages':2,'swap_read_folio':2,'zram_submit_bio':3 if phase!='enter' else 1,'zcomp_compress':2,'lz4_compress':3,'zcomp_decompress':4,'lz4_decompress':5}.get(name,3)
   if backend=='cram' and phase=='enter':depth={'cram_migrate_to':0,'migrate_pages':1,'alloc_cram_folio':2,'try_to_migrate':2,'folio_mc_copy':2,'lru_add_drain_all':1}[name]
   rs.append((name,label,val,depth))
  if ds.get('handle_mm_fault',{}).get('count',0)>1:rs.append(('handle_mm_fault','handle_mm_fault [2: retry]',ds['handle_mm_fault']['calls_us'][1],0))
  lists[backend]=rs
 xmax=max([r[2] for rs in lists.values() for r in rs] or [1])*1.18
 for ax,backend in zip(axes,['cram','zram']):
  rs=lists[backend];ax.set_xlim(0,xmax);ax.set_ylim(7,-1);ax.set_title('CRAM' if backend=='cram' else 'zram swap',fontproperties=font,fontsize=16,color=colors[backend],pad=10)
  if rs:
   for i,(_,label,val,depth) in enumerate(rs):
    ax.barh(i,val,height=.52,color=colors[backend],alpha=max(.42,1-depth*.12));ax.text(val+xmax*.014,i,f'{val:.3f}',va='center',fontsize=10,color='#243746')
   ax.set_yticks(range(len(rs)),[('↳ ' if r[3] else '')+r[1] for r in rs],fontfamily='monospace',fontsize=9)
  else:
   ax.set_yticks([]);msg='本阶段无所监控的 fault 函数调用\n\n' + ('读取后仍在 CRAM node 2' if backend=='cram' else '修改已恢复到普通 RAM 的页')+'\n\n无 fault 调用 ≠ 访问耗时为 0'
   ax.text(.5,.55,msg,transform=ax.transAxes,ha='center',va='center',fontproperties=font,fontsize=14,color=colors[backend],linespacing=1.8)
  ax.set_xlabel('函数耗时（µs，包含子调用）',fontproperties=font,fontsize=11);ax.grid(axis='x',alpha=.14);ax.set_axisbelow(True)
  for side in ['top','right','left']:ax.spines[side].set_visible(False)
  ax.tick_params(axis='y',length=0)
 fig.text(.02,.015,'第二轮 · 单页 4 KiB · 单次 function_graph 记录；子项标记表示下层调用，条形不是连续时间线，嵌套时间不相加。',fontproperties=font,fontsize=10,color='#52616b')
 fig.subplots_adjust(left=.18,right=.97,bottom=.14,top=.84,wspace=.95)
 for ext in ['png','svg']:fig.savefig(root/f'trace-{slug}.{ext}',bbox_inches='tight',facecolor='white')
 plt.close(fig)
print('Rendered four paired duration figures')
