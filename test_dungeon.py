import unittest
from mock import patch

import dungeon


class TestDungeonGame(unittest.TestCase):
    def setUp(self):
        self.url = TestDungeonGame.get_test_url()
        self.cookies = {"random-cookie": 'value'}
        self.dungeon_urls = dungeon.DungeonGameUrls(self.url, self.cookies)
        self.dungeon = dungeon.DungeonGame(self.dungeon_urls)

    @staticmethod
    def get_test_url():
        return "http://dungeon-game.com/index.php"

    def mocked_requests_get(*args, **kwargs):
        dungeon_urls = dungeon.DungeonGameUrls(TestDungeonGame.get_test_url(), {})
        if args[0] == dungeon_urls.base_url:
            with open("content/treasure.html") as f:
                return MockResponse(f.read(), 200)
        elif args[0] == dungeon_urls.get_attack_url():
            with open("content/attack.html") as f:
                return MockResponse(f.read(), 200)
        # TODO: add more requests
        return MockResponse({}, 404)

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_update_stats_from_base_url(self, get_mock):
        self.dungeon.update_stats(self.dungeon_urls.base_url)
        get_mock.assert_called_once_with(self.dungeon_urls.base_url, cookies=self.cookies)

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_update_stats_from_base_url(self, get_mock):
        self.dungeon.update_stats(self.dungeon_urls.get_attack_url())
        get_mock.assert_called_once_with(self.dungeon_urls.get_attack_url(), cookies=self.cookies)


class TestDungeonGameUrls(unittest.TestCase):
    def setUp(self):
        self.test_base_url = "http://example.com/index.php"

    def test_dungeon_game_urls_base_url(self):
        dungeon_urls = dungeon.DungeonGameUrls(self.test_base_url, {})
        self.assertEqual(self.test_base_url, dungeon_urls.base_url)

    def test_dungeon_urls_attack_url(self):
        dungeon_urls = dungeon.DungeonGameUrls(self.test_base_url, {})
        self.assertEqual(self.test_base_url + "?attack=1", dungeon_urls.get_attack_url())

    def test_dungeon_urls_move_south_url(self):
        dungeon_urls = dungeon.DungeonGameUrls(self.test_base_url, {})
        self.assertEqual(self.test_base_url + "?m=s", dungeon_urls.get_move_url("s"))


class TestDungeonGameHtmlParser(unittest.TestCase):
    def test_parse_weapon_without_additions(self):
        expected_weapon = ("Tester", 30, 0)
        self.assertEqual(expected_weapon, dungeon.DungeonGameHtmlParser.parse_weapon("Level 30 Tester"))

    def test_parse_weapon_with_additions(self):
        expected_weapon = ("Tester", 30, 1)
        self.assertEqual(expected_weapon, dungeon.DungeonGameHtmlParser.parse_weapon("Level 30 Tester +1"))

    def test_parse_game_html_treasure(self):
        expected_stats = dungeon.Stats(33, 740)
        expected_stats.inventory = [u'A potion +5', u'B potion +4', u'C potion +4']
        expected_stats.weapon = ("Tester", 30, 1)
        expected_stats.dungeon_level = 31
        with open("content/treasure.html") as f:
            dungeon_parser = dungeon.DungeonGameHtmlParser(f.read())
            stats = dungeon_parser.parse_game_stats()
            self.assertEqual(expected_stats.health, stats.health)
            self.assertEqual(expected_stats.level, stats.level)
            self.assertEqual(expected_stats.inventory, stats.inventory)
            self.assertEqual(expected_stats.weapon, stats.weapon)
            self.assertEqual(expected_stats.dungeon_level, stats.dungeon_level)

    def test_parse_game_html_attack(self):
        expected_stats = dungeon.Stats(33, 603)
        expected_stats.inventory = [u'A potion +5', u'B potion +4', u'C potion +4']
        expected_stats.weapon = ("Tester", 30, 1)
        expected_stats.dungeon_level = 31
        with open("content/attack.html") as f:
            dungeon_parser = dungeon.DungeonGameHtmlParser(f.read())
            stats = dungeon_parser.parse_game_stats()
            self.assertEqual(expected_stats.health, stats.health)
            self.assertEqual(expected_stats.level, stats.level)
            self.assertEqual(expected_stats.inventory, stats.inventory)
            self.assertEqual(expected_stats.weapon, stats.weapon)
            self.assertEqual(expected_stats.dungeon_level, stats.dungeon_level)

    def test_parse_html_possible_actions_base_url(self):
        expected_actions = dungeon.Actions(south=1, north=1)
        with open("content/treasure.html") as f:
            dungeon_parser = dungeon.DungeonGameHtmlParser(f.read())
            actions = dungeon_parser.parse_game_actions()
            self.assertEqual(expected_actions.move_north, actions.move_north)


class TestStats(unittest.TestCase):
    def test_compare_weapons_level(self):
        weapon1 = ("Tester", 30, 0)
        weapon2 = ("Tester", 29, 0)
        self.assertEqual(True, dungeon.Stats.compare_weapons(weapon1, weapon2))
        self.assertEqual(False, dungeon.Stats.compare_weapons(weapon2, weapon1))

    def test_compare_weapons_addition(self):
        weapon1 = ("Tester", 29, 1)
        weapon2 = ("Tester", 29, 0)
        self.assertEqual(True, dungeon.Stats.compare_weapons(weapon1, weapon2))
        self.assertEqual(False, dungeon.Stats.compare_weapons(weapon2, weapon1))

    def test_compare_weapons_level_and_addition(self):
        weapon1 = ("Tester", 30, 0)
        weapon2 = ("Tester", 29, 1)
        self.assertEqual(True, dungeon.Stats.compare_weapons(weapon1, weapon2))
        self.assertEqual(False, dungeon.Stats.compare_weapons(weapon2, weapon1))


class MockResponse(object):
    def __init__(self, text, status_code):
        self.text = text
        self.status_code = status_code

    def text(self):
        return self.text

if __name__ == '__main__':
    unittest.main()
