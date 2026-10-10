from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/'figures.json').read_text())
# Chinese font: set a locally available CJK font on other systems.
font=Path('/System/Library/Fonts/STHeiti Light.ttc')
if font.exists():plt.rcParams['font.family']=FontProperties(fname=font).get_name()
plt.rcParams.update({'svg.fonttype':'path','axes.unicode_minus':False,'font.size':12,'figure.facecolor':'#ffffff','axes.spines.top':False,'axes.spines.right':False})
blue='#2563eb';teal='#0d9488';orange='#ea580c';gray='#64748b'
def save(fig,name):
 fig.savefig(ROOT/(name+'.svg'),bbox_inches='tight');fig.savefig(ROOT/(name+'.png'),dpi=150,bbox_inches='tight');plt.close(fig)
r=D['fbatch'];fig,axes=plt.subplots(1,2,figsize=(11.5,4.6))
for ax,suffix,title in zip(axes,['median_us','p99_us'],['中位数','P99']):
 x=range(3);ax.bar([v-.19 for v in x],r['base_'+suffix],.38,color=gray,label='原版');ax.bar([v+.19 for v in x],r['patched_'+suffix],.38,color=teal,label='完整 fbatch 回移')
 ax.set_yscale('log');ax.set_xticks(list(x),['1 页','16 页','256 页']);ax.set_ylabel('迁入调用时间（µs，对数轴）');ax.set_title(title,loc='left');ax.legend(frameon=False,fontsize=10);ax.grid(axis='y',alpha=.16)
fig.suptitle('消掉入口同步，小批迁入收益最明显',fontsize=18)
fig.text(.09,.01,'每个配置 / 页数组合：3 个新 guest，600 个无详细 tracing 样本。',fontsize=10,color=gray);fig.tight_layout(rect=(0,.06,1,.94));save(fig,'fbatch-ab')
# Actual guest timestamps, no invented alignment. Marker interval includes marker overhead.
r=D['guest_tail'];base=r['marker_begin'];fig,ax=plt.subplots(figsize=(11,4.5))
spans=[('MOVE marker 窗口',[r['marker_begin'],r['marker_end']],gray),('前台 off-CPU',r['offcpu'],orange),('后台发送命令',r['send'],blue),('其中 memcpy_toio',r['memcpy'],teal)]
for y,(name,span,color) in enumerate(spans):
 left=(span[0]-base)*1000;duration=(span[1]-span[0])*1000;ax.barh(y,duration,left=left,height=.5,color=color)
 ax.text(left+duration/2,y,f'{duration:.3f} ms',va='center',ha='center',color='white',fontsize=12)
