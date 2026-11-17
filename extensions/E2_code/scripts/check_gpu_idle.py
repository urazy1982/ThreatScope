#!/usr/bin/env python3
"""Block a GPU experiment when any other NVIDIA compute app is present. No kills/no waits."""
import subprocess,sys

def check(query=None):
 if query is None:
  query=subprocess.run(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],
   capture_output=True,text=True,timeout=30)
 if query.returncode!=0:
  raise RuntimeError('GPU_QUERY_FAILED: '+query.stderr.strip())
 lines=[v.strip() for v in query.stdout.splitlines() if v.strip() and v.strip().lower() not in ('n/a','[not supported]')]
 if lines:
  raise RuntimeError('GPU_BUSY_COMPUTE_PIDS='+','.join(lines)+'; do not interrupt them. Try again when idle.')
 return True
if __name__=='__main__':
 try:
  check();print('GPU_IDLE_PASS: no competing compute process reported by nvidia-smi')
 except Exception as e:
  print('GPU_START_BLOCKED:',e,file=sys.stderr);sys.exit(2)
