import unittest
from scripts.collect import is_retail_news, normalize_title, cat

class RetailFilters(unittest.TestCase):
    def test_excludes_non_retail(self):
        blocked = [
            ('와우 포에버 PVP 호드 서버', 'Inven'),
            ('[포에버] 곰세툴팁', 'Inven'),
            ('WoW Classic Anniversary Realms', 'Wowhead'),
            ('Latest News Comments - Wowhead', 'Wowhead'),
            ('와우 정보 게시판', 'Inven'),
            ('[잡담] 와우 재밌네요', 'Inven'),
        ]
        for title, source in blocked:
            with self.subTest(title=title):
                self.assertFalse(is_retail_news(title, source))

    def test_keeps_retail(self):
        allowed = [
            ('Midnight Season 3 Dungeon Rotation', 'Wowhead'),
            ('12.2 Eclipse PTR Class Tuning', 'Wowhead'),
            ('이번 주 본섭 쐐기 공략', 'Inven'),
            ('World of Warcraft Hotfixes', 'Blizzard'),
        ]
        for title, source in allowed:
            with self.subTest(title=title):
                self.assertTrue(is_retail_news(title, source))

    def test_normalize_and_category(self):
        self.assertEqual(normalize_title('Midnight Season 3 Dungeon Rotation - Wowhead'), 'Midnight Season 3 Dungeon Rotation')
        self.assertEqual(cat('Season 3 Mythic Dungeon Rotation'), '쐐기·레이드')
        self.assertEqual(cat('Class Tuning Hotfixes'), '공식·핫픽스')

if __name__ == '__main__':
    unittest.main()
