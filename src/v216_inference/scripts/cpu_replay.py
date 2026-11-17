"""Synthetic-only integration test. NEVER treat synthetic effects as real science."""
from __future__ import annotations
import argparse,hashlib,json,random,tempfile,shutil
from pathlib import Path
from crosscti.core import write,read,lines,digest,prompt,parse,cell_id
from crosscti.prepare import prepare
from crosscti.runner import expected_identity,validate_checkpoint
from crosscti.analyze import analyze,verify_prepared,exact_sign_flip

def synthetic_records(cfg):
    result=[]
    for si,s in enumerate(cfg['source_names']):
        for ri in range(10):
            paras=[]
            for i in range(24):
                paras.append(f'The investigative analyst observed simulated malware activity on network segment {i+1} during fictional response case {si+1}-{ri+1}.')
            result.append({'CTI':{'source':s,'text':'\n\n'.join(paras)}})
    return result

def create_synthetic(root):
    cfg=read(root/'config/study.json');source=root/'outputs/synthetic_reports.json'
    write(source,synthetic_records(cfg))
    m=prepare(source,root)
    assert m['windows']==160 and m['total_calls']==7680,(m['windows'],m['total_calls'])
    return m

def fill_fake(root,alter=False):
    cfg,m,windows=verify_prepared(root)
    for model_i,(model,rev) in enumerate(cfg['models'].items()):
      for precision in cfg['precisions']:
        base=root/'outputs/runs'/cell_id(model,precision)
        meta=expected_identity(root,model,precision);write(base/'run_metadata.json',meta)
        ih=digest(meta)
        for w in windows:
          for k in range(8):
            # Scripted indices, not neural predictions: BF16 weak self-preference,
            # NF4 stronger self-preference; report data remain synthetic.
            self_preference=(int(w['window_id'][:2],16)+k+model_i)%7
            selected=[j for j in range(8) if (j+int(w['window_id'][:2],16)+model_i)%7==0]
            if precision=='nf4' and self_preference<=2: selected.append(k)
            if precision=='bf16' and self_preference==0: selected.append(k)
            selected=sorted(set(selected))
            raw=json.dumps({'relevant':selected},separators=(',',':'))
            p=parse(raw)
            rec={'window_id':w['window_id'],'input_sha256':w['input_sha256'],'anchor':k,
                'model':model,'precision':precision,'revision':rev,
                'identity_sha256':ih,'prompt_sha256':digest([__import__('crosscti.core',fromlist=['SYS']).SYS,prompt(w,k),model]),
                'raw':raw,'raw_sha256':digest(raw),'valid':p['valid'],'indices':p['indices'],'error':p['error'],
                'input_tokens':123,'generated_tokens':12,'generation_cap_reached':False,'latency_seconds':0.0}
            rec['record_sha256']=digest(rec)
            write(base/f'example_{k}'/(w['window_id']+'.json'),rec)
    return len(windows)*8*len(cfg['models'])*len(cfg['precisions'])

def run(root):
    root=Path(root)
    # Never touch real outputs: create a distinct, temporary synthetic fixture
    with tempfile.TemporaryDirectory(prefix='threat_v2_cpu_') as p:
        fake=Path(p)
        (fake/'config').mkdir();shutil.copy2(root/'config/study.json',fake/'config/study.json')
        m=create_synthetic(fake);n=fill_fake(fake)
        summary=analyze(fake)
        assert n==7680 and summary['rows']==n
        assert summary['source_count']==10 and len(summary['models'])==3
        # Verify no overclaiming a randomization p-value from report pseudoreplication
        assert exact_sign_flip([1.0]*10)==2/1024
        # Check tamper detection on a single raw response
        cfg=read(fake/'config/study.json');w=lines(fake/'outputs/prepared/inputs.jsonl')[0]
        model=next(iter(cfg['models']));rev=cfg['models'][model]
        fp=fake/'outputs/runs'/cell_id(model,'nf4')/'example_0'/(w['window_id']+'.json')
        r=read(fp);r['raw']='{"relevant":[]}';write(fp,r)
        try:validate_checkpoint(fp,w,0,model,'nf4',rev,digest(expected_identity(fake,model,'nf4')))
        except RuntimeError:pass
        else:raise AssertionError('TAMPER_NOT_DETECTED')
        print('SYNTHETIC_CPU_FULL_MATRIX_PASS',n,'publisher_groups',10)
        print('SYNTHETIC_MODEL_SUMMARIES',json.dumps(summary['models'],indent=2))
        print('CHECKPOINT_TAMPER_REJECTED_PASS')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default='.');run(Path(p.parse_args().root).resolve())
