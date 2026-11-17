#!/usr/bin/env python3
import sys,argparse,json,csv,hashlib,collections,itertools,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.e3_runner import load_frozen,validate_checkpoint,PROTOCOL,sha_file
from vendor.core import digest,read

def run(args):
 ws,gate,cfg=load_frozen(Path(args.inputs),Path(args.gate),Path(args.config))
 output=Path(args.results);by=[];all_rows=[]
 for model,revision in cfg['models'].items():
  for prec in cfg['precisions']:
   base=output/{'Qwen/Qwen2.5-3B-Instruct':'qwen2.5-3b-instruct','meta-llama/Llama-3.2-3B-Instruct':'llama-3.2-3b-instruct','mistralai/Mistral-7B-Instruct-v0.3':'mistral-7b-instruct-v0-3'}[model]/prec
   meta=base/'run_metadata.json'
   if not meta.exists():
    if args.allow_partial:continue
    raise RuntimeError('CELL_METADATA_MISSING '+str(base))
   ident=read(meta);assert ident['protocol']==PROTOCOL and ident['input_sha256']==gate['new_inputs_sha256']
   assert ident['runner_sha256']==sha_file(Path(__file__).resolve().parent/'e3_runner.py'),'RUNNER_SHA_DRIFT'
   ih=digest(ident);total=0;valid=0
   for w in ws:
    for k in range(8):
     f=base/f'example_{k}'/(w['window_id']+'.json')
     if not f.exists():
      if args.allow_partial:continue
      raise RuntimeError('MISSING_CHECKPOINT '+str(f))
     rec=validate_checkpoint(f,w,k,model,prec,revision,ih)
     total+=1;valid+=int(rec['valid'])
     all_rows.append({'model':model,'precision':prec,'source':w['source'],'report_id':w['report_id'],'window_id':w['window_id'],'anchor':k,'valid':rec['valid'],'indices':rec['indices'],'input_sha256':w['input_sha256'],'prompt_sha256':rec['prompt_sha256'],'record_sha256':rec['record_sha256']})
   by.append({'model':model,'precision':prec,'total':total,'valid':valid,'invalid':total-valid})
   print('E3_AUDIT_CELL',model,prec,total,valid,flush=True)
 if not args.allow_partial:assert len(by)==6 and len(all_rows)==3456,'INCOMPLETE_MATRIX'
 out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
 report={'status':'PASS' if len(all_rows)==3456 else 'PARTIAL','protocol':PROTOCOL,'input_sha256':gate['new_inputs_sha256'],'cells':by,'total':len(all_rows)}
 (out/'E3_audit.json').write_text(json.dumps(report,indent=2)+'\n')
 with (out/'E3_decisions_textfree.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=['model','precision','source','report_id','window_id','anchor','valid','indices','input_sha256','prompt_sha256','record_sha256']);writer.writeheader()
  for r in all_rows:writer.writerow({**r,'indices':json.dumps(r['indices'],separators=(',',':'))})
 if len(all_rows)!=3456:return
 # Historical D: difference in selection frequency for index k versus other indices, for each window
 import statistics
 records={(r['model'],r['precision'],r['window_id'],r['anchor']):r for r in all_rows}
 windows=[]
 for model in cfg['models']:
  for prec in cfg['precisions']:
   for w in ws:
    recs=[records[(model,prec,w['window_id'],k)] for k in range(8)]
    # Mark invalid selection as empty as in historical Arm A; index-k dependence evaluated over 8x8 decisions.
    vals=[]
    for k in range(8):
     for j in range(8):
      vals.append((k,j, int(recs[k]['valid'] and j in recs[k]['indices'])))
    match=sum(v for k,j,v in vals if k==j)/8
    other=sum(v for k,j,v in vals if k!=j)/56
    windows.append({'model':model,'precision':prec,'source':w['source'],'report_id':w['report_id'],'window_id':w['window_id'],'D':match-other,'invalid_prompts':sum(not r['valid'] for r in recs)})
 with (out/'E3_window_effects.csv').open('w',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=list(windows[0]));wr.writeheader();wr.writerows(windows)
 pubs=[]
 for model in cfg['models']:
  for source in sorted(set(w['source'] for w in ws)):
   a=[]
   for prec in cfg['precisions']:
    x=[r['D'] for r in windows if r['model']==model and r['source']==source and r['precision']==prec]
    assert x
    a.append(sum(x)/len(x))
   pubs.append({'model':model,'source':source,'D_bf16':a[0],'D_nf4':a[1],'delta':a[1]-a[0]})
 with (out/'E3_publisher_effects.csv').open('w',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=list(pubs[0]));wr.writeheader();wr.writerows(pubs)
 summ=[]
 for model in cfg['models']:
  vals=[r['delta'] for r in pubs if r['model']==model];obs=sum(vals)/len(vals)
  all_signed=[abs(sum(v*sign for v,sign in zip(vals,sgn))/len(vals)) for sgn in itertools.product((-1,1),repeat=len(vals))]
  p=sum(x>=abs(obs)-1e-12 for x in all_signed)/len(all_signed)
  summ.append({'model':model,'publishers':len(vals),'nf4_minus_bf16_pp':round(obs*100,6),'exact_signflip_p_exploratory':p,'validity_note':'8-publisher historical-archive retrospective holdout; not independent corpus'})
 (out/'E3_summary.json').write_text(json.dumps({'status':'COMPUTED','rows':summ},indent=2)+'\n')
 print('E3_AUDIT_ANALYSIS_PASS',len(all_rows),'checkpoint records',flush=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('--inputs',required=True);p.add_argument('--gate',required=True);p.add_argument('--config',required=True);p.add_argument('--results',required=True);p.add_argument('--out',required=True);p.add_argument('--allow-partial',action='store_true');run(p.parse_args())
if __name__=='__main__':main()
