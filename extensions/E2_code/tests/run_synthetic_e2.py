#!/usr/bin/env python3
"""CPU-only software rehearsal using deliberately synthetic E2 checkpoints.

The 'choices' equal the archived Arm C winners by construction, so the resulting
zero procedure contrast is NOT a newly measured GPU effect.
"""
import argparse,csv,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from vendor.e1_neutral_gpu import verify_frozen_inputs,sha,canonical,atomic
from vendor.v22core.core import SYS_SINGLE,prompt
from vendor.v22core.tokenizer_gate import model_messages
from scripts.e2_singleton_gpu import identity_for,PROTOCOL_ID

def run(inputs,manifest):
    model='Qwen/Qwen2.5-3B-Instruct';slug='qwen2.5-3b'
    m,ws,cfg=verify_frozen_inputs(inputs,manifest,model)
    with (ROOT/'reference/archived_armC_6912_winners.csv').open() as f:
        raw=list(csv.DictReader(f))
    reference={(r['precision'],r['window_id'],int(r['anchor'])):int(r['winner']) for r in raw if r['model']==model}
    if len(reference)!=2304:raise RuntimeError('HISTORICAL_REFERENCE_MISSING')
    with tempfile.TemporaryDirectory(prefix='e2_synthetic_') as d:
        base=Path(d)/'results';analysis=Path(d)/'analysis'
        for prec in ('bf16','nf4'):
            folder=base/slug/prec;folder.mkdir(parents=True)
            ident=identity_for(m,cfg,model,prec,(manifest,ROOT/'scripts/e2_singleton_gpu.py'))
            atomic(folder/'identity.json',ident)
            for w in ws:
                for anchor in range(8):
                    idx=reference[prec,w['window_id'],anchor]
                    rawjson='{"relevant":['+str(idx)+']}'
                    r={'protocol':PROTOCOL_ID,'model':model,'precision':prec,
                       'revision':cfg['models'][model],'window_id':w['window_id'],
                       'report_id':w['report_id'],'source':w['source'],'anchor':anchor,
                       'input_sha256':w['input_sha256'],'identity_sha256':sha(canonical(ident)),
                       'prompt_sha256':sha(canonical(model_messages(model,prompt(w,anchor),SYS_SINGLE))),
                       'generated_ids':[100,idx,200],  # SYNTHETIC, NEVER TOKENIZER-AUTHENTICATED
                       'raw':rawjson,'raw_sha256':sha(rawjson),'selected_index':idx,
                       'valid':True,'prompt_tokens':128,'generated_tokens':3,'elapsed_seconds':0}
                    r['record_sha256']=sha(canonical(r))
                    atomic(folder/'windows'/w['window_id']/f'anchor_{anchor}.json',r)
        cmd=[sys.executable,str(ROOT/'scripts/analyze_e2.py'),'--inputs',str(inputs),'--manifest',str(manifest),'--results',str(base),'--out',str(analysis),'--model',model]
        result=subprocess.run(cmd,check=True,capture_output=True,text=True)
        summary=json.loads((analysis/'E2_summary.json').read_text())
        assert summary['windows']==144
        assert summary['greedy_generations']==2304
        assert abs(summary['difference_of_precision_deltas_pp'])<1e-10
        assert summary['greedy_vs_scoring_agreement_bf16']==1.0
        assert summary['greedy_vs_scoring_agreement_nf4']==1.0
        print('SYNTHETIC_E2_FULL_CHECKPOINT_REHEARSAL_PASS',
              '2304 mock records, 144 matched windows, historical Arm C effect alignment; NOT new GPU evidence')
        # Negative: source-checkpoint mutation must block statistical analysis.
        target=base/slug/'bf16'/'windows'/ws[0]['window_id']/'anchor_0.json'
        obj=json.loads(target.read_text());obj['selected_index']=7 if obj['selected_index']!=7 else 0
        atomic(target,obj)
        bad=subprocess.run(cmd,capture_output=True,text=True)
        assert bad.returncode!=0 and ('RECORD' in bad.stderr or 'DRIFT' in bad.stderr),bad.stderr
        print('E2_SYNTHETIC_CHECKPOINT_TAMPER_REJECTED_PASS')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--inputs',type=Path,required=True)
    ap.add_argument('--manifest',type=Path,required=True)
    a=ap.parse_args();run(a.inputs,a.manifest)
