"""CPU tokenizer gate for all 8 anchor examples and all sampled inputs."""
from __future__ import annotations
import argparse,json,collections
from .analyze import verify_prepared
from .core import SYS,prompt,read
from .runner import model_messages

def count_chat_tokens(tok, messages):
    """Count real IDs, accepting both Tensor and BatchEncoding outputs."""
    from .token_encoding import chat_input_ids
    output = tok.apply_chat_template(messages, tokenize=True,
                                     add_generation_prompt=True,
                                     return_tensors='pt')
    count = int(chat_input_ids(output).shape[1])
    if count < 64:
        raise RuntimeError('PREFLIGHT_IMPLAUSIBLY_SHORT_PROMPT ' + str(count))
    return count

def run(root):
    from transformers import AutoTokenizer
    cfg,m,windows=verify_prepared(root)
    summary=[]
    for model,rev in cfg['models'].items():
        tok=AutoTokenizer.from_pretrained(model,revision=rev,trust_remote_code=False,use_fast=True)
        max_l=0;unequal=[]
        for w in windows:
            lengths=[count_chat_tokens(tok,model_messages(model,prompt(w,k))) for k in range(8)]
            if len(set(lengths))!=1:unequal.append((w['window_id'],lengths))
            max_l=max(max_l,*lengths)
        ok=not unequal and max_l<=cfg['max_input_tokens']
        summary.append({'model':model,'max_input_tokens':max_l,'unequal_windows':len(unequal),'ok':ok})
        if not ok:raise RuntimeError('TOKENIZER_GATE_FAIL '+model+' '+str(unequal[:2]))
    return summary

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',default='.');a=p.parse_args()
    print(json.dumps(run(a.root),indent=2))
if __name__=='__main__':main()