ax.set_yticks(range(4),[v[0] for v in spans]);ax.invert_yaxis();ax.set_xlim(0,17);ax.set_xlabel('相对 MOVE_BEGIN 的 guest 时间（ms）');ax.grid(axis='x',alpha=.15);ax.set_title('前台等待期间，CPU 0 正在发送清理命令',loc='left',fontsize=17)
fig.text(.04,.02,'同一 guest 时钟；区间重叠，不能相加。系统调用独立计时为 16.183 ms；marker 窗口包含标记开销。',fontsize=10,color=gray);fig.tight_layout(rect=(0,.08,1,1));save(fig,'guest-tail')
r=D['mmio'];fig,ax=plt.subplots(figsize=(11,4.4));colors=[blue,teal,orange,gray,'#9333ea']
ax.barh(range(5),r['parts_ms'],color=colors);ax.set_yticks(range(5),r['parts']);ax.invert_yaxis();ax.set_xlim(0,7.6);ax.set_xlabel('累计时间（ms）');ax.set_title('2040 字节 payload：510 次 MMIO 往返，共 15.267 ms',loc='left',fontsize=17)
for y,v in enumerate(r['parts_ms']):ax.text(v+.08,y,f'{v:.3f}',va='center')
fig.text(.03,.02,'各行互斥。另一个计数器诊断批次：510 次设备 payload 回调累计 0.081 ms；不与本图相减。',fontsize=10,color=gray);fig.tight_layout(rect=(0,.08,1,1));save(fig,'mmio-cycle')
r=D['releasecpu'];fig,axes=plt.subplots(1,2,figsize=(11,4.6));ax=axes[0]
ax.bar(['remote\n发送 1 / 归还 1','split\n发送 1 / 归还 0'],r['p99_ms'][1:],color=[blue,teal]);ax.set_ylabel('正式迁入 P99（ms）');ax.set_ylim(0,2.35)
for i,v in enumerate(r['p99_ms'][1:]):ax.text(i,v+.07,f'{v:.3f}',ha='center')
ax.set_title('P99 下降约 52%',loc='left');ax=axes[1];ax.bar(['remote','split'],r['warm_ept_count'],color=[blue,teal]);ax.set_ylim(0,3400);ax.set_ylabel('目标复制 EPT fault（次）')
for i,v in enumerate(r['warm_ept_count']):ax.text(i,v+80,str(v),ha='center')
ax.set_title('独立宿主 trace：fault 减少',loc='left');fig.suptitle('把完成清零的页归还到前台 CPU',fontsize=18)
fig.text(.07,.01,'左：每组 6 个新 guest，共 6000 次；右：每组 2 个新 guest，每次 1000 轮，去掉各批前两轮。',fontsize=10,color=gray);fig.tight_layout(rect=(0,.07,1,.93));save(fig,'release-ab')
# Engineering diagram: two actual PFN chains, spacing is logical, not a proportional time axis.
fig,ax=plt.subplots(figsize=(13,5.6));ax.set_xlim(0,13);ax.set_ylim(0,5.8);ax.axis('off')
def box(x,y,text,color):
 ax.add_patch(FancyBboxPatch((x,y),2.7,1.2,boxstyle='round,pad=.08',facecolor='#f8fafc',edgecolor=color,lw=1.6));ax.text(x+1.35,y+.6,text,ha='center',va='center',fontsize=11)
def arrow(x1,x2,y):ax.annotate('',xy=(x2,y),xytext=(x1,y),arrowprops={'arrowstyle':'->','color':gray,'lw':1.5})
ax.text(.05,5.35,'清零完成后归还到哪里，决定下一次怎样取回同一 PFN',fontsize=18)
ax.text(.05,4.75,'split：PFN 0x37007e，第 0 轮 → 第 14 轮',color=teal,fontsize=12)
texts=['CPU 0 归还 → PCP 0\n10.317484 / 10.317485 s','CPU 0 同一 PCP 出队\n10.320039 s','分配并复制同一 PFN\n10.320040 / 10.320697 s','再次复制：EPT = 0\n完整直接复用：5973 次']
for i,t in enumerate(texts):box(.1+i*3.2,3.3,t,teal)
for i in range(3):arrow(2.88+i*3.2,3.2+i*3.2,3.9)
ax.text(.05,2.78,'remote：PFN 0x3700e2，第 0 轮 → 第 39 轮',color=blue,fontsize=12)
texts=['CPU 1 归还 → PCP 1\n8.786915 / 8.786916 s','PCP 1 drain → buddy\n8.821568 s','buddy refill → PCP 0\n8.825231 s','CPU 0 取出、再复制\n8.859890 / 8.860449 s\n再次复制：EPT = 0']
for i,t in enumerate(texts):box(.1+i*3.2,1.3,t,blue)
for i in range(3):arrow(2.88+i*3.2,3.2+i*3.2,1.9)
ax.text(.1,.52,'PCP 0 / 1 是同一 node 2 zone 的每 CPU 空闲页列表；箭头为逻辑顺序，横向距离不表示时间。',fontsize=11,color=gray)
ax.text(.1,.1,'两组复制 EPT fault 全部对应首次分配到的 PFN；复用 PFN 的复制 EPT fault 为 0。',fontsize=11,color=gray)
save(fig,'pfn-lineage')
