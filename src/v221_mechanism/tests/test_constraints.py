import unittest
from v22core.constraints import canonical,canonical_language,verify_language,TokenTrie

class CharTokenizer:
    def __init__(self):self.eos=256
    def encode(self,s):return list(map(ord,s))
    def decode(self,t):return ''.join(map(chr,t))

class ConstraintsTests(unittest.TestCase):
    def test_all_subsets(self):
        self.assertTrue(verify_language()['parser_equivalence_over_canonical_subsets'])
    def test_unique_representations(self):self.assertEqual(len(set(canonical_language())),256)
    def test_includes_empty_full(self):
        self.assertIn('{"relevant":[]}',canonical_language())
        self.assertIn('{"relevant":[0,1,2,3,4,5,6,7]}',canonical_language())
    def test_no_duplicates(self):
        with self.assertRaises(ValueError):canonical([1,1])
    def test_out_of_range(self):
        with self.assertRaises(ValueError):canonical([8])
    def test_bad_index_types(self):
        for x in (1.0,'1',True):
            with self.subTest(x=x),self.assertRaises(ValueError):canonical([x])
    def test_build(self):
        t=CharTokenizer();self.assertEqual(TokenTrie(t.encode,t.decode,t.eos).summary()['canonical_outputs'],256)
    def test_accepts_all(self):
        t=CharTokenizer();trie=TokenTrie(t.encode,t.decode,t.eos)
        for s in canonical_language():
            seq=t.encode(s)+[t.eos]
            self.assertTrue(trie.accepts(seq))
    def test_prefix_walk(self):
        t=CharTokenizer();trie=TokenTrie(t.encode,t.decode,t.eos)
        for s in canonical_language():
            prefix=[]
            for x in t.encode(s):
                self.assertIn(x,trie.allowed(prefix));prefix.append(x)
            self.assertIn(t.eos,trie.allowed(prefix))
    def test_rejects_trailing(self):
        t=CharTokenizer();trie=TokenTrie(t.encode,t.decode,t.eos)
        self.assertFalse(trie.accepts(t.encode('{"relevant":[0,0]}')+[t.eos]))
        self.assertFalse(trie.accepts(t.encode('{"relevant":[1]}')))
        self.assertEqual(trie.allowed([999]),())
    def test_fails_broken_roundtrip(self):
        t=CharTokenizer()
        with self.assertRaises(ValueError):TokenTrie(t.encode,lambda x:'WRONG',t.eos)
    def test_fails_eos_inside(self):
        t=CharTokenizer()
        with self.assertRaises(ValueError):TokenTrie(t.encode,t.decode,ord('"'))
    def test_bad_encoding(self):
        with self.assertRaises(ValueError):TokenTrie(lambda x:[],lambda x:'',1)
