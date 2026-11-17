"""SYNTHETIC SOFTWARE REGRESSION. Never treat this output as neural inference."""
import argparse,hashlib,json,sys,tempfile,csv
from pathlib import Path
p=argparse.ArgumentParser(description='CPU-only synthetic integration; NEVER inference results')
p.add_argument('--inputs',type=Path,required=True)
p.add_argument('--manifest',type=Path,required=True)
a=p.parse_args()
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from e1_neutral_gpu import canonical,sha,SYS,PROTOCOL_ID,build_messages,verify_frozen_inputs
from orchestrate_e1 import MODELS
from audit_e1 import verify_cell
from analyze_e1 import main as analyze_main
from verify_gpu_authorization import verify as verify_gpu_auth
inputs=a.inputs
manifest_path=a.manifest
m,windows,cfg=verify_frozen_inputs(inputs,manifest_path)
with tempfile.TemporaryDirectory(prefix='threatscope_v112_mock_') as td:
    out=Path(td);issue_id=windows[6]['window_id'];empty_id=windows[7]['window_id']
    for model,slug in MODELS.items():
      for prec in ('bf16','nf4'):
       for cond in ('N0','N1'):
        d=out/'E1'/slug/prec/cond;d.mkdir(parents=True)
        ident=dict(protocol=PROTOCOL_ID,model=model,revision=cfg['models'][model],precision=prec,condition=cond,
         manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),inputs_sha256=m['input_sha256'],sys_sha256=sha(SYS),
         code_sha256=hashlib.sha256((R/'scripts/e1_neutral_gpu.py').read_bytes()).hexdigest(),
         torch='2.10.0+cu128',transformers='5.22.2',bitsandbytes='0.50.2',
         generation={'do_sample':False,'num_beams':1,'max_new_tokens':96,'pad_token_id':'eos'},additional_dependencies={'huggingface-hub':'SYNTHETIC_ONLY'})
        (d/'identity.json').write_text(json.dumps(ident))
        provenance=dict(model=model,revision=cfg['models'][model],precision=prec,verified_4bit_linear_modules=4 if prec=='nf4' else 0,
          tokenizer_chat_template_sha256=sha('MOCK_TEMPLATE_DO_NOT_USE'),cuda_device='SYNTHETIC_GPU_DO_NOT_CLAIM',
          pytorch='2.10.0+cu128',transformers='5.22.2',bitsandbytes='0.50.2',
          model_config_commit=cfg['models'][model],tokenizer_init_commit=cfg['models'][model],additional_dependencies={'huggingface-hub':'SYNTHETIC_ONLY'})
        (d/'load_provenance.json').write_text(json.dumps(provenance))
        invalid_count=0
        for w in windows:
         raw='{"relevant":['+('0' if prec=='bf16' else '1')+']}'
         if model=='Qwen/Qwen2.5-3B-Instruct' and prec=='nf4' and cond=='N1' and w['window_id']==issue_id:raw='malformed-json'
         if model=='Qwen/Qwen2.5-3B-Instruct' and prec=='bf16' and cond=='N1' and w['window_id']==empty_id:raw='{"relevant":[]}'
         from e1_neutral_gpu import parse_output
         valid,idx,err=parse_output(raw);invalid_count+=not valid
         rec=dict(window_id=w['window_id'],input_sha256=w['input_sha256'],prompt_sha256=sha(canonical(build_messages(model,w,cond))),
             identity=sha(canonical(ident)),raw=raw,raw_sha256=sha(raw),valid=valid,indices=idx,error=err,
             prompt_tokens=256,generated_tokens=10,generation_cap_reached=False,elapsed_seconds=0.0)
         rec['record_sha256']=sha(canonical(rec))
         (d/(w['window_id']+'.json')).write_text(json.dumps(rec))
        (d/'cell_status.json').write_text(json.dumps(dict(model=model,precision=prec,condition=cond,requested_windows=144,
            completed_windows=144,valid_windows=144-invalid_count,invalid_windows=invalid_count,
            complete_full_cell=True,identity=sha(canonical(ident)))))
        rep=verify_cell(d,model,prec,cond,windows,m,cfg,144,hashlib.sha256(manifest_path.read_bytes()).hexdigest())
        if prec=='nf4' and cond=='N1' and model=='Qwen/Qwen2.5-3B-Instruct':
          assert rep['invalid']==1 and rep['valid_empty_windows']==0,rep
        if prec=='bf16' and cond=='N1' and model=='Qwen/Qwen2.5-3B-Instruct':
          assert rep['invalid']==0 and rep['valid_empty_windows']==1,rep
    # Test stale tokenizer evidence rejected: there is no valid C8 report.
    try:verify_gpu_auth(inputs,manifest_path,out,R,'full')
    except RuntimeError as e:assert 'C8_' in str(e),str(e)
    else:raise AssertionError('INVALID_GPU_AUTHORIZATION_ACCEPTED')
    # Software-only positive and negative checks with a plainly fake local
    # tokenizer certificate. This is NOT real tokenizer evidence.
    c8=out/'preflight/C8_actual_tokenizer_ids.json';c8.parent.mkdir(exist_ok=True)
    info={'status':'TOKENIZER_ID_MEASURED_AND_RECORDED','tokenizer_id_status':'PASS_OBSERVED_TOKENIZER_COMPARISON',
       'input_sha256':m['input_sha256'],'config_sha256':m['config_sha256'],
       'tokenizer_gate_script_sha256':hashlib.sha256((R/'scripts/c8_prompt_gate.py').read_bytes()).hexdigest(),
       'models':[{'model':x,'revision':revision,'observed_tokenizer_commit':revision,
         'total_prompt_comparisons':8064,'unequal_length_pairs':0,
         'by_instruction':{'B':{'pairs':4032},'C':{'pairs':4032}}} for x,revision in cfg['models'].items()]}
    c8.write_text(json.dumps(info))
    assert verify_gpu_auth(inputs,manifest_path,out,R,'smoke')['status']=='E1_LAUNCH_AUTHORIZATION_PASS'
    assert verify_gpu_auth(inputs,manifest_path,out,R,'full')['smoke_verified']
    info['tokenizer_gate_script_sha256']='tampered-certification-sha'
    c8.write_text(json.dumps(info))
    try:verify_gpu_auth(inputs,manifest_path,out,R,'full')
    except RuntimeError as e:assert 'STALE_OR_WRONG_C8' in str(e)
    else:raise AssertionError('TAMPERED_GPU_AUTHORIZATION_ACCEPTED')
    # Synthetic records are kept entirely temporary; test real CPU pipeline.
    sys.argv=['analyze_e1','--inputs',str(inputs),'--manifest',str(manifest_path),
         '--results',str(out),'--labels',str(R/'reports/C4_exact_288_textfree.csv'),
         '--out',str(out/'analysis')]
    analyze_main()
    with (out/'analysis/E1_stability_summary.csv').open() as f:
     st=list(csv.DictReader(f))
    with (out/'analysis/E1_cell_quality.csv').open() as f:cells=list(csv.DictReader(f))
    assert len(st)==3 and len(cells)==12,(len(st),len(cells))
    assert (out/'analysis/E1_prompt_F1_contrasts.csv').exists()
    assert (out/'analysis/E1_stability_window.csv').exists()
    assert st[0]['matched_windows']=='143',st[0]
    assert (out/'analysis/E1_stability_window.csv').read_text().count('\n')==433
    print('SYNTHETIC_FULL_SOFTWARE_REHEARSAL_PASS 12x144=1728 mock checkpoints, 12 quality cells, 3 direct stability summaries')
    print('INVALID_AND_EMPTY_OUTPUT_SEPARATION_PASS; STALE_OR_TAMPERED_AUTHORIZATION_DENIED_PASS; MOCK_AUTHORIZATION_CODE_PATH_PASS')
print('TEMPORARY_SYNTHETIC_CHECKPOINTS_DELETED')
