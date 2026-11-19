import unittest
from datetime import datetime, timedelta, timezone
from scripts.collect_dps import read_page, number, discover_periods

class DPSParserTests(unittest.TestCase):
    def test_metric_conversion(self):
        self.assertEqual(number('435K'),435000)
        self.assertEqual(number('2.3K'),2300)
        self.assertEqual(number('1.2M'),1200000)
        with self.assertRaises(ValueError):number('??')

    def test_season_period_index(self):
        html='<html><body><h1>Period (week) index</h1>1090 mid2 Meta 1089 mid2 Meta 1075 mid1 Meta 1061 mid1 Meta 1060 tww3 Meta</body></html>'
        self.assertEqual(discover_periods(html),[(1061,'mid1'),(1075,'mid1'),(1089,'mid2'),(1090,'mid2')])

    def make_section(self, names):
        return ' '.join(f'{i} 0 C {220+i}K {300+i}K 1.3K {name}' for i,name in enumerate(names,1))

    def test_complete_three_roles_and_requested_period(self):
        damage=[
          'assassination rogue','subtlety rogue','outlaw rogue','elemental shaman','enhancement shaman',
          'arms warrior','fury warrior','devourer demon-hunter','havoc demon-hunter',
          'demonology warlock','affliction warlock','destruction warlock','windwalker monk',
          'frost death-knight','unholy death-knight','fire mage','arcane mage','frost mage',
          'marksmanship hunter','beast-mastery hunter','survival hunter','retribution paladin',
          'feral druid','balance druid','shadow priest','devastation evoker','augmentation evoker']
        tanks=['blood death-knight','vengeance demon-hunter','guardian druid','protection warrior','protection paladin','brewmaster monk']
        healers=['preservation evoker','mistweaver monk','holy paladin','restoration shaman','discipline priest','holy priest','restoration druid']
        html='<html><body><h1>Period 1090 (Test)</h1> Damage specs '+self.make_section(damage)+' Tank specs '+self.make_section(tanks)+' Healer specs '+self.make_section(healers)+' About this summary </body></html>'
        record=read_page(html,requested=1090,now=datetime(2026,11,19,tzinfo=timezone(timedelta(hours=9))),season='mid2')
        self.assertEqual(len(record['items']),40)
        self.assertEqual(len([x for x in record['items'] if x['role']=='damage']),27)
        self.assertEqual(len([x for x in record['items'] if x['role']=='tank']),6)
        self.assertEqual(len([x for x in record['items'] if x['role']=='healer']),7)
        self.assertEqual(record['items'][0]['avg_dps'],221000)
        self.assertEqual(record['items'][0]['runs'],1300)
        with self.assertRaises(ValueError):read_page(html,requested=1089)

    def test_partial_section_rejected(self):
        with self.assertRaises(ValueError):read_page('<html>Period 1090 Damage specs 1 0 C 2K 3K 4 assassination rogue Tank specs Healer specs</html>')

if __name__=='__main__':unittest.main()
