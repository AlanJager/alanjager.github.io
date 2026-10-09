import json,re,sys
from pathlib import Path
p=Path(sys.argv[1]);s=p.read_text().replace('\r','')
part=s.split('NO_SWAP_BEGIN',1)[1].split('NO_SWAP_END',1)[0]
checks={'no_swap':not re.search(r'^/\S+',part,re.M),'pressure_irq':'lthresh watermark: pressuring node 2' in s,'stress_killed':bool(re.search(r'Out of memory: Killed process \d+ \(stress\)',s)),'exit_137':'OOM_EXIT 137' in s,'resumed':'MIGRATION_PROBE rc=0 errno=0 status=2 node=2' in s and 'hthresh watermark: resuming node 2' in s,'guest_survives':'LAB_GUEST_DONE' in s and 'reboot: Power down' in s,'no_panic':'Kernel panic' not in s}
print(json.dumps({'pass':all(checks.values()),'checks':checks},indent=2));sys.exit(0 if all(checks.values()) else 1)
