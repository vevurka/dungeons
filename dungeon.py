from bs4 import BeautifulSoup

import requests


class DungeonGameUrls(object):
    def __init__(self, base_url, cookie_jar):
        self.base_url = base_url
        self.cookies = cookie_jar

    def get_attack_url(self):
        return self.base_url + "?attack=1"

    def get_move_url(self, direction):
        print "going " + direction
        return self.base_url + "?m=" + direction

    def get_treasure_url(self):
        return self.base_url + "?tres=1"

    # not tested
    def send_get_treasure_request(self):
        response = requests.get(self.get_treasure_url(), cookies=self.cookies)
        return response.text

    # not tested
    def send_move_request(self, direction):
        response = requests.get(self.get_move_url(direction), cookies=self.cookies)
        return response.text

    # not tested
    def send_attack_request(self):
        response = requests.get(self.get_attack_url(), cookies=self.cookies)
        return response.text

    # not tested
    def send_base_request(self):
        response = requests.get(self.base_url, cookies=self.cookies)
        return response.text

# TODO:
# 1. Refactor tests (get.requests mock and url methods) to allow functional tests
# 2. Refactor reading html - not so many requests
# 3. Refactor moving logic?
# 4. Usage of potions


class DungeonGame(object):
    def __init__(self, dungeon_game_urls):
        self.stats = Stats(0, 0)
        self.board = Board()
        self.dungeon_game_urls = dungeon_game_urls
        self.actions = Actions()

    def update_stats(self, url):
        response = requests.get(url, cookies=self.dungeon_game_urls.cookies) #TODO: it should be from loaded html
        dungeon_parser = DungeonGameHtmlParser(response.text)
        self.stats = dungeon_parser.parse_game_stats()

    # not tested
    def get_actions(self, url):
        response = requests.get(url, cookies=self.dungeon_game_urls.cookies) #TODO: it should be from loaded html
        dungeon_parser = DungeonGameHtmlParser(response.text)
        self.actions = dungeon_parser.parse_game_actions()

    # not tested
    def game_logic(self):
        self.update_stats(self.dungeon_game_urls.base_url)
        self.get_actions(self.dungeon_game_urls.base_url)
        while self.actions is not None:
            self.board = Board()
            found_downstairs_and_ready = False
            found_start_position = False
            picked_up_treasure = None
            while not found_downstairs_and_ready and self.actions is not None:
                self.update_stats(self.dungeon_game_urls.base_url)
                self.get_actions(self.dungeon_game_urls.base_url)

                if self.actions.attack == 1:
                    self.attack()
                elif self.actions.treasure is not None and picked_up_treasure is None:
                    picked_up_treasure = self.pick_up_treasure()
                elif self.actions.downstairs == 1:
                    picked_up_treasure = None
                    print "downstairs?"
                    print "action down: ", self.actions.downstairs
                    print "stats: ", self.stats.level, self.stats.dungeon_level
                    print "current pos ", self.board.current_position
                    self.board.downstairs = self.board.current_position
                    found_downstairs_and_ready = self.move_downstairs()
                elif found_start_position:
                    picked_up_treasure = None
                    print "action down: ", self.actions.downstairs
                    print "stats: ", self.stats.level, self.stats.dungeon_level
                    print "current pos ", self.board.current_position
                    self.move()  # this appends to board
                else:
                    print "looking for start pos"
                    picked_up_treasure = None
                    self.board = Board()
                    found_start_position = self.move_to_start_position()

    # not tested
    def attack(self):
        return self.dungeon_game_urls.send_attack_request()

    # not tested
    def pick_up_treasure(self):
        if "potion" not in self.actions.treasure.lower():
            if self.stats.compare_weapons(
                    DungeonGameHtmlParser.parse_weapon(self.actions.treasure), self.stats.weapon):
                self.dungeon_game_urls.send_get_treasure_request()
                return True
        return False

    # not tested
    def move(self):
        if self.board.downstairs is not None:
            print "only wandering s-n our downstairs is ", self.board.downstairs, "our position ", self.board.current_position
            if self.board.is_south(self.board.downstairs):
                self.board.move_south()
                self.dungeon_game_urls.send_move_request('s')
            elif self.board.is_north(self.board.downstairs):
                self.board.move_north()
                self.dungeon_game_urls.send_move_request('n')
            elif self.board.is_east(self.board.downstairs):
                self.board.move_east()
                self.dungeon_game_urls.send_move_request('e')
            elif self.board.is_west(self.board.downstairs):
                self.board.move_west()
                self.dungeon_game_urls.send_move_request('w')
            else:
                print "we are on a downstairs position but we are not ready"
                if self.actions.move_south == 1:
                    self.board.move_south()
                    self.dungeon_game_urls.send_move_request('s')
                elif self.actions.move_north == 1:
                    self.board.move_north()
                    self.dungeon_game_urls.send_move_request('n')
        else:
            if self.actions.move_east == 1 and not self.board.been_east():
                self.board.move_east()
                self.dungeon_game_urls.send_move_request('e')
            elif self.actions.move_west == 1 and not self.board.been_west():
                self.board.move_west()
                self.dungeon_game_urls.send_move_request('w')
            elif self.actions.move_north == 1 and ((self.board.been_east() and self.actions.move_west != 1) ^
                                                       (self.board.been_west() and self.actions.move_east != 1)):
                self.board.move_north()
                self.dungeon_game_urls.send_move_request('n')
            else:
                print "#### i think it's unused code - ~146"
                self.board.move_south()
                self.dungeon_game_urls.send_move_request('s')

    # not tested
    def move_downstairs(self):
        print "deciding if moving downstairs ", self.stats.level, " ", self.stats.dungeon_level
        if self.stats.level - 2 > self.stats.dungeon_level:
            self.dungeon_game_urls.send_move_request("d")
            self.board = Board()
            return True
        else:
            self.move()
            return False

    # not tested
    def move_to_start_position(self):
        if self.actions.move_south == 1:
            self.dungeon_game_urls.send_move_request("s")
            return False
        elif self.actions.move_west == 1:
            self.dungeon_game_urls.send_move_request("w")
            return False
        return True


