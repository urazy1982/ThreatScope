import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.e3_runner import EXPECTED, INPUT_SHA,model_messages,PROTOCOL
from vendor.core import prompt,parse
class TestE3(unittest.TestCase):
 def test_allocation(self):self.assertEqual(sum(EXPECTED.values()),72)
 def test_prompt_index_change(self):
  w={'sentences':[{'context_before':'','sentence_text':'An adversary used malware.'} for i in range(8)]}
  a,b=prompt(w,0),prompt(w,1)
  self.assertEqual(len(a),len(b));self.assertIn('{"relevant":[0]}',a);self.assertIn('{"relevant":[1]}',b)
 def test_parser(self):self.assertTrue(parse('{"relevant":[0,2]}')['valid']);self.assertFalse(parse('not JSON')['valid'])
 def test_mistral_role(self):
  self.assertEqual(len(model_messages('mistralai/Mistral-7B-Instruct-v0.3','abc')),1)
  self.assertEqual(len(model_messages('Qwen/Qwen2.5-3B-Instruct','abc')),2)
 def test_protocol(self):self.assertEqual(len(INPUT_SHA),64);self.assertIn('E3',PROTOCOL)
if __name__=='__main__':unittest.main()
