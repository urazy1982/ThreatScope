import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from e1_neutral_gpu import build_prompt,parse_output
class TestE1(unittest.TestCase):
 def test_templates(self):
  w={'sentences':[{'context_before':'','sentence_text':'example'} for _ in range(8)]}
  n0=build_prompt(w,'N0');n1=build_prompt(w,'N1')
  self.assertIn('TARGET_SENTENCES_JSON:',n0)
  self.assertIn('TARGET_SENTENCES_JSON:',n1)
  self.assertNotIn('OUTPUT FORMAT EXAMPLE',n0)
  self.assertIn('OUTPUT FORMAT EXAMPLE',n1)
  self.assertIn('{"relevant":[]}',n1)
  self.assertNotIn('{"relevant":[0]}',n1)
 def test_schema(self):
  self.assertEqual(parse_output('{"relevant":[1,3]}')[:2],(True,[1,3]))
  self.assertFalse(parse_output('{"relevant":[8]}')[0]);self.assertFalse(parse_output('{"relevant":[1,1]}')[0])
  self.assertFalse(parse_output('{"relevant":[true]}')[0])
if __name__=='__main__':unittest.main()
