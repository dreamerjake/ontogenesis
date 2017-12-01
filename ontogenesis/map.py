from math import sqrt
import random

import pygame as pg

import settings


class Camera:
    def __init__(self, width, height):
        self.camera = pg.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.x + int(settings.WIDTH / 2)
        y = -target.rect.y + int(settings.HEIGHT / 2)

        # limit scrolling to map boundaries
        x = min(0, x)
        y = min(0, y)
        x = max(-(self.width - settings.WIDTH), x)
        y = max(-(self.height - settings.HEIGHT), y)

        self.camera = pg.Rect(x, y, self.width, self.height)


class Map:
    def __init__(self, game, tilewidth, tileheight):
        self.game = game
        self.tilewidth = tilewidth
        self.tileheight = tileheight
        self.width = self.tilewidth * settings.TILESIZE
        self.height = self.tileheight * settings.TILESIZE
        self.generator = CellularAutomata()
        self.data = self.generator.generate_level(self.tilewidth, self.tileheight)
        self.player_start = None

        for x in range(self.tilewidth):
            for y in range(self.tileheight):

                if self.data[x][y] == 1:
                    Wall(self.game, x, y)

                    if self.game.debug:
                        print("Spawned Wall at ({}, {})".format(x, y))

                elif self.player_start is None:
                    tile_center_x = x * settings.TILESIZE + settings.TILESIZE / 2
                    tile_center_y = y * settings.TILESIZE + settings.TILESIZE / 2
                    self.player_start = (tile_center_x, tile_center_y)

                    if self.game.debug:
                        print("Player starting coordinates set to: {}".format(self.player_start))


class Wall(pg.sprite.Sprite):
    """ Your basic movement-blocking map element """
    # Destructable?
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.walls
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((settings.TILESIZE, settings.TILESIZE))
        self.image.fill(settings.BROWN)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * settings.TILESIZE
        self.rect.y = y * settings.TILESIZE


