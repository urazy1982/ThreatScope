"""CPU-only tests of sample traceability and uncertainty logic (fabricated fixtures)."""
import csv
import hashlib
import sys
import unittest
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from analyze_e1 import validate_labels, hierarchical_ci

class ScientificNegativeCases(unittest.TestCase):
 def fixture(self):
  windows=[];labels=[]
  for pi in range(9):
   for ri in range(4):
    w={'source':f'pub{pi}','report_id':f'report{pi}_{ri}',
       'window_id':f'win{pi}_{ri}',
       'sentences':[{'sentence_text':f'FAKE {pi} {ri} {i}', 'context_before':''} for i in range(8)]}
    windows.append(w)
    for i in range(8):
     s=w['sentences'][i]['sentence_text']
     labels.append({'window_id':w['window_id'],'target_index':str(i),
       'publisher':w['source'],'report_id':w['report_id'],
       'text_sha256':hashlib.sha256(s.encode()).hexdigest(),
       'adjudicated':'0'})
  for r in labels[-15:]:r['adjudicated']=''
  return windows,labels

 def test_exact_288_passes(self):
  windows,labels=self.fixture()
  validate_labels(labels,windows)

 def test_text_hash_drift_detected(self):
  windows,labels=self.fixture();labels[0]['text_sha256']='0'*64
  with self.assertRaisesRegex(RuntimeError,'TARGET_TEXT_HASH_MISMATCH'):
   validate_labels(labels,windows)

 def test_missing_item_rejected(self):
  windows,labels=self.fixture()
  with self.assertRaisesRegex(RuntimeError,'REQUIRES_ORIGINAL_288_LABELS'):
   validate_labels(labels[:-1],windows)

 def test_wrong_adjudication_count_rejected(self):
  windows,labels=self.fixture();labels[-1]['adjudicated']='1'
  with self.assertRaisesRegex(RuntimeError,'WRONG_DETERMINATE_COUNT'):
   validate_labels(labels,windows)

 def test_deterministic_publisher_report_bootstrap(self):
  data=defaultdict(list)
  for p in range(9):
   for r in range(8):
    for w in range(2):
     data[f'pub{p}'].append({'report_id':f'r{r}','N1_minus_N0_disagreement_pp':p+r+w})
  low,high,n=hierarchical_ci(data,draws=300,seed=77)
  self.assertEqual((low,high,n),hierarchical_ci(data,draws=300,seed=77))
  self.assertLess(low,high)

if __name__=='__main__':unittest.main()
