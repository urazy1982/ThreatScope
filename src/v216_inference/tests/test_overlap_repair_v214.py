import json, tempfile, unittest
from pathlib import Path
from corpusapt.acquire import stage_archive
from crosscti.core import lines,write_lines
from tests.test_corpusapt import fixture,BASE

class OverlapRepairV214(unittest.TestCase):
    def test_deterministic_next_in_source_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);meta,archive=fixture(root,count=11)
            old=stage_archive(meta,archive,root/'original',BASE)
            rows=lines(root/'original/outputs/prepared/inputs.jsonl')
            self.assertEqual(len(rows),144)
            first=rows[0]
            offender=first['report_id']
            text=first['sentences'][0]['sentence_text']
            baseline=root/'smah.jsonl'
            write_lines(baseline,[{'sentences':[{'sentence_text':text}]}])
            repaired=stage_archive(meta,archive,root/'repaired',BASE,baseline)
            self.assertEqual(repaired['selected_reports'],72)
            self.assertEqual(repaired['input_windows'],144)
            self.assertEqual(repaired['excluded_for_overlap'],1)
            after=lines(root/'repaired/outputs/prepared/inputs.jsonl')
            ids={x['report_id'] for x in after}
            self.assertNotIn(offender,ids)
            self.assertNotIn(text.casefold(),{s['sentence_text'].casefold() for w in after for s in w['sentences']})
            before_source={w['report_id'] for w in rows if w['source']==first['source']}
            after_source={w['report_id'] for w in after if w['source']==first['source']}
            self.assertEqual(len(before_source),8)
            self.assertEqual(len(after_source),8)
            self.assertEqual(len(after_source-before_source),1)
            provenance=json.loads((root/'repaired/dataset/corpus_provenance.json').read_text())
            self.assertEqual(provenance['overlap_repair_status'],'FULL_REPORT_SENTENCE_EXCLUSION_PASS')
            self.assertEqual(provenance['excluded_for_overlap'][0]['report_id'],offender)
    def test_missing_baseline_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);meta,archive=fixture(root,count=9)
            with self.assertRaises(FileNotFoundError):
                stage_archive(meta,archive,root/'work',BASE,root/'not-here.jsonl')
    def test_excess_overlap_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);meta,archive=fixture(root,count=8)
            stage_archive(meta,archive,root/'original',BASE)
            rows=lines(root/'original/outputs/prepared/inputs.jsonl')
            target=rows[0]['source']
            baseline=root/'smah.jsonl'
            write_lines(baseline,[{'sentences':[{'sentence_text':w['sentences'][0]['sentence_text']}]} for w in rows if w['source']==target and w['window_slot']==0])
            with self.assertRaisesRegex(RuntimeError,'NO_EIGHT_NONOVERLAPPING_REPORTS'):
                stage_archive(meta,archive,root/'repaired',BASE,baseline)

if __name__=='__main__':unittest.main()
