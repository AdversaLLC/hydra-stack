import importlib.util,sqlite3,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('hg',str(Path(__file__).with_name('hydra_graph.py')));hg=importlib.util.module_from_spec(spec);spec.loader.exec_module(hg)
def source(path,rows):
 c=sqlite3.connect(path);c.execute('CREATE TABLE observations(id INTEGER PRIMARY KEY,ts TEXT,type TEXT,project TEXT,session TEXT,tags TEXT,conf TEXT,source TEXT,text TEXT,hash TEXT)')
 for i,project,text in rows:c.execute('INSERT INTO observations VALUES(?,?,?,?,?,?,?,?,?,?)',(i,'2026-11-17T00:00:00Z','note',project,'test','','U','test',text,hg.norm_hash(text)))
 c.commit();c.close()
class Cursors(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.r=Path(self.t.name);self.g=hg.Graph(self.r/'graph.db')
 def tearDown(self):self.g.db.close();self.t.cleanup()
 def test_larger_legacy_checkpoint_does_not_skip_current_source(self):
  self.g.set_state('hydra-mem.last_id','16354');p=self.r/'mem.db';source(p,[(1,'arch','Current selected memory source contains a retained observation')])
  self.assertEqual(hg.promote(self.g,p)['added'],1);self.assertEqual(hg.promote(self.g,p)['added'],0)
  self.assertEqual(self.g.state('hydra-mem.last_id'),'16354')
 def test_sources_and_project_scopes_are_independent(self):
  a=self.r/'a.db';b=self.r/'b.db';source(a,[(1,'a','First source observation'),(2,'b','Other project observation')]);source(b,[(1,'a','Independent second source')])
  self.assertEqual(hg.promote(self.g,a,'a')['added'],1);self.assertEqual(hg.promote(self.g,a,'b')['added'],1);self.assertEqual(hg.promote(self.g,b)['added'],1)
 def test_same_path_replaced_database_with_reused_id(self):
  p=self.r/'mem.db';source(p,[(1,'arch','Original retained source observation')]);hg.promote(self.g,p)
  p.unlink();source(p,[(1,'arch','Replacement source observation')]);out=hg.promote(self.g,p)
  self.assertTrue(out['reconciled']);self.assertEqual(out['added'],1);self.assertTrue(self.g.verify_integrity()[0])
 def test_rolling_summary_does_not_replay_or_quarantine_new_wisdom(self):
  p=self.r/'mem.db';source(p,[(i,'arch',f'Original wisdom observation number {i}') for i in range(1,21)])
  with sqlite3.connect(p) as c:c.execute("INSERT INTO observations VALUES(21,'2026-11-17','summary','arch','test','','U','test','old summary','summary-old')")
  self.assertEqual(hg.promote(self.g,p)['added'],20)
  with sqlite3.connect(p) as c:
   c.execute('DELETE FROM observations WHERE id=21')
   c.execute("INSERT INTO observations VALUES(22,'2026-11-17','note','arch','test','','U','test','Legitimate new wisdom observation','new-wisdom')")
   c.execute("INSERT INTO observations VALUES(23,'2026-11-17','summary','arch','test','','U','test','new summary','summary-new')")
  out=hg.promote(self.g,p)
  self.assertFalse(out.get('reconciled',False));self.assertEqual(out['dup'],0);self.assertEqual(out['added'],1);self.assertEqual(out['quarantined'],0)
 def test_reconciliation_duplicates_do_not_consume_new_wisdom_budget(self):
  p=self.r/'mem.db';rows=[(i,'arch',f'Existing wisdom observation number {i}') for i in range(1,21)];source(p,rows)
  with sqlite3.connect(p) as c:c.execute("INSERT INTO observations VALUES(30,'2026-11-17','summary','arch','test','','U','test','old summary','summary-old')")
  hg.promote(self.g,p)
  p.unlink();source(p,rows+[(21,'arch','One new wisdom after source replacement')])
  out=hg.promote(self.g,p)
  self.assertTrue(out['reconciled']);self.assertEqual(out['dup'],20);self.assertEqual(out['added'],1);self.assertEqual(out['quarantined'],0)
if __name__=='__main__':unittest.main(verbosity=2)
