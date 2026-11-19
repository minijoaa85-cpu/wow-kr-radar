import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import Mock
from scripts.collect_kr_runs import parse_runs, collect, safe_link

class KRRunTests(unittest.TestCase):
    def test_parse_sanitized(self):
        data={'runs':[{'dungeon':{'name':'Example Dungeon'},'mythic_level':16,'score':220.1,'url':'https://raider.io/mythic-plus-runs/example'}, {'dungeon':'Broken','mythic_level':'bad'}]}
        r=parse_runs(data)
        self.assertEqual(len(r),1)
        self.assertEqual(r[0]['level'],16)
        self.assertEqual(r[0]['score'],220.1)
    def test_only_verified_source_links(self):
        self.assertEqual(safe_link('javascript:alert(1)'),'')
        self.assertEqual(safe_link('https://raider.io.evil.invalid/run'),'')
    def test_unavailable_does_not_invent_runs(self):
        session=Mock()
        session.get.return_value.json.return_value={'bad':'format'}
        with TemporaryDirectory() as folder:
            r=collect(session,Path(folder)/'runs.json')
            self.assertEqual(r['status'],'unavailable')
            self.assertEqual(r['runs'],[])

if __name__=='__main__':unittest.main()
