"""Independent CPU stress tests; no HF models, CUDA, or real predictions."""
import json, math, random, shutil, sys, tempfile, types, unittest
from pathlib import Path
from unittest.mock import patch
from crosscti.core import ANCHORS,SYS,digest,parse,prompt,read,write
from crosscti.analyze import anchor_effect,cluster_bootstrap,exact_sign_flip,verify_prepared
from crosscti.prepare import read_dataset,prepare,sentences
from crosscti.runner import model_messages
from crosscti.preflight import run as preflight
from scripts.cpu_replay import synthetic_records

ROOT=Path(__file__).resolve().parent.parent
CONFIG=read(ROOT/'config/study.json')

class Expanded(unittest.TestCase):
    def data_fixture(self):
        tmp=tempfile.TemporaryDirectory(prefix='threat_cpu_extended_')
        root=Path(tmp.name)
        (root/'config').mkdir();shutil.copy2(ROOT/'config/study.json',root/'config/study.json')
        d=root/'data.json';write(d,synthetic_records(CONFIG))
        return tmp,root,d

    def test_exact_sign_flip_positive_minimum(self):
        self.assertAlmostEqual(exact_sign_flip([1]*10),.001953125)
    def test_exact_sign_flip_five_source_resolution(self):
        self.assertEqual(exact_sign_flip([1]*5),.0625)
    def test_exact_sign_flip_null(self):
        self.assertEqual(exact_sign_flip([0]*10),1.0)
    def test_exact_sign_flip_order_invariance(self):
        vals=[-1.5,.2,0,1,.7,-.3,.6,.9,.1,-.4]
        self.assertEqual(exact_sign_flip(vals),exact_sign_flip(list(reversed(vals))))
    def test_bootstrap_seed_reproducible(self):
        r={'a':[0,1,2],'b':[3,4,5],'c':[-2,-3,-4]}
        self.assertEqual(cluster_bootstrap(r,7,300),cluster_bootstrap(r,7,300))
    def test_anchor_index_relabel_invariance(self):
        rng=random.Random(817)
        for _ in range(60):
            rows={k:{p for p in ANCHORS if rng.random()<0.5} for k in ANCHORS}
            perm=list(ANCHORS);rng.shuffle(perm)
            new={perm[k]:{perm[j] for j in rows[k]} for k in ANCHORS}
            self.assertAlmostEqual(anchor_effect(rows),anchor_effect(new))
    def test_balanced_anchor_no_preferences(self):
        for subset in [set(),{0},{0,1,7},set(ANCHORS)]:
            self.assertAlmostEqual(anchor_effect({k:subset for k in ANCHORS}),0)
    def test_cardinality_only_counterexample(self):
        # A position-prefix selection rule with cardinality determined by the
        # example digit can create positive anchor score with no copy rule.
        rows={k:set(range(k+1)) for k in ANCHORS}
        self.assertGreater(anchor_effect(rows),0.1)
    def test_parser_malicious_and_nonfinite(self):
        for x in ['{"relevant":[NaN]}','{"relevant":[-1]}','{"relevant":[1.0]}',
                  '{"relevant":[false]}','{"relevant":[0],"extra":true}',
                  '```json\n{"relevant":[0]}\n```',
                  '{"relevant":[0,0]}','{"relevant":[7,8]}']:
            self.assertFalse(parse(x)['valid'],x)
    def test_parser_all_positions(self):
        self.assertEqual(parse('{"relevant":[7,4,0,2,3,1,6,5]}')['indices'],list(ANCHORS))
    def test_anchor_prompt_exact_one_character_diff(self):
        w={'sentences':[{'sentence_text':f'Sentence number {x} is an indicative CTI description.','context_before':''} for x in ANCHORS]}
        p0=prompt(w,0)
        for k in ANCHORS:
            pk=prompt(w,k)
            self.assertEqual(len(pk.encode()),len(p0.encode()))
            self.assertEqual(sum(a!=b for a,b in zip(pk,p0)),int(k!=0))
    def test_cross_publisher_exact_duplicate_rejected(self):
        tmp,root,data=self.data_fixture()
        with tmp:
            records=read(data);records[10]['CTI']['text']=records[0]['CTI']['text'];write(data,records)
            with self.assertRaisesRegex(ValueError,'CROSS_SOURCE_DUPLICATE_TEXT'):prepare(data,root)
    def test_cross_publisher_whitespace_duplicate_rejected(self):
        tmp,root,data=self.data_fixture()
        with tmp:
            records=read(data);records[10]['CTI']['text']='\n  '+records[0]['CTI']['text'].replace('\n\n','\n \n')+'  '
            write(data,records)
            with self.assertRaisesRegex(ValueError,'CROSS_SOURCE_DUPLICATE_TEXT'):prepare(data,root)
    def test_same_source_normalized_duplicate_rejected(self):
        tmp,root,data=self.data_fixture()
        with tmp:
            records=read(data);records[1]['CTI']['text']=records[0]['CTI']['text'].replace('   ',' ').replace('\n\n','\n \n')
            write(data,records)
            with self.assertRaisesRegex(ValueError,'DUPLICATE'):prepare(data,root)
    def test_unknown_publisher_rejected(self):
        tmp,root,data=self.data_fixture()
        with tmp:
            records=read(data);records[0]['CTI']['source']='Plausible Fake Publisher';write(data,records)
            with self.assertRaisesRegex(ValueError,'UNKNOWN_PUBLISHER'):read_dataset(data,CONFIG)
    def test_absent_publisher_rejected(self):
        tmp,root,data=self.data_fixture()
        with tmp:
            records=read(data);records[0]['CTI'].pop('source');write(data,records)
            with self.assertRaisesRegex(ValueError,'MISSING_SOURCE'):read_dataset(data,CONFIG)
    def test_full_positive_preparation(self):
        tmp,root,data=self.data_fixture()
        with tmp:
            m=prepare(data,root)
            self.assertEqual(m['windows'],160)
            self.assertEqual(m['total_calls'],7680)
            cfg,mm,w=verify_prepared(root)
            self.assertEqual(len({x['report_id'] for x in w}),80)
            self.assertEqual(len({x['window_id'] for x in w}),160)
            self.assertTrue(all(len(x['sentences'])==8 for x in w))
            self.assertTrue(all(sum(x['source']==p for x in w)==16 for p in cfg['source_names']))
            self.assertEqual(len(set(x['input_sha256'] for x in w)),160)
    def test_prepared_input_tamper_rejected(self):
        tmp,root,data=self.data_fixture()
        with tmp:
            prepare(data,root)
            p=root/'outputs/prepared/inputs.jsonl';p.write_text(p.read_text()+'\n{}\n')
            with self.assertRaisesRegex(RuntimeError,'PREPARED_INPUT_DRIFT'):verify_prepared(root)
    def test_prepared_config_tamper_rejected(self):
        tmp,root,data=self.data_fixture()
        with tmp:
            prepare(data,root)
            p=root/'config/study.json';s=p.read_text();p.write_text(s+' ')
            with self.assertRaisesRegex(RuntimeError,'PREPARED_CONFIG_DRIFT'):verify_prepared(root)
    def test_prepared_reordering_rejected(self):
        tmp,root,data=self.data_fixture()
        with tmp:
            prepare(data,root)
            p=root/'outputs/prepared/inputs.jsonl';ss=p.read_text().splitlines();ss.reverse();p.write_text('\n'.join(ss)+'\n')
            with self.assertRaisesRegex(RuntimeError,'PREPARED_INPUT_DRIFT'):verify_prepared(root)
    def test_provenance_path_not_authenticated_by_schema(self):
        # This software cannot certify source authenticity from an arbitrary
        # string; keep a mandatory real-world provenance gate before inference.
        tmp,root,data=self.data_fixture()
        with tmp:
            m=prepare(data,root)
            self.assertNotIn('source_url_sha256',m)
            self.assertEqual(CONFIG['source_provenance_status'],'UNVERIFIED_REPORT_SOURCE_LABELS_MUST_BE_AUTHENTICATED_BEFORE_GPU')
    def test_exclusion_of_short_sentences(self):
        self.assertEqual(sentences('Short.\n\nToo brief.'),[])
    def test_tokenizer_fake_equal_pass(self):
        tmp,root,data=self.data_fixture()
        with tmp:
            prepare(data,root)
            class FakeTokenizer:
                def apply_chat_template(self,msgs,**kwargs):return {'input_ids':[[1]*sum(len(m['content']) for m in msgs)]}
            fake=types.SimpleNamespace(AutoTokenizer=types.SimpleNamespace(from_pretrained=lambda *args,**kw:FakeTokenizer()))
            with patch.dict(sys.modules,{'transformers':fake}):
                records=preflight(root)
            self.assertEqual(len(records),3)
            self.assertTrue(all(r['unequal_windows']==0 and r['ok'] for r in records))
    def test_gpu_runner_fails_closed_before_cuda(self):
        from crosscti.runner import run_cell
        tmp,root,data=self.data_fixture()
        with tmp:
            prepare(data,root)
            with self.assertRaisesRegex(RuntimeError,'GPU_AUTHORIZATION_MISSING'):
                run_cell(root,next(iter(CONFIG['models'])),'bf16')
    def test_tokenizer_fake_anchor_inequality_rejected(self):
        tmp,root,data=self.data_fixture()
        with tmp:
            prepare(data,root)
            class FakeTokenizer:
                def apply_chat_template(self,msgs,**kwargs):
                    joined=''.join(m['content'] for m in msgs)
                    return {'input_ids':[[1]*(len(joined)+(1 if '{"relevant":[7]}' in joined else 0))]}
            fake=types.SimpleNamespace(AutoTokenizer=types.SimpleNamespace(from_pretrained=lambda *args,**kw:FakeTokenizer()))
            with patch.dict(sys.modules,{'transformers':fake}):
                with self.assertRaisesRegex(RuntimeError,'TOKENIZER_GATE_FAIL'):preflight(root)

if __name__=='__main__':unittest.main()
