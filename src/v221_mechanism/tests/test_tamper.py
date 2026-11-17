import unittest,zipfile,json,tempfile
from pathlib import Path
from v22core.replay import validate_archive
R=Path(__file__).resolve().parents[1]
Z=R/'reference/ThreatStudy_v216_Complete_Results.zip'

class RealRecordTamperTests(unittest.TestCase):
    def test_archive_rejects_raw_modified(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'tampered.zip'
            with zipfile.ZipFile(Z) as src,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as dst:
                changed=False
                for info in src.infolist():
                    data=src.read(info.filename)
                    if not changed and '/example_' in info.filename and info.filename.endswith('.json'):
                        r=json.loads(data);r['raw']+='x';data=json.dumps(r).encode();changed=True
                    dst.writestr(info.filename,data)
            self.assertTrue(changed)
            with self.assertRaisesRegex(RuntimeError,'RAW_HASH_DRIFT'):
                validate_archive(out)
    def test_archive_rejects_missing_one_checkpoint(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'missing.zip'
            with zipfile.ZipFile(Z) as src,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as dst:
                changed=False
                for info in src.infolist():
                    if not changed and '/example_' in info.filename and info.filename.endswith('.json'):
                        changed=True;continue
                    dst.writestr(info.filename,src.read(info.filename))
            self.assertTrue(changed)
            with self.assertRaises(KeyError):validate_archive(out)
