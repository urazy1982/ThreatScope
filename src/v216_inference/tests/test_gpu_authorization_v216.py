import tempfile, unittest, json
from pathlib import Path
from unittest.mock import patch
from crosscti.core import digest, write
from crosscti.gpu_gate import verify_authorization

class AuthorizationTests(unittest.TestCase):
    def test_requires_authorization(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(RuntimeError,'GPU_AUTHORIZATION_MISSING'):
                verify_authorization(d)
    def fixture(self,d):
        root=Path(d);identity={'models':{'m1':'revision1','m2':'revision2','m3':'revision3'},'calls':6912}
        preflight=[{'model':m,'max_input_tokens':100,'unequal_windows':0,'ok':True} for m in identity['models']]
        doc={'status':'GPU_AUTHORIZED_DATASET_BOUND','identity':identity,'preflight':preflight}
        doc['authorization_sha256']=digest(doc)
        write(root/'outputs/authorization/gpu_authorization.json',doc)
        return root,identity,doc
    def test_valid_authorization(self):
        with tempfile.TemporaryDirectory() as d:
            root,iden,doc=self.fixture(d)
            with patch('crosscti.gpu_gate.identity',return_value=iden):
                self.assertEqual(verify_authorization(root)['status'],'GPU_AUTHORIZED_DATASET_BOUND')
    def test_checkpoint_invalidated_by_source_change(self):
        with tempfile.TemporaryDirectory() as d:
            root,iden,doc=self.fixture(d)
            with patch('crosscti.gpu_gate.identity',return_value={'dataset_sha256':'changed'}):
                with self.assertRaisesRegex(RuntimeError,'GPU_AUTHORIZATION_INPUT_DRIFT'):verify_authorization(root)
    def test_rejects_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            root,iden,doc=self.fixture(d)
            doc['status']='GPU_AUTHORIZED_ANYTHING'
            write(root/'outputs/authorization/gpu_authorization.json',doc)
            with self.assertRaisesRegex(RuntimeError,'AUTHORIZATION_TAMPERED'):verify_authorization(root)
    def test_unbalanced_preflight_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root,iden,doc=self.fixture(d)
            doc['preflight'][0]['unequal_windows']=1
            doc['authorization_sha256']=digest({k:v for k,v in doc.items() if k!='authorization_sha256'})
            write(root/'outputs/authorization/gpu_authorization.json',doc)
            with patch('crosscti.gpu_gate.identity',return_value=iden):
                with self.assertRaisesRegex(RuntimeError,'PREFLIGHT_INVALID'):verify_authorization(root)
    def test_release_launcher_does_not_bypass_gate(self):
        script=(Path(__file__).resolve().parents[1]/'scripts/run_gpu.sh').read_text()
        self.assertIn('gpu_gate --root',script)
        self.assertIn('--verify-only',script)
    def test_runner_gate_before_cuda(self):
        src=(Path(__file__).resolve().parents[1]/'crosscti/runner.py').read_text()
        self.assertLess(src.index('verify_authorization(root)'),src.index('import torch,transformers,bitsandbytes'))
if __name__=='__main__':unittest.main()
