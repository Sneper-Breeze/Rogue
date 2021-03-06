import random
import os
import pygame as pg

TILE_SIZE = 32

import copy
ENEMIES = [':', '%']


class Generator:
    def __init__(self, tiles):
        self.width = 100 # Ширина всей карты
        self.height = 100 # Длина (высота) всей карты
        self.max_rooms = 20 # Максимальное количество комнат
        self.min_room_dimens = 10 # Минимальный размер комнаты
        self.max_room_dimens = 30 # Максимальный размер комнаты
        self.rooms_overlap = False # Должны ли комнаты соединяться (когда между ними стена в 1 блок)
        self.random_connections = 0 # Количество случайных корридоров между комнатами
        self.random_spurs = 0 # Количество случайных тупиков
        self.tiles = tiles
        self.level = list()
        self.room_list = list()
        self.corridor_list = list()
        self.tiles_level = list()
        self.gen_level()
        self.gen_tiles_level()
        self.spawn_player()
        self.spawn_enemies()

    def gen_room(self):
        x, y, w, h = 0, 0, 0, 0

        w = random.randint(self.min_room_dimens, self.max_room_dimens)
        h = random.randint(self.min_room_dimens, self.max_room_dimens)
        x = random.randint(1, (self.width - w - 1))
        y = random.randint(1, (self.height - h - 1))

        return [x, y, w, h]

    def room_overlapping(self, room, room_list):
        x, y, w, h = room

        for current_room in room_list:
            if (x < (current_room[0] + current_room[2]) and current_room[0] < (x + w) and
                y < (current_room[1] + current_room[3]) and current_room[1] < (y + h)):
                return True

        return False


    def corridor_between_points(self, x1, y1, x2, y2, join_type='either'):
        if x1 == x2 and y1 == y2 or x1 == x2 or y1 == y2:
            return [(x1, y1), (x2, y2)]
        else:
            join = None
            if join_type == 'either' and set([0, 1]).intersection(
                 set([x1, x2, y1, y2])):

                join = 'bottom'
            elif join_type == 'either' and set([self.width - 1,
                 self.width - 2]).intersection(set([x1, x2])) or set(
                 [self.height - 1, self.height - 2]).intersection(
                 set([y1, y2])):

                join = 'top'
            elif join_type == 'either':
                join = random.choice(['top', 'bottom'])
            else:
                join = join_type

            if join == 'top':
                return [(x1, y1), (x1, y2), (x2, y2)]
            elif join == 'bottom':
                return [(x1, y1), (x2, y1), (x2, y2)]

    def join_rooms(self, room_1, room_2, join_type='either'):
        # sort by the value of x
        sorted_room = [room_1, room_2]
        sorted_room.sort(key=lambda x_y: x_y[0])

        x1 = sorted_room[0][0]
        y1 = sorted_room[0][1]
        w1 = sorted_room[0][2]
        h1 = sorted_room[0][3]
        x1_2 = x1 + w1 - 1
        y1_2 = y1 + h1 - 1

        x2 = sorted_room[1][0]
        y2 = sorted_room[1][1]
        w2 = sorted_room[1][2]
        h2 = sorted_room[1][3]
        x2_2 = x2 + w2 - 1
        y2_2 = y2 + h2 - 1

        # overlapping on x
        if x1 < (x2 + w2) and x2 < (x1 + w1):
            jx1 = random.randint(x2, x1_2)
            jx2 = jx1
            tmp_y = [y1, y2, y1_2, y2_2]
            tmp_y.sort()
            jy1 = tmp_y[1] + 1
            jy2 = tmp_y[2] - 1

            corridors = self.corridor_between_points(jx1, jy1, jx2, jy2)
            self.corridor_list.append(corridors)

        # overlapping on y
        elif y1 < (y2 + h2) and y2 < (y1 + h1):
            if y2 > y1:
                jy1 = random.randint(y2, y1_2)
                jy2 = jy1
            else:
                jy1 = random.randint(y1, y2_2)
                jy2 = jy1
            tmp_x = [x1, x2, x1_2, x2_2]
            tmp_x.sort()
            jx1 = tmp_x[1] + 1
            jx2 = tmp_x[2] - 1

            corridors = self.corridor_between_points(jx1, jy1, jx2, jy2)
            self.corridor_list.append(corridors)

        # no overlap
        else:
            join = None
            if join_type == 'either':
                join = random.choice(['top', 'bottom'])
            else:
                join = join_type

            if join == 'top':
                if y2 > y1:
                    jx1 = x1_2 + 1
                    jy1 = random.randint(y1, y1_2)
                    jx2 = random.randint(x2, x2_2)
                    jy2 = y2 - 1
                    corridors = self.corridor_between_points(
                        jx1, jy1, jx2, jy2, 'bottom')
                    self.corridor_list.append(corridors)
                else:
                    jx1 = random.randint(x1, x1_2)
                    jy1 = y1 - 1
                    jx2 = x2 - 1
                    jy2 = random.randint(y2, y2_2)
                    corridors = self.corridor_between_points(
                        jx1, jy1, jx2, jy2, 'top')
                    self.corridor_list.append(corridors)

            elif join == 'bottom':
                if y2 > y1:
                    jx1 = random.randint(x1, x1_2)
                    jy1 = y1_2 + 1
                    jx2 = x2 - 1
                    jy2 = random.randint(y2, y2_2)
                    corridors = self.corridor_between_points(
                        jx1, jy1, jx2, jy2, 'top')
                    self.corridor_list.append(corridors)
                else:
                    jx1 = x1_2 + 1
                    jy1 = random.randint(y1, y1_2)
                    jx2 = random.randint(x2, x2_2)
                    jy2 = y2_2 + 1
                    corridors = self.corridor_between_points(
                        jx1, jy1, jx2, jy2, 'bottom')
                    self.corridor_list.append(corridors)


    def gen_level(self):
        for i in range(self.height):
            self.level.append([' '] * self.width)
        self.room_list = []
        self.corridor_list = []

        max_iters = self.max_rooms * 5

        for a in range(max_iters):
            tmp_room = self.gen_room()

            if self.rooms_overlap or not self.room_list:
                self.room_list.append(tmp_room)
            else:
                tmp_room = self.gen_room()
                tmp_room_list = self.room_list[:]

                if self.room_overlapping(tmp_room, tmp_room_list) == False:
                    self.room_list.append(tmp_room)

            if len(self.room_list) >= self.max_rooms:
                break

        # connect the rooms
        for a in range(len(self.room_list) - 1):
            self.join_rooms(self.room_list[a], self.room_list[a + 1])

        # do the random joins
        for a in range(self.random_connections):
            room_1 = self.room_list[random.randint(0, len(self.room_list) - 1)]
            room_2 = self.room_list[random.randint(0, len(self.room_list) - 1)]
            self.join_rooms(room_1, room_2)

        # do the spurs
        for a in range(self.random_spurs):
            room_1 = [random.randint(2, self.width - 2), random.randint(
                     2, self.height - 2), 1, 1]
            room_2 = self.room_list[random.randint(0, len(self.room_list) - 1)]
            self.join_rooms(room_1, room_2)

        # fill the map
        # paint rooms
        for room_num, room in enumerate(self.room_list):
            for b in range(room[2]):
                for c in range(room[3]):
                    self.level[room[1] + c][room[0] + b] = '.'

        # paint corridors
        for corridor in self.corridor_list:
            x1, y1 = corridor[0]
            x2, y2 = corridor[1]
            for width in range(abs(x1 - x2) + 1):
                for height in range(abs(y1 - y2) + 1):
                    self.level[min(y1, y2) + height][
                        min(x1, x2) + width] = '.'

            if len(corridor) == 3:
                x3, y3 = corridor[2]

                for width in range(abs(x2 - x3) + 1):
                    for height in range(abs(y2 - y3) + 1):
                        self.level[min(y2, y3) + height][
                            min(x2, x3) + width] = '.'

        # paint the walls
        for row in range(1, self.height - 1):
            for col in range(1, self.width - 1):
                if self.level[row][col] == '.':
                    if self.level[row - 1][col - 1] == ' ':
                        self.level[row - 1][col - 1] = '#'

                    if self.level[row - 1][col] == ' ':
                        self.level[row - 1][col] = '#'

                    if self.level[row - 1][col + 1] == ' ':
                        self.level[row - 1][col + 1] = '#'

                    if self.level[row][col - 1] == ' ':
                        self.level[row][col - 1] = '#'

                    if self.level[row][col + 1] == ' ':
                        self.level[row][col + 1] = '#'

                    if self.level[row + 1][col - 1] == ' ':
                        self.level[row + 1][col - 1] = '#'

                    if self.level[row + 1][col] == ' ':
                        self.level[row + 1][col] = '#'

                    if self.level[row + 1][col + 1] == ' ':
                        self.level[row + 1][col + 1] = '#'

    def gen_tiles_level(self):

        for row_num, row in enumerate(self.level):
            tmp_tiles = []

            for col_num, col in enumerate(row):
                if col == ' ':
                    tmp_tiles.append(' ')
                if col == '.':
                    tmp_tiles.append('.')
                if col == '#':
                    tmp_tiles.append('#')

            self.tiles_level.append(''.join(tmp_tiles))


    def spawn_player(self):
        starting_room = random.choice(range(len(self.room_list)))
        self.rooms_for_enemies = copy.deepcopy(self.room_list)
        starting_room = self.rooms_for_enemies.pop(starting_room)
        start_x = starting_room[0] + starting_room[2] // 2
        start_y = starting_room[1] + starting_room[3] // 2
        self.starting_point = [start_x * TILE_SIZE, start_y * TILE_SIZE]

    def spawn_enemies(self):
        for room in self.rooms_for_enemies:
            y = 0
            x = 0
            while self.level[y][x] != '.':
                x1 = room[0] + 2
                x2 = room[2] - 2 + room[0]
                x = random.randint(x1, x2)
                y1 = room[1] + 2
                y2 = room[3] - 2 + room[1]
                y = random.randint(y1, y2)
            self.level[y][x] = random.choice(ENEMIES)
