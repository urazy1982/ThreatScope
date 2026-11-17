#!/usr/bin/env python3
"""CPU-only frozen-data and protocol preparation. NEVER loads a model or CUDA."""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from e1_neutral_gpu import verify_frozen_inputs,build_prompt,sha,SYS,PROTOCOL_ID,N1_EXAMPLE_LINE
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--inputs',type=Path,required=True)
 p.add_argument('--manifest',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 manifest,windows,config=verify_frozen_inputs(a.inputs,a.manifest)
 with zipfile.ZipFile(ROOT/'upstream/ThreatScope_v1.0.0.zip') as z:
  frozen_config=z.read('ThreatScope/data/config/study.json')
 assert hashlib.sha256(frozen_config).hexdigest()==manifest['config_sha256'],'RELEASE_CONFIG_MISMATCH'
 assert json.loads(frozen_config)==config,'MODEL_REVISIONS_MISMATCH'
 models=list(config['models'])
 assert len(models)==3 and len(windows)==144
 assert all(build_prompt(w,'N1')==build_prompt(w,'N0')+N1_EXAMPLE_LINE for w in windows),'N0_N1_NOT_SINGLE_APPEND_ONLY'
 rows=[]
 for model in models:
  for precision in ('bf16','nf4'):
   for condition in ('N0','N1'):
    prompt_sizes=[len(build_prompt(w,condition)) for w in windows]
    suffix='' if condition=='N0' else N1_EXAMPLE_LINE
    rows.append(dict(model=model,revision=config['models'][model],precision=precision,condition=condition,
     windows=len(windows),max_prompt_characters=max(prompt_sizes),output_contract_sha256=sha(suffix)))
 report={'status':'E1_CPU_PREPARATION_PASS','protocol':PROTOCOL_ID,
         'windows':144,'reports':72,'publishers':9,'sentences':1152,'cells':rows,'minimal_difference_checks':144,
         'inputs_sha256':manifest['input_sha256'], 'config_sha256':manifest['config_sha256'],
         'source_release_zip_sha256':hashlib.sha256((ROOT/'upstream/ThreatScope_v1.0.0.zip').read_bytes()).hexdigest(),
         'note':'This does NOT measure GPU inference or actual tokenizer-ID Hamming distance.'}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n')
 print('E1_CPU_PREPARATION_PASS 144 windows, 72 reports, 9 publishers, 12 cells')
 print('OUTPUT',a.out)
if __name__=='__main__':main()