class Board(object):
    def __init__(self):
        self.board = {0: [0]}
        self.current_position = (0, 0)
        self.downstairs = None

    def move_north(self):
        x, y = self.current_position
        self.current_position = (x, y+1)
        self._append_position_to_board()

    def move_east(self):
        x, y = self.current_position
        self.current_position = (x+1, y)
        self._append_position_to_board()

    def move_west(self):
        x, y = self.current_position
        self.current_position = (x-1, y)
        self._append_position_to_board()

    def been_west(self):
        x, y = self.current_position
        if self.board.get(x-1) is None:
            return False
        return y in self.board.get(x-1)

    def been_east(self):
        x, y = self.current_position
        if self.board.get(x+1) is None:
            return False
        return y in self.board.get(x+1)

    def move_south(self):
        x, y = self.current_position
        self.current_position = (x, y-1)
        self._append_position_to_board()

    def _append_position_to_board(self):
        x, y = self.current_position
        if self.board.get(x) is None:
            self.board[x] = [y]
        elif y not in self.board.get(x):
            self.board[x].append(y)

    def is_south(self, position):
        _x_current, y_current = self.current_position
        _x_pos, y_pos = position
        return y_pos < y_current

    def is_north(self, position):
        _x_current, y_current = self.current_position
        x_pos, y_pos = position
        return y_pos > y_current

    def is_east(self, position):
        x_current, _y_current = self.current_position
        x_pos, _y_pos = position
        return x_pos > x_current

    def is_west(self, position):
        x_current, _y_current = self.current_position
        x_pos, _y_pos = position
        return x_pos < x_current


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
        if 'stands before you' in self.game_html:
            print self.game_html
            return None
        soup_href = self.parser.find_all('a')
        actions_dict = {}
        for tag in soup_href:
            if '?tres' in tag.get('href'):
                actions_dict['treasure'] = tag.text
            else:
                actions_dict[tag.text.lower().replace('!', '').replace(' ', '')] = 1
        return Actions(**actions_dict)

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
        self.treasure = kwargs.get('treasure')
        self.downstairs = kwargs.get('downstairs')

    def __str__(self):
        return str({"n": self.move_north,
                    "s": self.move_north,
                    "w": self.move_west,
                    "e": self.move_east,
                    "attack": self.attack,
                    "tres": self.treasure,
                    "d": self.downstairs})


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

    def __str__(self):
        return str({"level": self.level,
                    "health": self.health,
                    "inv": self.inventory,
                    "weapon": self.weapon,
                    "dungeon_level": self.dungeon_level})
