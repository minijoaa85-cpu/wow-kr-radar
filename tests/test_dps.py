import unittest
from datetime import datetime, timedelta, timezone
from scripts.collect_dps import read_page, number

class DPSParserTests(unittest.TestCase):
    def test_metric_conversion(self):
        self.assertEqual(number('435K'),435000)
        self.assertEqual(number('2.3K'),2300)
        self.assertEqual(number('1.2M'),1200000)
        with self.assertRaises(ValueError):number('??')
    def test_full_snapshot_and_period_validation(self):
        rows=[
          ('assassination rogue',435,597),('subtlety rogue',388,512),
          ('elemental shaman',357,470),('arms warrior',354,469),
          ('devourer demon-hunter',353,478),('demonology warlock',348,476),
          ('windwalker monk',348,460),('frost death-knight',342,467),
          ('fire mage',340,400),('arcane mage',338,442),
          ('unholy death-knight',338,449),('marksmanship hunter',337,413),
          ('retribution paladin',336,452),('feral druid',332,431),
          ('enhancement shaman',331,422),('outlaw rogue',327,401)
        ]
        text=' '.join(f'{i} 0 C {avg}K {top}K 1.3K {name}' for i,(name,avg,top) in enumerate(rows,1))
        html='<html><body><h1>Period 1090 (Test period)</h1><p>Damage specs</p><div>'+text+'</div><h3>Tank specs</h3></body></html>'
        record=read_page(html,requested=1090,now=datetime(2026,11,19,tzinfo=timezone(timedelta(hours=9))))
        self.assertEqual(record['period'],1090)
        self.assertEqual(len(record['items']),16)
        self.assertEqual(record['items'][0]['avg_dps'],435000)
        self.assertEqual(record['items'][0]['runs'],1300)
        self.assertEqual(record['items'][7]['class'],'death-knight')
        with self.assertRaises(ValueError):read_page(html,requested=1089)
    def test_bad_page_not_stored(self):
        with self.assertRaises(ValueError):read_page('<html><body>Period 1090 Damage specs 1 0 C 2K 3K 4 assassination rogue Tank specs</body></html>')

if __name__=='__main__':
    unittest.main()
