"""Draw the measured anonymous-page lifecycle; requires matplotlib."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from matplotlib.font_manager import FontProperties
ROOT=Path(__file__).resolve().parent
plt.rcParams['font.family']=FontProperties(fname='/System/Library/Fonts/STHeiti Light.ttc').get_name()
plt.rcParams['svg.fonttype']='path'
fig,ax=plt.subplots(figsize=(16,7));fig.patch.set_facecolor('white')
ax.set_xlim(-1.6,15);ax.set_ylim(-2.2,5.3);ax.axis('off')
xs=[0,4,8,12];ys=[3.0,.5];w=2.55;h=1.35
for x,label in zip(xs,['初始页','进入目标层后','首次读后','随后首次写后']):
 ax.text(x+w/2,4.55,label,ha='center',va='center',fontsize=15,color='#334155')
ax.text(-.25,5.0,'同一个 4 KiB 匿名页：读完以后是否回到普通内存？',fontsize=19,color='#0f172a')
cram=[('普通内存页','node 0\npresent，可读写','#e2e8f0'),('CRAM 中的页','node 2\npresent，只读','#ccfbf1'),('仍是 CRAM 页','node 2\npresent，只读','#ccfbf1'),('恢复普通内存页','node 0\npresent，可读写','#e2e8f0')]
zram=[('普通内存页','node 0\npresent，可读写','#e2e8f0'),('zram 压缩对象','保存在普通 RAM 中\nPTE：swap entry','#ffedd5'),('恢复普通内存页','node 0\npresent，可读写','#e2e8f0'),('仍是普通内存页','node 0\npresent，可读写','#e2e8f0')]
for y,backend,items,edges,color in [(ys[0],'CRAM',cram,['整页迁移\n写保护','直接读取\n无恢复 fault','写保护 fault\n整页提升'],'#0f766e'),(ys[1],'zram\n作为 swap',zram,['swap-out\nLZ4 压缩','swap fault\n整页解压恢复','直接写入\n无新 swap fault'],'#c2410c')]:
 ax.text(-.25,y+.2,backend,ha='right',va='center',fontsize=16,color=color)
 for x,(title,body,fill) in zip(xs,items):
  ax.add_patch(FancyBboxPatch((x,y-h/2),w,h,boxstyle='round,pad=.07,rounding_size=.12',facecolor=fill,edgecolor='#94a3b8',lw=1))
  ax.text(x+w/2,y+.34,title,ha='center',va='center',fontsize=14,color='#0f172a')
  ax.text(x+w/2,y-.2,body,ha='center',va='center',fontsize=12,color='#334155',linespacing=1.5)
 for x,label in zip(xs[:-1],edges):
  ax.add_patch(FancyArrowPatch((x+w+.12,y),(x+4-.13,y),arrowstyle='-|>',mutation_scale=15,lw=1.6,color=color))
  ax.text(x+3.25,y+.30,label,ha='center',va='bottom',fontsize=11,color=color,linespacing=1.5)
ax.text(0,-.95,'CRAM：首次读后，页仍在压缩内存；首次写才提升。\nzram swap：首次读已恢复普通页，随后写入不再需要 swap-in。',fontsize=13,color='#334155',linespacing=1.7)
ax.text(0,-1.85,'若跳过读直接写：CRAM 仍需写 fault 提升；zram 需 swap fault 恢复原页，再修改 8 字节。\n图示为本轮固定版本的匿名页路径；压缩对象所在的 RAM 不等于原来的可映射匿名页。',fontsize=11,color='#64748b',linespacing=1.5)
fig.tight_layout(pad=.6)
fig.savefig(ROOT/'page-lifecycle.png',dpi=160)
fig.savefig(ROOT/'page-lifecycle.svg')
