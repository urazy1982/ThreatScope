import hashlib,json,tempfile,unittest
from pathlib import Path
from crosscti.final_cpu_gate import grams,norm,source_host,validate

class TestFinalGate(unittest.TestCase):
    def test_normalization(self):self.assertEqual(norm(' A  B\nC '),'a b c')
    def test_shingle_works(self):self.assertEqual(len(grams('one two three four five six')),2)
    def test_shingle_short(self):self.assertFalse(grams('short'))
    def test_host_true(self):self.assertTrue(source_host('https://securelist.com/test','securelist_apt'))
    def test_host_spoof(self):self.assertFalse(source_host('https://securelist.com.bad.test/test','securelist_apt'))
    def test_host_unknown(self):self.assertFalse(source_host('https://securelist.com/','fake'))
    def test_empty_workspace_fails(self):
        with tempfile.TemporaryDirectory() as p:
            with self.assertRaises(FileNotFoundError):validate(p,Path(p)/'missing.jsonl')
    def test_no_hidden_gpu_enable(self):
        p=Path(__file__).resolve().parents[1]
        self.assertIn('gpu_gate --root', (p/'scripts/run_gpu.sh').read_text())
    def test_no_false_source_classification(self):
        self.assertFalse(source_host('https://evil.com/securelist.com','securelist_apt'))
if __name__=='__main__':unittest.main()