class CellularAutomata:
    """
    adapted from https://github.com/AtTheMatinee/

    Rather than implement a traditional cellular automata, I
    decided to try my hand at a method discribed by "Evil
    Scientist" Andy Stobirski that I recently learned about
    on the Grid Sage Games blog.
    """

    def __init__(self):
        self.level = []

        self.iterations = 30000
        self.neighbors = 4  # number of neighboring walls for this cell to become a wall
        self.wall_probability = 0.50  # probability of a cell becoming a wall, recommended to be between .35 and .55

        self.room_min_size = 16  # size in total number of cells, not dimensions
        self.room_max_size = 500  # size in total number of cells, not dimensions

        self.smooth_edges = True
        self.smoothing = 1

        self.caves = []

    def generate_level(self, map_width, map_height):
        # Creates an empty 2D array or clears existing array

        self.level = [[1
                       for _ in range(map_height)]
                      for _ in range(map_width)]

        self.random_fill_map(map_width, map_height)

        self.create_caves(map_width, map_height)

        self.get_caves(map_width, map_height)

        self.connect_caves(map_width, map_height)

        self.clean_up_map(map_width, map_height)
        return self.level

    def random_fill_map(self, map_width, map_height):
        for y in range(1, map_height - 1):
            for x in range(1, map_width - 1):
                if random.random() >= self.wall_probability:
                    self.level[x][y] = 0

    def create_caves(self, map_width, map_height):
        # ==== Create distinct caves ====
        for i in range(0, self.iterations):
            # Pick a random point with a buffer around the edges of the map
            tile_x = random.randint(1, map_width - 2)  # (2, map_width - 3)
            tile_y = random.randint(1, map_height - 2)  # (2, map_height - 3)

            # if the cell's neighboring walls > self.neighbors, set it to 1
            if self.get_adjacent_walls(tile_x, tile_y) > self.neighbors:
                self.level[tile_x][tile_y] = 1
            # or set it to 0
            elif self.get_adjacent_walls(tile_x, tile_y) < self.neighbors:
                self.level[tile_x][tile_y] = 0

        self.clean_up_map(map_width, map_height)

    def clean_up_map(self, map_width, map_height):
        if self.smooth_edges:
            for i in range(0, 5):
                # Look at each cell individually and check for smoothness
                for x in range(1, map_width - 1):
                    for y in range(1, map_height - 1):
                        if (self.level[x][y] == 1) and (self.get_adjacent_walls_simple(x, y) <= self.smoothing):
                            self.level[x][y] = 0

    def create_tunnel(self, point1, point2, current_cave, map_width, map_height):
        # run a heavily weighted random Walk
        # from point1 to point1
        drunkard_x = point2[0]
        drunkard_y = point2[1]
        while (drunkard_x, drunkard_y) not in current_cave:
            # ==== Choose Direction ====
            north = 1.0
            south = 1.0
            east = 1.0
            west = 1.0

            weight = 1

            # weight the random walk against edges
            if drunkard_x < point1[0]:  # drunkard is left of point1
                east += weight
            elif drunkard_x > point1[0]:  # drunkard is right of point1
                west += weight
            if drunkard_y < point1[1]:  # drunkard is above point1
                south += weight
            elif drunkard_y > point1[1]:  # drunkard is below point1
                north += weight

            # normalize probabilities so they form a range from 0 to 1
            total = north + south + east + west
            north /= total
            south /= total
            east /= total
            west /= total

            # choose the direction
            choice = random.random()
            if 0 <= choice < north:
                dx = 0
                dy = -1
            elif north <= choice < (north + south):
                dx = 0
                dy = 1
            elif (north + south) <= choice < (north + south + east):
                dx = 1
                dy = 0
            else:
                dx = -1
                dy = 0

            # ==== Walk ====
            # check colision at edges
            if (0 < drunkard_x + dx < map_width - 1) and (0 < drunkard_y + dy < map_height - 1):
                drunkard_x += dx
                drunkard_y += dy
                if self.level[drunkard_x][drunkard_y] == 1:
                    self.level[drunkard_x][drunkard_y] = 0

    def get_adjacent_walls_simple(self, x, y):  # finds the walls in four directions
        wall_counter = 0
        # print("(",x,",",y,") = ",self.level[x][y])
        if self.level[x][y - 1] == 1:  # Check north
            wall_counter += 1
        if self.level[x][y + 1] == 1:  # Check south
            wall_counter += 1
        if self.level[x - 1][y] == 1:  # Check west
            wall_counter += 1
        if self.level[x + 1][y] == 1:  # Check east
            wall_counter += 1

        return wall_counter

    def get_adjacent_walls(self, tile_x, tile_y):  # finds the walls in 8 directions
        pass
        wall_counter = 0
        for x in range(tile_x - 1, tile_x + 2):
            for y in range(tile_y - 1, tile_y + 2):
                if self.level[x][y] == 1:
                    if (x != tile_x) or (y != tile_y):  # exclude (tileX,tileY)
                        wall_counter += 1
        return wall_counter

    def get_caves(self, map_width, map_height):
        # locate all the caves within self.level and stor them in self.caves
        for x in range(0, map_width):
            for y in range(0, map_height):
                if self.level[x][y] == 0:
                    self.flood_fill(x, y)

        for tileset in self.caves:
            for tile in tileset:
                self.level[tile[0]][tile[1]] = 0

        # check for 2 that weren't changed.
        """
        The following bit of code doesn't do anything. I 
        put this in to help find mistakes in an earlier 
        version of the algorithm. Still, I don't really 
        want to remove it.
        """
        for x in range(0, map_width):
            for y in range(0, map_height):
                if self.level[x][y] == 2:
                    print("(", x, ",", y, ")")

    def flood_fill(self, x, y):
        """
        flood fill the separate regions of the level, discard
        the regions that are smaller than a minimum size, and
        create a reference for the rest.
        """
        cave = set()
        tile = [(x, y)]
        to_be_filled = set(tile)
        while to_be_filled:
            tile = to_be_filled.pop()

            if tile not in cave:
                cave.add(tile)

                self.level[tile[0]][tile[1]] = 1

                # check adjacent cells
                x = tile[0]
                y = tile[1]
                north = (x, y - 1)
                south = (x, y + 1)
                east = (x + 1, y)
                west = (x - 1, y)

                for direction in [north, south, east, west]:

                    if self.level[direction[0]][direction[1]] == 0:
                        if direction not in to_be_filled and direction not in cave:
                            to_be_filled.add(direction)

        if len(cave) >= self.room_min_size:
            self.caves.append(cave)

    def connect_caves(self, map_width, map_height):
        # Find the closest cave to the current cave
        for current_cave in self.caves:
            for point1 in current_cave:
                break  # get an element from cave1
            point2 = None
            distance = None
            for next_cave in self.caves:
                if next_cave != current_cave and not self.check_connectivity(current_cave, next_cave):
                    # choose a random point from next_cave
                    for next_point in next_cave:
                        break  # get an element from cave1
                    # compare distance of point1 to old and new point2
                    new_distance = self.distance_formula(point1, next_point)
                    if distance is None or (new_distance < float(distance)):
                        point2 = next_point
                        distance = new_distance

            if point2:  # if all tunnels are connected, point2 == None
                self.create_tunnel(point1, point2, current_cave, map_width, map_height)

    @staticmethod
    def distance_formula(point1, point2):
        d = sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)
        return d

    def check_connectivity(self, cave1, cave2):
        # floods cave1, then checks a point in cave2 for the flood

        connected_region = set()

        # for start in cave1:
        #     break  # get an element from cave1
        start = [next(iter(cave1))]

        to_be_filled = set(start)
        while to_be_filled:
            tile = to_be_filled.pop()

            if tile not in connected_region:
                connected_region.add(tile)

                # check adjacent cells
                x = tile[0]
                y = tile[1]
                north = (x, y - 1)
                south = (x, y + 1)
                east = (x + 1, y)
                west = (x - 1, y)

                for direction in [north, south, east, west]:

                    if self.level[direction[0]][direction[1]] == 0:
                        if direction not in to_be_filled and direction not in connected_region:
                            to_be_filled.add(direction)

        # for end in cave2:
        #     break  # get an element from cave2
        end = next(iter(cave2))

        if end in connected_region:
            return True

        else:
            return False
