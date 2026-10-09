import subprocess,socket,json,time,pathlib
root=pathlib.Path(__file__).resolve().parent;log=root/'logs/guest-boot.log';events=[]
with log.open('w') as f:
 p=subprocess.Popen(['bash',str(root/'run-guest.sh')],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,cwd=root)
 sent=set();deadline=time.monotonic()+310
 while p.poll() is None and time.monotonic()<deadline:
  s=log.read_text(errors='replace')
  for label,cmd in [('LOW','cxl-inject-ct3-lthresh-watermark'),('HIGH','cxl-inject-ct3-hthresh-watermark')]:
   if 'INJECT_'+label+'_READY' in s and label not in sent:
    with socket.socket(socket.AF_UNIX) as sock:
     sock.settimeout(3);sock.connect(str(root/'qmp.sock'));rf=sock.makefile('r');greet=json.loads(rf.readline())
     def request(payload):
      sock.sendall((json.dumps(payload)+'\n').encode())
      while True:
       r=json.loads(rf.readline())
       if 'return' in r or 'error' in r:return r
     caps=request({'execute':'qmp_capabilities'})
     reply=request({'execute':cmd,'arguments':{'path':'/machine/peripheral/cxl-ct3-0'}})
     events.append({'label':label,'command':cmd,'response':reply,'monotonic':time.monotonic()})
     (root/'qmp-events.json').write_text(json.dumps(events,indent=2))
    sent.add(label)
  time.sleep(.1)
 if p.poll() is None:p.terminate()
 rc=p.wait()
(root/'guest-exit-status.txt').write_text(str(rc)+'\n')
print('GUEST_EXIT',rc,'QMP',events)
