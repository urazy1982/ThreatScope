import unittest,itertools,math
from v22core.core import SYS,SYS_SINGLE,prompt,parse,original_effect,mass_effect,exact_p,holm,digest

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.window={'sentences':[{'context_before':'','sentence_text':f'sentence {i}'} for i in range(8)]}
    def test_prompt_one_digit(self):
        prompts=[prompt(self.window,k) for k in range(8)]
        self.assertEqual(len({len(s) for s in prompts}),1)
        self.assertEqual(len(set(prompts)),8)
        for k in range(8):
            self.assertEqual(prompts[k].replace('"relevant":['+str(k)+']','"relevant":[X]'),
                             prompts[0].replace('"relevant":[0]','"relevant":[X]'))
    def test_prompt_repeatable(self):self.assertEqual(prompt(self.window,7),prompt(self.window,7))
    def test_prompt_wrong_window(self):
        with self.assertRaises(ValueError):prompt({'sentences':[]},0)
    def test_prompt_anchor_type(self):
        for x in (True,3.0,'3',-1,8):
            with self.subTest(x=x),self.assertRaises(ValueError):prompt(self.window,x)
    def test_single_instruction_resolves_conflict(self):
        self.assertIn('exactly one',SYS_SINGLE)
        self.assertIn('If no sentence meets',SYS_SINGLE)
        self.assertNotIn('Return an empty list',SYS_SINGLE)
        self.assertIn('Return an empty list',SYS)
    def test_valid_outputs(self):
        for s,values in [('{"relevant":[]}',[]),('{"relevant":[7,0,2]}',[0,2,7])]:
            obj=parse(s);self.assertTrue(obj['valid']);self.assertEqual(obj['indices'],values)
    def test_reject_malformed(self):
        for s in ('JSON{}','{"bad":[]}','{"relevant":[0,0]}','{"relevant":[8]}','{"relevant":[true]}',
                  '{"relevant": "0"}','{"relevant":[1.0]}','[0]', '{}'):
            with self.subTest(s=s):self.assertFalse(parse(s)['valid'])
    def test_original_matches_direct_formula(self):
        for vals in [set(),{0},{2,4},{0,1,2,3,4,5,6,7}]:
            d={e:set(vals) for e in range(8)}
            self.assertAlmostEqual(original_effect(d)['effect'],0)
    def test_proportion_equal_size_not_always_effect(self):
        x={e:{e} for e in range(8)}
        self.assertAlmostEqual(original_effect(x)['effect'],1)
        x={e:set(range(8)) for e in range(8)}
        self.assertAlmostEqual(original_effect(x)['effect'],0)
    def test_diagonal_invariance(self):
        for k in range(8):
            x={e:{k} for e in range(8)}
            self.assertAlmostEqual(original_effect(x)['effect'],0)
    def test_decomposition_exhaustive_singletons(self):
        for indices in itertools.product(range(8),repeat=3):
            x={e:{indices[e]} if e<3 else set() for e in range(8)}
            out=original_effect(x)
            self.assertAlmostEqual(out['effect'],out['diagonal_component']+out['cardinality_component'])
    def test_mass_normalized_on_exact_copy(self):
        d={k:{k} for k in range(8)}
        self.assertAlmostEqual(mass_effect(d)['effect'],1)
    def test_mass_normalized_no_selection(self):
        self.assertEqual(mass_effect({k:set() for k in range(8)})['effect'],0)
    def test_mass_normalized_all(self):
        self.assertAlmostEqual(mass_effect({k:set(range(8)) for k in range(8)})['effect'],0)
    def test_incomplete_anchors(self):
        with self.assertRaises(ValueError):original_effect({})
        with self.assertRaises(ValueError):mass_effect({})
    def test_exact_signflip_floor(self):self.assertAlmostEqual(exact_p([1]*9),2/512)
    def test_exact_signflip_symmetric(self):self.assertEqual(exact_p([2,1,-1]),exact_p([-2,-1,1]))
    def test_exact_signflip_rejects_one(self):
        with self.assertRaises(ValueError):exact_p([1])
    def test_holm(self):
        ps={'a':.004,'b':.008,'c':.016}
        self.assertEqual(holm(ps),{'a':.012,'b':.016,'c':.016})
    def test_hash_repeatability(self):self.assertEqual(digest({'b':2,'a':1}),digest({'a':1,'b':2}))
