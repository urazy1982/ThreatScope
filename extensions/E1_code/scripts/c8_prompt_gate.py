#!/usr/bin/env python3
"""CPU prompt-byte audit; optionally checks exact token ID Hamming distances.

No inference, weights or CUDA are used. Token-ID evidence requires access to
pinned model tokenizer snapshots. Missing snapshots yield BLOCKED, not PASS.
"""
import argparse,hashlib,json,sys,collections,itertools
from pathlib import Path

def sha(t):return hashlib.sha256(t.encode()).hexdigest()
def write(o,p):Path(p).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
def pairwise_token_counts(variants):
 if len(variants)!=8:raise ValueError('EIGHT_PROMPT_VARIANTS_REQUIRED')
 counter=collections.Counter()
 for left,right in itertools.combinations(variants,2):
  counter['pairs']+=1
  if len(left)!=len(right):counter['unequal']+=1;continue
  diff=sum(x!=y for x,y in zip(left,right))
  counter['max_hamming']=max(counter['max_hamming'],diff)
  counter['one']+=diff==1;counter['multi']+=diff>1
  counter['zero']+=diff==0
 return counter

def merge_window_counts(total, observed):
 """Sum count fields, but pool the maximum Hamming distance by max."""
 total['max_hamming'] = max(total['max_hamming'], observed['max_hamming'])
 for key in ('pairs', 'unequal', 'one', 'multi', 'zero'):
  total[key] += observed[key]
 return total

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--release',type=Path,required=True);ap.add_argument('--inputs',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--tokenizer-id-check',action='store_true');a=ap.parse_args()
 sys.path.insert(0,str(a.release/'src/v221_mechanism'))
 from v22core.core import prompt,SYS,SYS_SINGLE
 from v22core.tokenizer_gate import model_messages,extract_ids
 windows=[json.loads(line) for line in a.inputs.read_text().splitlines() if line.strip()]
 assert len(windows)==144
 config=json.loads((a.release/'data/config/study.json').read_text());assert len(config['models'])==3
 total=0;bad=[]; modelreport=[]
 for w in windows:
  strings=[prompt(w,k) for k in range(8)]
  assert all(len(s)==len(strings[0]) for s in strings)
  for e in range(8):
   for k in range(e):
    changed=[i for i,(x,y) in enumerate(zip(strings[e],strings[k])) if x!=y]
    total+=1
    if len(changed)!=1 or strings[e][changed[0]]!=str(e) or strings[k][changed[0]]!=str(k):bad.append((w['window_id'],e,k,len(changed)))
 assert not bad,bad[:5]
 result={'status':'TEXT_MUTATION_PASS_TOKEN_ID_NOT_VERIFIED','textual_pairwise_checks':total,'windows':144,
         'input_sha256':hashlib.sha256(a.inputs.read_bytes()).hexdigest(),
         'config_sha256':hashlib.sha256((a.release/'data/config/study.json').read_bytes()).hexdigest(),
         'tokenizer_gate_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'condition':'single index character changes in prompt(w,k), identical length','no_actual_tokenizer_id_test':True,
         'archived_report':'tokenizer_gate_v221.json reports equal token lengths for B/C, not token-ID Hamming distance',
         'models':[]}
 if a.tokenizer_id_check:
  try:from transformers import AutoTokenizer
  except ImportError as e:
   result['tokenizer_id_status']='BLOCKED_MISSING_TRANSFORMERS';result['blocker']=str(e)
   a.out.parent.mkdir(parents=True,exist_ok=True);write(result,a.out);print(json.dumps(result,indent=2));return 2
  try:
   for model,revision in config['models'].items():
    tok=AutoTokenizer.from_pretrained(model,revision=revision,local_files_only=True,trust_remote_code=False,use_fast=True)
    m={'model':model,'revision':revision,'observed_tokenizer_commit':getattr(tok,'init_kwargs',{}).get('_commit_hash'),'total_prompt_comparisons':0,'unequal_length_pairs':0,'one_token_hamming_pairs':0,'more_than_one_token_changed_pairs':0,'max_hamming_distance':0,'by_instruction':{}}
    if m['observed_tokenizer_commit'] is not None and m['observed_tokenizer_commit']!=revision:
     raise RuntimeError('PINNED_TOKENIZER_REVISION_DRIFT '+model)
    for regime,instruction in [('B',SYS),('C',SYS_SINGLE)]:
     counter=collections.Counter()
     for w in windows:
      variants=[]
      for anchor in range(8):
       msgs=model_messages(model,prompt(w,anchor),instruction)
       arr=tok.apply_chat_template(msgs,tokenize=True,add_generation_prompt=True)
       ids=extract_ids(arr)
       variants.append(ids)
      # Check all 28 combinations, not only seven pairs vs anchor 0.
      merge_window_counts(counter, pairwise_token_counts(variants))
     if counter['pairs']!=4032 or (counter['unequal']+counter['one']+counter['multi']+counter['zero'])!=counter['pairs']:
      raise RuntimeError('TOKENIZER_PAIRWISE_AGGREGATE_INCONSISTENT '+model+' '+regime)
     m['by_instruction'][regime]=dict(counter)
     m['total_prompt_comparisons']+=counter['pairs'];m['unequal_length_pairs']+=counter['unequal'];m['one_token_hamming_pairs']+=counter['one'];m['more_than_one_token_changed_pairs']+=counter['multi'];m['max_hamming_distance']=max(m['max_hamming_distance'],counter['max_hamming'])
    if m['total_prompt_comparisons']!=8064 or m['unequal_length_pairs']>0:
     raise RuntimeError('TOKENIZER_PAIR_COVERAGE_OR_LENGTH_MISMATCH '+model)
    result['models'].append(m)
   result['tokenizer_id_status']='PASS_OBSERVED_TOKENIZER_COMPARISON'
   result['status']='TOKENIZER_ID_MEASURED_AND_RECORDED'
   result['no_actual_tokenizer_id_test']=False
  except Exception as e:
   result['tokenizer_id_status']='BLOCKED_MODEL_TOKENIZER_NOT_CACHED_OR_REVISION_UNAVAILABLE';result['blocker']=repr(e)
 a.out.parent.mkdir(parents=True,exist_ok=True);write(result,a.out);print(json.dumps(result,indent=2));return 0 if result.get('tokenizer_id_status')=='PASS_OBSERVED_TOKENIZER_COMPARISON' else 2
 a.out.parent.mkdir(parents=True,exist_ok=True);write(result,a.out)
if __name__=='__main__':sys.exit(main() or 0)
