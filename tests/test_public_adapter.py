"""Portable original-method checks with fake callbacks; no API or hidden tests."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from public_adapter import run,extract
PUBLIC={'problem_id':'unit/0','entry_point':'f','prompt':'Return one.',
 'tests':[{'kind':'python_assert','source_code':'assert f()==1'}],'dataset':'mbpp_500'}

class AdapterTests(unittest.TestCase):
 def test_public_pass_skips_all_model_requests(self):
  def forbidden(*args):raise AssertionError('Unexpected request')
  result=run(PUBLIC,'original',forbidden,lambda code:{'passed':True,'result':'passed'})
  self.assertEqual((result['rounds'],result['final_code']),(0,'original'))
 def test_teacher_precedes_student(self):
  calls=[];checks=[]
  def generate(role,turn,prompt):calls.append(role);return 'repair advice' if role=='teacher' else 'def f(): return 1'
  def check(code):checks.append(code);return {'passed':len(checks)>1,'result':'public feedback'}
  result=run(PUBLIC,'bad',generate,check)
  self.assertEqual(calls,['teacher','student']);self.assertEqual(result['rounds'],1)
 def test_five_rounds_without_tracecoder_patience(self):
  calls=[]
  def generate(role,turn,prompt):calls.append(role);return str(turn)
  result=run(PUBLIC,'bad',generate,lambda code:{'passed':False,'result':'public feedback'})
  self.assertEqual((result['rounds'],len(calls),result['final_code']),(5,10,'5'))
 def test_hidden_fields_rejected(self):
  for key in ('hidden_tests','reference','scores','canonical_solution'):
   with self.assertRaises(ValueError):run(dict(PUBLIC,**{key:'private'}),'',None,None)
 def test_original_permissive_extraction(self):
  self.assertEqual(extract('def f(:',PUBLIC),'def f(:')
  self.assertEqual(extract('    return 1',dict(PUBLIC,dataset='humaneval',prompt='def f():')),'def f():\n    return 1')
 def test_failure_propagates_to_outer_transport(self):
  calls=[]
  def fail(*args):calls.append(args);raise TimeoutError('simulated transport failure')
  with self.assertRaises(TimeoutError):run(PUBLIC,'bad',fail,lambda code:{'passed':False,'result':'public feedback'})
  self.assertEqual(len(calls),1)

if __name__=='__main__':unittest.main()
