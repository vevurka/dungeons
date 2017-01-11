from bs4 import BeautifulSoup

import requests


class DungeonGameUrls(object):
    def __init__(self, base_url, cookie_jar):
        self.base_url = base_url
        self.cookies = cookie_jar

    def get_attack_url(self):
        return self.base_url + "?attack=1"

    def get_move_url(self, direction):
        return self.base_url + "?m=" + direction


class DungeonGame(object):
    def __init__(self, dungeon_game_urls):
        self.stats = Stats(0, 0)
        self.board = Board()
        self.dungeon_game_urls = dungeon_game_urls

    def update_stats(self, url):
        response = requests.get(url, cookies=self.dungeon_game_urls.cookies)
        dungeon_parser = DungeonGameHtmlParser(response.text)
        self.stats = dungeon_parser.parse_game_stats()

    def attack(self):
        response = requests.get(self.dungeon_game_urls.base_url, cookies=self.dungeon_game_urls.cookies)
        if "Attack!" in response.content:
            attack_response = requests.get(self.dungeon_game_urls.get_attack_url(), cookies=self.dungeon_game_urls.cookies)
            print "Attacked", attack_response.text
        # TODO: remember about new gear


class Board():
    pass


class DungeonGameHtmlParser(object):
    def __init__(self, game_html):
        self.game_html = game_html
        self.parser = BeautifulSoup(self.game_html, 'html.parser')

    def parse_game_stats(self):
        soup_stats_table = self.parser.find('table', attrs={"border": 1})
        stats_list = []
        rows = soup_stats_table.find_all('tr')
        for row in rows:
            stats_list.append([stat.text for stat in row.find_all('td')])
        health = int(stats_list[1][1])
        level = int(stats_list[1][0])
        stats = Stats(level, health)
        inventory = stats_list[2][0].split("\n")

        stats.inventory = filter(lambda e: "potion" in e, inventory)
        stats.weapon = DungeonGameHtmlParser.parse_weapon(stats_list[1][3])

        soup_dungeon_level_html = self.parser.find('h2')
        stats.dungeon_level = DungeonGameHtmlParser.parse_dungeon_level(soup_dungeon_level_html.text)
        return stats

    def parse_game_actions(self):
        pass

    @staticmethod
    def parse_weapon(weapon_string):
        weapon_tokens = weapon_string.split()
        if len(weapon_tokens) < 4:
            return weapon_tokens[2], int(weapon_tokens[1]), 0
        else:
            return weapon_tokens[2], int(weapon_tokens[1]), int(weapon_tokens[3])

    @staticmethod
    def parse_dungeon_level(dungeon_level_string):
        dungeon_level_tokens = dungeon_level_string.split()
        return int(dungeon_level_tokens[2])


class Actions(object):
    def __init__(self, **kwargs):
        self.move_south = kwargs.get('south')
        self.move_north = kwargs.get('north')
        self.move_west = kwargs.get('west')
        self.move_east = kwargs.get('east')
        self.attack = kwargs.get('attack')


class Stats(object):
    def __init__(self, level, health):
        self.level = level
        self.health = health
        self.inventory = []
        self.weapon = ()
        self.dungeon_level = 0

    @classmethod
    def compare_weapons(cls, weapon1, weapon2):
        name1, level1, addition1 = weapon1
        name2, level2, addition2 = weapon2
        if level1 != level2:
            return level1 > level2
        else:
            return addition1 > addition2
