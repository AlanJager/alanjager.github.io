from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,BoundaryNorm
from matplotlib.patches import Patch
from matplotlib.font_manager import FontProperties
ROOT=Path(__file__).resolve().parent
r=json.loads((ROOT/'page-color-results.json').read_text());rows=list(csv.DictReader((ROOT/'timeline.csv').open()))
x=np.array([int(a['end_ns'])/1e9 for a in rows]);z=np.array([[{'D':0,'C':1,'S':2,'U':3}[c] for c in a['states_D_C_S_U']] for a in rows],dtype=np.uint8).T
y=(np.arange(1920)+.5)/4
plt.rcParams['font.family']=FontProperties(fname='/System/Library/Fonts/STHeiti Light.ttc').get_name()
plt.rcParams['axes.unicode_minus']=False
colors=['#94a3b8','#14b8a6','#f59e0b','#f8fafc'];cmap=ListedColormap(colors);norm=BoundaryNorm([-.5,.5,1.5,2.5,3.5],4)
fig,axes=plt.subplots(2,1,figsize=(12,9),gridspec_kw={'height_ratios':[1,2]})
end=r['runs']['observed']['writes'][1]['begin']/1e9
for ax,mask,title in [(axes[0],x<=end,'原升温阶段：只写前 64 MiB 页范围'),(axes[1],np.ones(len(x),dtype=bool),'完整时间线：升温后分段轮流写，遍历工作集三遍')]:
 ax.pcolormesh(x[mask],y,z[:,mask],shading='nearest',cmap=cmap,norm=norm,rasterized=True)
 ax.set_ylim(480,0);ax.set_ylabel('逻辑页偏移（MiB）');ax.set_title(title,loc='left',fontsize=13)
 ax.axhline(64,color='#334155',lw=.8,ls='--')
 ax.set_xlabel('自 cold 快照起的时间（s）')
for write in r['runs']['observed']['writes']:
 if write['stage']=='rotating':axes[1].axvline(write['begin']/1e9,color='white',lw=.4,alpha=.6)
axes[0].axvspan(r['runs']['observed']['writes'][0]['begin']/1e9,r['runs']['observed']['writes'][0]['end']/1e9,facecolor='none',edgecolor='#dc2626',lw=1.4)
fig.suptitle('给同一逻辑页着色：位置变化时间线',fontsize=18)
fig.legend(handles=[Patch(color=c,label=l) for c,l in zip(colors,['普通内存 node 0','CRAM node 2','swap','未确定／采样竞争'])],loc='lower center',bbox_to_anchor=(.5,.07),ncol=4,fontsize=11)
fig.text(.09,.02,'每 64 页抽样 1 页，共 1920 页；约每 20 ms 发起一次快照。相邻颜色变化是观测到的状态变化。\n观察器有开销，快照不是原子操作，短暂往返可能漏采；逻辑页编号保持不变，PFN 允许变化。',fontsize=10,color='#475569')
fig.tight_layout(rect=(0,.13,1,.95))
fig.savefig(ROOT/'page-color.png',dpi=170);fig.savefig(ROOT/'page-color.svg');plt.close(fig)
