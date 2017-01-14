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

    @staticmethod
    def get_test_cookies():
        return {"random-cookie": 'value'}

    def mocked_requests_get(*args, **kwargs):
        dungeon_urls = dungeon.DungeonGameUrls(TestDungeonGame.get_test_url(), TestDungeonGame.get_test_cookies())
        if args[0] == dungeon_urls.base_url:
            with open("content/base.html") as f:
                return MockResponse(f.read(), 200)
        if args[0] == dungeon_urls.get_treasure_url():
            with open("content/treasure.html") as f:
                return MockResponse(f.read(), 200)
        elif args[0] == dungeon_urls.get_attack_url():
            with open("content/attack.html") as f:
                return MockResponse(f.read(), 200)
        elif args[0] == dungeon_urls.get_move_url('d'):
            with open("content/downstairs.html") as f:
                return MockResponse(f.read(), 200)
        # TODO: add more requests
        return MockResponse({}, 404)

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_update_stats_from_base_url(self, get_mock):
        self.dungeon.update_stats(self.dungeon_urls.base_url)
        get_mock.assert_called_once_with(self.dungeon_urls.base_url, cookies=self.cookies)
        self.assertIsNotNone(self.dungeon.stats)

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_update_stats_from_attack_url(self, get_mock):
        self.dungeon.update_stats(self.dungeon_urls.get_attack_url())
        get_mock.assert_called_once_with(self.dungeon_urls.get_attack_url(), cookies=self.cookies)
        self.assertIsNotNone(self.dungeon.stats)

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_update_actions_from_base_url(self, get_mock):
        self.dungeon.get_actions(self.dungeon_urls.base_url)
        get_mock.assert_called_once_with(self.dungeon_urls.base_url, cookies=self.cookies)
        self.assertIsNotNone(self.dungeon.actions)

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_update_actions_from_attack_url(self, get_mock):
        self.dungeon.get_actions(self.dungeon_urls.get_attack_url())
        get_mock.assert_called_once_with(self.dungeon_urls.get_attack_url(), cookies=self.cookies)
        self.assertIsNotNone(self.dungeon.actions)

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_pick_up_treasure_from_treasure_url(self, get_mock):
        self.dungeon.update_stats(self.dungeon_urls.get_treasure_url())
        self.dungeon.get_actions(self.dungeon_urls.get_treasure_url())
        self.dungeon.pick_up_treasure()
        get_mock.assert_called(self.dungeon_urls.send_get_treasure_request())

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_move_downstairs_from_downstairs_url_when_level_enough(self, get_mock):
        self.dungeon.update_stats(self.dungeon_urls.get_move_url('d'))
        self.dungeon.get_actions(self.dungeon_urls.get_move_url('d'))
        self.assertTrue(self.dungeon.move_downstairs())
        get_mock.assert_called()

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_move_downstairs_from_downstairs_url_when_level_not_enough(self, get_mock):
        self.dungeon.update_stats(self.dungeon_urls.get_move_url('d'))
        self.dungeon.get_actions(self.dungeon_urls.get_move_url('d'))
        self.dungeon.stats.level = self.dungeon.stats.dungeon_level - 1
        self.assertFalse(self.dungeon.move_downstairs())


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

    def test_dungeon_urls_move_downstairs_url(self):
        dungeon_urls = dungeon.DungeonGameUrls(self.test_base_url, {})
        self.assertEqual(self.test_base_url + "?m=d", dungeon_urls.get_move_url("d"))

    def test_dungeon_urls_treasure_url(self):
        dungeon_urls = dungeon.DungeonGameUrls(self.test_base_url, {})
        self.assertEqual(self.test_base_url + "?tres=1", dungeon_urls.get_treasure_url())


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
            self._assert_equal_stats(expected_stats, stats)

    def test_parse_game_html_attack(self):
        expected_stats = dungeon.Stats(33, 603)
        expected_stats.inventory = [u'A potion +5', u'B potion +4', u'C potion +4']
        expected_stats.weapon = ("Tester", 30, 1)
        expected_stats.dungeon_level = 31
        with open("content/attack.html") as f:
            dungeon_parser = dungeon.DungeonGameHtmlParser(f.read())
            stats = dungeon_parser.parse_game_stats()
            self._assert_equal_stats(expected_stats, stats)

    def test_parse_game_html_downstairs(self):
        expected_stats = dungeon.Stats(44, 100)
        expected_stats.inventory = [u'A potion +5', u'B potion +4', u'C potion +4']
        expected_stats.weapon = ("Tester", 30, 1)
        expected_stats.dungeon_level = 31
        with open("content/downstairs.html") as f:
            dungeon_parser = dungeon.DungeonGameHtmlParser(f.read())
            stats = dungeon_parser.parse_game_stats()
            self._assert_equal_stats(expected_stats, stats)

    def test_parse_html_possible_actions_attack_url_without_boss(self):
        expected_actions = dungeon.Actions(attack=1)
        with open("content/attack.html") as f:
            dungeon_parser = dungeon.DungeonGameHtmlParser(f.read())
            actions = dungeon_parser.parse_game_actions()
            self._assert_equal_actions(expected_actions, actions)

    def test_parse_html_possible_actions_attack_url_with_boss(self):
        with open("content/boss.html") as f:
            dungeon_parser = dungeon.DungeonGameHtmlParser(f.read())
            actions = dungeon_parser.parse_game_actions()
            self.assertIsNone(actions)

    def test_parse_html_possible_actions_treasure_url(self):
        expected_actions = dungeon.Actions(south=1, north=1, east=1, treasure=u'Level 31 Tester +2')
        with open("content/treasure.html") as f:
            dungeon_parser = dungeon.DungeonGameHtmlParser(f.read())
            actions = dungeon_parser.parse_game_actions()
            self._assert_equal_actions(expected_actions, actions)

    def test_parse_html_possible_actions_downstairs_url(self):
        expected_actions = dungeon.Actions(west=1, south=1, east=1, downstairs=1)
        with open("content/downstairs.html") as f:
            dungeon_parser = dungeon.DungeonGameHtmlParser(f.read())
            actions = dungeon_parser.parse_game_actions()
            self._assert_equal_actions(expected_actions, actions)

    def _assert_equal_actions(self, expected_actions, actions):
        self.assertEqual(expected_actions.move_north, actions.move_north)
        self.assertEqual(expected_actions.move_south, actions.move_south)
        self.assertEqual(expected_actions.move_west, actions.move_west)
        self.assertEqual(expected_actions.move_east, actions.move_east)
        self.assertEqual(expected_actions.attack, actions.attack)
        self.assertEqual(expected_actions.treasure, actions.treasure)
        self.assertEqual(expected_actions.downstairs, actions.downstairs)

    def _assert_equal_stats(self, expected_stats, stats):
        self.assertEqual(expected_stats.health, stats.health)
        self.assertEqual(expected_stats.level, stats.level)
        self.assertEqual(expected_stats.inventory, stats.inventory)
        self.assertEqual(expected_stats.weapon, stats.weapon)
        self.assertEqual(expected_stats.dungeon_level, stats.dungeon_level)


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


