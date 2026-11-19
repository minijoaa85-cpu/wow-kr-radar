import unittest
from unittest.mock import Mock
from tempfile import TemporaryDirectory
from pathlib import Path
import scripts.collect_kr_mplus as mod

class KRMPlusTests(unittest.TestCase):
    def test_success(self):
        session=Mock()
        response=Mock()
        response.json.return_value={'title':'Weekly Affixes','affix_details':[{'name':'Fortified','description':'Test description'}]}
        session.get.return_value=response
        with TemporaryDirectory() as tmp:
            original=mod.DEST
            try:
                mod.DEST=Path(tmp)/'kr_mplus.json'
                data=mod.collect(session)
                self.assertEqual(data['status'],'live')
                self.assertEqual(data['affixes'][0]['name'],'Fortified')
                self.assertTrue(mod.DEST.exists())
                self.assertEqual(session.get.call_args.kwargs['params']['region'],'kr')
            finally:
                mod.DEST=original

    def test_unavailable_no_fake_affixes(self):
        session=Mock()
        response=Mock()
        response.json.return_value={'error':'bad response'}
        session.get.return_value=response
        with TemporaryDirectory() as tmp:
            original=mod.DEST
            try:
                mod.DEST=Path(tmp)/'kr_mplus.json'
                data=mod.collect(session)
                self.assertEqual(data['status'],'unavailable')
                self.assertEqual(data['affixes'],[])
            finally:
                mod.DEST=original

if __name__=='__main__':
    unittest.main()
