"""Project-scoped dashboard lifecycle; never stop listeners by port alone."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import httpx
import psutil

ROOT=Path(__file__).resolve().parents[2]
STATE=ROOT/'logs/.mars-dashboard-process.json'

def healthy(port):
    try:
        with httpx.Client(timeout=2) as client:
            root=client.get(f'http://127.0.0.1:{port}/')
            match=re.search(r'window\.__HERMES_SESSION_TOKEN__\s*=\s*("[^"\n]+")',root.text)
            if root.status_code!=200 or not match:return False
            client.headers['X-Hermes-Session-Token']=json.loads(match.group(1))
            return client.get(f'http://127.0.0.1:{port}/api/health').status_code==200
    except (httpx.HTTPError,ValueError):return False

def owned_process(record):
    """PID, start time, CWD and command must all match our saved launch."""
    try:
        process=psutil.Process(record['pid'])
        args=process.cmdline()
        if abs(process.create_time()-record['create_time'])>.01:return None
        if Path(process.cwd()).resolve()!=ROOT.resolve():return None
        if 'hermes_cli.main' not in args or 'dashboard' not in args:return None
        index=args.index('--port')
        if args[index+1]!=str(record['port']):return None
        if Path(args[0]).resolve()!=Path(record['executable']).resolve():return None
        return process
    except (psutil.Error,KeyError,ValueError,IndexError,OSError):return None

def stop_owned(record):
    process=owned_process(record)
    if process is None:return False
    # Terminate only the verified launcher; no scan/kill of other ports or PID tree.
    process.terminate()
    try:process.wait(timeout=10)
    except psutil.TimeoutExpired:raise RuntimeError('Owned dashboard did not exit; no forced termination performed')
    return True

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['start','status','stop'],nargs='?',default='start')
    parser.add_argument('--port',type=int,default=9120)
    args=parser.parse_args()
    if not 1<=args.port<=65535:parser.error('port must be 1..65535')
    if args.action=='stop':
        if not STATE.exists():raise SystemExit('No dashboard process owned by this helper; nothing stopped')
        record=json.loads(STATE.read_text(encoding='utf-8'))
        if not stop_owned(record):raise SystemExit('Ownership check failed; nothing stopped')
        STATE.unlink();print('Owned dashboard stopped');return
    if healthy(args.port):print(f'Dashboard ready: http://127.0.0.1:{args.port}');return
    if args.action=='status':raise SystemExit('Dashboard is not healthy on the requested port')
    if STATE.exists():
        record=json.loads(STATE.read_text(encoding='utf-8'))
        if owned_process(record):raise SystemExit('An owned process is already running; inspect its log before starting another')
    STATE.parent.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,HERMES_HOME=str(ROOT),PYTHONPATH=str(ROOT/'hermes-agent'))
    command=[sys.executable,'-m','hermes_cli.main','dashboard','--port',str(args.port),'--no-open']
    if (ROOT/'hermes-agent/hermes_cli/web_dist').is_dir():command.append('--skip-build')
    options={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {'start_new_session':True}
    with (ROOT/'logs/dashboard-mars.log').open('ab') as log:
        process=subprocess.Popen(command,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,**options)
    record={'pid':process.pid,'create_time':psutil.Process(process.pid).create_time(),'port':args.port,'executable':sys.executable}
    STATE.write_text(json.dumps(record),encoding='utf-8')
    for _ in range(30):
        if process.poll() is not None:STATE.unlink(missing_ok=True);raise SystemExit('Dashboard exited; see logs/dashboard-mars.log')
        if healthy(args.port):print(f'Dashboard ready: http://127.0.0.1:{args.port}');return
        time.sleep(1)
    raise SystemExit('Startup timed out; inspect log and owned process before retrying')

if __name__=='__main__':main()