class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = dungeon.Board()

    def test_move_north_from_scratch(self):
        self.board.move_north()
        self.assertEqual((0, 1), self.board.current_position)
        self.assertEqual({0: [0, 1]}, self.board.board)

    def test_move_north_to_existing(self):
        expected_board = {0: [0, 1], 1: [0, 1]}
        self.board.board = expected_board
        self.board.current_position = (1, 0)
        self.board.move_north()
        self.assertEqual((1, 1), self.board.current_position)
        self.assertEqual(expected_board, self.board.board)

    def test_move_south_from_scratch(self):
        self.board.move_south()
        self.assertEqual((0, -1), self.board.current_position)
        self.assertEqual({0: [0, -1]}, self.board.board)

    def test_move_south_to_existing(self):
        expected_board = {0: [0, 1], 1: [0, 1]}
        self.board.board = expected_board
        self.board.current_position = (1, 1)
        self.board.move_south()
        self.assertEqual((1, 0), self.board.current_position)
        self.assertEqual(expected_board, self.board.board)

    def test_move_east_from_scratch(self):
        self.board.move_east()
        self.assertEqual((1, 0), self.board.current_position)
        self.assertEqual({0: [0], 1: [0]}, self.board.board)

    def test_move_east_to_existing(self):
        expected_board = {0: [0, 1], 1: [0, 1]}
        self.board.board = expected_board
        self.board.current_position = (0, 1)
        self.board.move_east()
        self.assertEqual((1, 1), self.board.current_position)
        self.assertEqual(expected_board, self.board.board)

    def test_move_west_from_scratch(self):
        self.board.move_west()
        self.assertEqual((-1, 0), self.board.current_position)
        self.assertEqual({0: [0], -1: [0]}, self.board.board)

    def test_move_west_to_existing(self):
        expected_board = {0: [0, 1], -1: [0, 1]}
        self.board.board = expected_board
        self.board.current_position = (0, 1)
        self.board.move_west()
        self.assertEqual((-1, 1), self.board.current_position)
        self.assertEqual(expected_board, self.board.board)

    def test_is_south(self):
        self.assertTrue(self.board.is_south((0, -1)))

    def test_is_north(self):
        self.assertTrue(self.board.is_north((0, 1)))

    def test_is_east(self):
        self.assertTrue(self.board.is_east((1, 0)))

    def test_is_west(self):
        self.assertTrue(self.board.is_west((-1, 0)))


class MockResponse(object):
    def __init__(self, text, status_code):
        self.text = text
        self.status_code = status_code

    def text(self):
        return self.text

if __name__ == '__main__':
    unittest.main()
