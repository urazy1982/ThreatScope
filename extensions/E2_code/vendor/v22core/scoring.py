"""Arm C teacher-forced candidate scoring. Works on CPU torch and CUDA torch.

The required end-of-turn token is model-specific, must be verified by the local
tokenizer full-chat roundtrip before inference. No length normalization.
"""
from __future__ import annotations
import math
from .constraints import canonical

END_MARKER={'Qwen/Qwen2.5-3B-Instruct':'<|im_end|>',
            'meta-llama/Llama-3.2-3B-Instruct':'<|eot_id|>',
            'mistralai/Mistral-7B-Instruct-v0.3':'</s>'}

def candidates():return [canonical([i]) for i in range(8)]

def argmax_lowest(scores):
    if len(scores)!=8 or any(not math.isfinite(float(s)) for s in scores):raise ValueError('BAD_SCORES')
    winner=max(range(8),key=lambda i:float(scores[i]))
    top=max(scores)
    return {'index':winner,'exact_ties':sum(float(s)==float(top) for s in scores),'scores':[float(s) for s in scores]}

def softmax(scores):
    if len(scores)!=8 or any(not math.isfinite(float(s)) for s in scores):raise ValueError('BAD_SCORES')
    high=max(scores);xs=[math.exp(float(s)-high) for s in scores];total=sum(xs)
    return [x/total for x in xs]

def score_candidates_batch(model,prompt_ids,continuations,pad_token_id):
    """One batched model forward over eight prompt+candidate sequences (not KV-shared).

    model: callable returning an object with .logits [B,L,V].  Candidate continuation
    includes the frozen model-specific end-of-turn ID. No sampled decoding involved.
    """
    import torch
    if len(continuations)!=8:raise ValueError('EIGHT_CANDIDATES_REQUIRED')
    if not isinstance(prompt_ids,torch.Tensor) or prompt_ids.ndim!=2 or prompt_ids.shape[0]!=1 or prompt_ids.shape[1]<1:
        raise ValueError('INVALID_PROMPT_TENSOR')
    if any(not x or any(type(t) is not int or t<0 for t in x) for x in continuations):
        raise ValueError('BAD_CONTINUATION')
    P=prompt_ids.shape[1];N=max(len(c) for c in continuations);dev=prompt_ids.device
    full=torch.full((8,P+N),int(pad_token_id),device=dev,dtype=torch.long)
    mask=torch.zeros((8,P+N),device=dev,dtype=torch.long)
    full[:,:P]=prompt_ids.expand(8,-1);mask[:,:P]=1
    for i,c in enumerate(continuations):
        full[i,P:P+len(c)]=torch.tensor(c,device=dev,dtype=torch.long)
        mask[i,P:P+len(c)]=1
    with torch.inference_mode():
        output=model(input_ids=full,attention_mask=mask,use_cache=False)
        logits=output.logits
        if logits.ndim!=3 or logits.shape[:2]!=(8,P+N):raise RuntimeError('LM_LOGIT_SHAPE')
        res=[]
        for i,c in enumerate(continuations):
            targets=full[i,P:P+len(c)]
            # logits at position t-1 predict the target token at position t.
            pred=logits[i,P-1:P-1+len(c)].to(torch.float32)
            vals=torch.log_softmax(pred,dim=-1).gather(1,targets.unsqueeze(1)).squeeze(1)
            x=float(vals.sum().item())
            if not math.isfinite(x):raise RuntimeError('NONFINITE_CANDIDATE_SCORE')
            res.append(x)
    return {'scores':res,'winner':argmax_lowest(res)['index'],
            'exact_ties':argmax_lowest(res)['exact_ties'],'probability_mass':softmax(res),
            'candidate_token_lengths':[len(x) for x in continuations]}

def encode_continuations(tokenizer,model_name):
    """Fail closed if model-specific end-of-turn marker cannot be authenticated."""
    marker=END_MARKER[model_name]
    tid=tokenizer.convert_tokens_to_ids(marker)
    if type(tid) is not int or tid<0 or tid==getattr(tokenizer,'unk_token_id',None):
        raise ValueError('END_MARKER_UNVERIFIED '+marker)
    decoded=tokenizer.decode([tid],skip_special_tokens=False,clean_up_tokenization_spaces=False)
    if decoded!=marker:raise ValueError('END_MARKER_ROUNDTRIP_FAIL '+repr(decoded))
    sequences=[]
    for s in candidates():
        arr=tokenizer.encode(s,add_special_tokens=False)
        if not arr or tokenizer.decode(arr,skip_special_tokens=True,clean_up_tokenization_spaces=False)!=s:
            raise ValueError('SINGLE_CHOICE_TOKENIZER_ROUNDTRIP_FAIL')
        sequences.append(list(map(int,arr))+[tid])
    return sequences

def score_candidates_serial(model,prompt_ids,continuations):
    """Memory-safe teacher-forced scoring on CUDA or CPU, one candidate at a time.

    Each candidate includes model-specific end-of-turn token; the chat-template
    gate validates its alignment. Scores sum unnormalized token log-probabilities.
    This intentionally avoids an 8-way BF16 prompt batch on 32-GB GPUs.
    """
    import torch
    if len(continuations)!=8 or any(not x for x in continuations):
        raise ValueError('EIGHT_NONEMPTY_CANDIDATES_REQUIRED')
    if not isinstance(prompt_ids,torch.Tensor) or prompt_ids.ndim!=2 or prompt_ids.shape[0]!=1 or prompt_ids.shape[1]<1:
        raise ValueError('INVALID_PROMPT_TENSOR')
    P=int(prompt_ids.shape[1]);scores=[]
    with torch.inference_mode():
        for c in continuations:
            ct=torch.tensor([c],dtype=torch.long,device=prompt_ids.device)
            tokens=torch.cat((prompt_ids,ct),dim=1)
            output=model(input_ids=tokens,attention_mask=torch.ones_like(tokens),use_cache=False)
            logits=output.logits
            if logits.ndim!=3 or logits.shape[:2]!=(1,P+len(c)):
                raise RuntimeError('LM_LOGIT_SHAPE')
            next_logits=logits[0,P-1:P-1+len(c)].to(torch.float32)
            token_logs=torch.log_softmax(next_logits,dim=-1)
            val=float(token_logs.gather(1,ct[0].unsqueeze(1)).sum().item())
            if not math.isfinite(val):raise RuntimeError('NONFINITE_CANDIDATE_SCORE')
            scores.append(val)
            del output,logits,token_logs,next_logits,tokens,ct
    winner=argmax_lowest(scores)
    return {'scores':scores,'winner':winner['index'],
        'exact_ties':winner['exact_ties'],'probability_mass':softmax(scores),
        'candidate_token_lengths':[len(c) for c in continuations]}
