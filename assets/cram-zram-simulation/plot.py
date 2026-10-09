"""Regenerate publication figures from summary.csv; requires matplotlib."""
from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
ROOT = Path(__file__).resolve().parent
rows = list(csv.DictReader((ROOT/'summary.csv').open()))
def val(kind, case, backend, metric):
    return float(next(r['value'] for r in rows if (r['kind'],r['case'],r['backend'],r['metric'])==(kind,case,backend,metric)))
fontpath=Path('/System/Library/Fonts/STHeiti Light.ttc')
if fontpath.exists():
    plt.rcParams['font.family']=FontProperties(fname=fontpath).get_name()
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.unicode_minus':False,'figure.facecolor':'white','savefig.facecolor':'white'})
colors=['#64748b','#0f766e','#d97706']
fig,axes=plt.subplots(3,1,figsize=(10,8),sharex=True)
for ax,(case,metric,title) in zip(axes,[('readrepeat','read_ns','首次读'),('direct','write_ns','直接首次写'),('readwrite','write_ns','先读后首次写')]):
    ax.axvspan(.156,.429,color='#e2e8f0',alpha=.7)
    for y,backend,color in zip([2,1,0],['dram','cram','zram'],colors):
        p=[val('latency',case,backend,metric+'_'+q)/1000 for q in ['p50','p95','p99']]
        ax.hlines(y,p[0],p[2],color=color,lw=2)
        ax.plot(p[0],y,'o',color=color,ms=7)
        ax.plot(p[1],y,'|',color=color,ms=14,mew=2)
        ax.plot(p[2],y,'|',color=color,ms=8)
        ax.text(p[2]*1.15,y,f'{p[0]:.3f} / {p[1]:.3f} / {p[2]:.3f}',va='center',fontsize=10,color=color)
    ax.set_yticks([2,1,0],['DRAM','CRAM','zram'])
    ax.set_ylim(-.5,2.6)
    ax.set_title(title,loc='left',fontweight='bold')
    ax.set_xscale('log'); ax.set_xlim(.1,160)
    ax.grid(axis='x',alpha=.2)
axes[-1].set_xlabel('访问时间（µs，对数坐标）')
fig.suptitle('固定版本模拟：首次访问的 p50 / p95 / p99',fontweight='bold',fontsize=16)
fig.text(.12,.02,'每组 n=1000；原始计时含开销。灰区：空计时区间 p50–p99（0.156–0.429 µs）。\nRAM 后备设备，cache 未控制；这些数字不是实际硬件延迟。',fontsize=10)
fig.tight_layout(rect=(0,.08,1,.95))
fig.savefig(ROOT/'latency.png',dpi=180); plt.close(fig)
fig,(a,b)=plt.subplots(1,2,figsize=(12,5),gridspec_kw={'width_ratios':[1.45,1]})
labels=['关闭 demotion','开启 demotion','压力阻止迁入']
left=[0,0,0]
for metric,label,color in [('node0_samples','普通 node 0',colors[0]),('node2_samples','CRAM node 2',colors[1]),('swap_samples','swapped',colors[2])]:
    values=[val('pressure_distribution',case,'cram+zram',metric) for case in ['cold_disabled','cold_enabled','cold_blocked']]
    a.barh([2,1,0],values,left=left,color=color,label=label,height=.55)
    for y,l,v in zip([2,1,0],left,values):
        if v:a.text(l+v/2,y,str(int(v)),ha='center',va='center',color='white')
    left=[l+v for l,v in zip(left,values)]
a.set_yticks([2,1,0],labels);a.set_xlim(0,2000);a.set_xlabel('采样点数量（每组共 1920 点）');a.set_title('冷阶段页分布',loc='left',fontweight='bold');a.legend(loc='upper center',bbox_to_anchor=(.5,-.38),ncol=3,fontsize=9)
warm=[val('pressure_warm',case,'cram+zram','batch_write_wall_time')/1e6 for case in ['disabled','enabled','blocked']]
b.barh([2,1,0],warm,color=[colors[2],colors[1],colors[2]],height=.55)
b.set_yticks([2,1,0],['zram 控制','CRAM','zram 回退']);b.set_xlim(0,300)
for y,v in zip([2,1,0],warm):b.text(v+5,y,f'{v:.3f}',va='center')
b.set_xlabel('单批墙钟时间（ms）');b.set_title('逐页写入升温',loc='left',fontweight='bold')
fig.suptitle('480 MiB 工作集：页分布与升温成本',fontsize=16,fontweight='bold')
fig.text(.08,.015,'升温：64 MiB 页范围，每页写 8 字节，实际共写 128 KiB；单批次、固定顺序。\n页分布是抽样快照，不是压缩率；额外 RAM 后备容量未按相同物理预算对齐。',fontsize=10)
fig.tight_layout(rect=(0,.20,1,.93));fig.savefig(ROOT/'pressure.png',dpi=180);plt.close(fig)
