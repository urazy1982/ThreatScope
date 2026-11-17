#!/usr/bin/env python3
"""Optional CPU-only download of precisely pinned tokenizers (never model weights)."""
import argparse,sys,zipfile,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--release',type=Path,default=Path(__file__).resolve().parents[1]/'upstream/ThreatScope_v1.0.0.zip');a=p.parse_args()
try:
 from transformers import AutoTokenizer
except ImportError as e:raise SystemExit('INSTALL_TRANSFORMERS_IN_LOCAL_RESEARCH_VENV_FIRST: '+str(e))
with zipfile.ZipFile(a.release) as z:
 cfg=json.loads(z.read('ThreatScope/data/config/study.json'))
for model,rev in cfg['models'].items():
 print('CACHING_PINNED_TOKENIZER',model,rev,flush=True)
 try:
  tok=AutoTokenizer.from_pretrained(model,revision=rev,trust_remote_code=False,use_fast=True)
  print('TOKENIZER_READY',model,'vocab',len(tok),flush=True)
 except Exception as e:
  print('BLOCKED',model,repr(e),file=sys.stderr);sys.exit(2)
print('PINNED_TOKENIZER_CACHE_PASS (CPU only; token-ID gate still required)')
