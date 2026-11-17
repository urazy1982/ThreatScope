#!/usr/bin/env python3
"""Opt-in sequential E1 launch; never runs in background or kills a process."""
import argparse,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from e1_neutral_gpu import verify_frozen_inputs
from check_gpu_idle import check
ROOT=Path(__file__).resolve().parents[1]
MODELS={'Qwen/Qwen2.5-3B-Instruct':'qwen2.5-3b',
        'meta-llama/Llama-3.2-3B-Instruct':'llama-3.2-3b',
        'mistralai/Mistral-7B-Instruct-v0.3':'mistral-7b'}
def cells(mode):
 if mode=='smoke':return [('Qwen/Qwen2.5-3B-Instruct','bf16','N0')]
 return [(m,p,c) for m in MODELS for p in ('bf16','nf4') for c in ('N0','N1')]
def run(args):
 manifest,windows,config=verify_frozen_inputs(args.inputs,args.manifest)
 for name in MODELS:
  assert name in config['models'],'FROZEN_MODEL_MISSING '+name
 # Fail closed when another compute process is active. Run in foreground only.
 if not args.dry_run:check()
 out=Path(args.results).expanduser().resolve()
 for model,precision,condition in cells(args.mode):
  target=out/'E1'/MODELS[model]/precision/condition
  cmd=[sys.executable,str(ROOT/'scripts/e1_neutral_gpu.py'),
       '--inputs',str(args.inputs),'--manifest',str(args.manifest),'--model',model,
       '--precision',precision,'--condition',condition,'--out',str(target)]
  if args.mode=='smoke':cmd+=['--limit','2']
  print('CELL',model,precision,condition,'->',target,flush=True)
  if args.dry_run:
   print('DRY_RUN_ONLY', ' '.join(cmd));continue
  log_dir=out/'logs';log_dir.mkdir(parents=True,exist_ok=True)
  logfile=log_dir/(MODELS[model]+'_'+precision+'_'+condition+'.log')
  with open(logfile,'a',encoding='utf-8') as f:
   f.write('\n=== CELL START ===\n'+' '.join(cmd)+'\n');f.flush()
   proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
   for line in proc.stdout:
    print(line,end='',flush=True);f.write(line);f.flush()
   code=proc.wait();f.write('CELL_EXIT_CODE='+str(code)+'\n')
  if code:raise SystemExit('CELL_FAILED: '+str(logfile)+' EXIT_CODE='+str(code))
  print('CELL_PASS',model,precision,condition,flush=True)
 print('E1_'+args.mode.upper()+('_DRY_RUN_PLAN_ONLY' if args.dry_run else '_RUN_RETURNED_SUCCESS'),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['smoke','full'],required=True)
 p.add_argument('--inputs',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True)
 p.add_argument('--results',type=Path,required=True);p.add_argument('--dry-run',action='store_true')
 run(p.parse_args())
