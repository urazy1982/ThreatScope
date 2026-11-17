"""Arm B: the 256 canonical, unique-index JSON outputs and a tokenizer-aware prefix trie.

The 256-output canonical language is a deliberately stricter output language than the
permissive v2.1.6 parser (which accepts whitespace and permutations). It is equivalent
at the level of SETS OF INDICES, not literal JSON byte strings.
"""
from __future__ import annotations
from .core import parse

def canonical(indices):
    seq=sorted(indices)
    if len(set(seq))!=len(seq) or any(type(x) is not int or x not in range(8) for x in seq):
        raise ValueError('BAD_SUBSET')
    return '{"relevant":['+','.join(map(str,seq))+']}'

def canonical_language():
    return tuple(canonical(i for i in range(8) if mask>>i&1) for mask in range(256))

def verify_language():
    forms=canonical_language()
    if len(forms)!=256 or len(set(forms))!=256:raise RuntimeError('LANGUAGE_NOT_256')
    for text in forms:
        p=parse(text)
        if not p['valid'] or canonical(p['indices'])!=text:raise RuntimeError('PARSER_GRAMMAR_CONFLICT')
    assert not parse('{"relevant":[0,0]}')['valid']
    assert not parse('{"relevant":[8]}')['valid']
    return {'valid_canonical_outputs':256,'parser_equivalence_over_canonical_subsets':True,
            'restriction':'Canonical ascending subsets only; parser also accepts other JSON spellings'}

class TokenTrie:
    END=None
    def __init__(self,encode,decode,eos_token_id):
        self.root={}; self.eos=int(eos_token_id); self.encoded=[]
        if self.eos < 0:raise ValueError('BAD_EOS')
        for output in canonical_language():
            ids=tuple(encode(output))
            if not ids or any(type(i) is not int or i<0 for i in ids):raise ValueError('BAD_TOKEN_IDS')
            if self.eos in ids:raise ValueError('EOS_INSIDE_JSON_TOKENS')
            text=decode(list(ids))
            if text!=output:raise ValueError('TOKENIZER_NOT_CANONICAL_ROUNDTRIP '+repr(output)+' '+repr(text))
            self.encoded.append(ids)
            node=self.root
            for x in ids:node=node.setdefault(x,{})
            node[self.END]={}
        if len(set(self.encoded))!=256:raise RuntimeError('TOKEN_COLLISION')
    def allowed(self,prefix):
        node=self.root
        for n in prefix:
            if n==self.eos:return ()
            if int(n) not in node:return ()
            node=node[int(n)]
        return tuple(sorted(self.eos if n is None else n for n in node))
    def accepts(self,ids):
        if not ids or ids[-1]!=self.eos:return False
        return tuple(ids[:-1]) in set(self.encoded)
    def summary(self):
        sizes=list(map(len,self.encoded))
        return {'canonical_outputs':len(self.encoded),'min_output_tokens':min(sizes),
                'max_output_tokens':max(sizes),'prefix_nodes':_count_nodes(self.root)}

def _count_nodes(node):return 1+sum(_count_nodes(c) for k,c in node.items() if k is not None)
