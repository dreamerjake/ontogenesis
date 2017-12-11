# -*- coding: utf-8 -*-

from io import BytesIO
from itertools import product, combinations, cycle
from math import sqrt
import random

import matplotlib.pyplot as plt
import networkx as nx
import pygame as pg
from pygame.math import Vector2 as Vec2

from enemy import Mob, GiantLizard
from helpers import calc_dist
import settings
from settings import colors


class Camera:
    def __init__(self, width, height):
        self.camera = pg.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.offset = Vec2(1, 0)

    def apply(self, entity, hit_rect=False):
        if hit_rect:
            return entity.hit_rect.move(self.camera.topleft)
        return entity.rect.move(self.camera.topleft)

    def update(self, target, hit_rect=False):
        if hit_rect:
            x = -target.hit_rect.x + int(settings.WIDTH / 2)
            y = -target.hit_rect.y + int(settings.HEIGHT / 2)
        else:
            x = -target.rect.x + int(settings.WIDTH / 2)
            y = -target.rect.y + int(settings.HEIGHT / 2)

        # limit scrolling to map boundaries
        x = min(0, x)
        y = min(0, y)
        x = max(-(self.width - settings.WIDTH), x)
        y = max(-(self.height - settings.HEIGHT), y)

        self.offset = Vec2(x, y)

        self.camera = pg.Rect(x, y, self.width, self.height)


class WorldMap:
    def __init__(self, game, width=20, height=10, min_dist=4, path_base_chance=.1, path_length_bonus=.3):
        self.game = game
        self.mob_types = cycle([Mob, GiantLizard])
        self.image = None
        self.visible = False

        self.border = 100
        self.width = width  # cells
        self.height = height  # cells
        self.min_dist = min_dist  # cells
        self.path_base_chance = path_base_chance
        self.path_length_bonus = path_length_bonus

        self.graph = None
        # print('graph before gen: {}'.format(self.graph))
        self.generate_graph()
        self.generate_image()
        # print('graph after gen: {}'.format(self.graph))

        self.scalex = self.image.get_width() / self.width
        self.scaley = self.image.get_height() / self.height

        # draw worldmap grid
        # line_width = 2
        # for x in range(0, self.width * int(self.scalex), int(self.scalex)):
        #     # print((x, 0), (x, self.image.get_height()))
        #     pg.draw.line(self.image, colors.red, (x, 0), (x, self.image.get_height()), line_width)
        #
        # for y in range(0, self.height * int(self.scaley), int(self.scaley)):
        #     # print((x, 0), (x, self.image.get_height()))
        #     pg.draw.line(self.image, colors.red, (0, y), (self.image.get_width(), y), line_width)

        self.current_node = random.choice([*self.graph.nodes()])  # random starting location for now
        self.discover_node(self.current_node, neighbors=True)
        self.visit_node(self.current_node)
        self.destination_node = None
        # print(self.current_node)
        # nodesAt5 = filter(lambda (n, d): d['at'] == 5, P.nodes(data=True))

        self.rect = self.image.get_rect()

    def calc_prune_chance(self, edge):
        return self.path_base_chance + (self.path_length_bonus * self.min_dist / edge[2]['weight'])

    def generate_image(self):
        bg = self.game.worldmap_background.copy()
        bg = pg.transform.scale(bg, (settings.WIDTH - self.border * 2, settings.HEIGHT - self.border * 2))
        # bg.set_colorkey(bg.get_at((0, 0)))
        self.image = bg

    def discover_node(self, node, neighbors=False):
        self.graph.node[node]['discovered'] = True
        if neighbors:
            for neighbor in self.graph.neighbors(node):
                self.graph.node[neighbor]['discovered'] = True

    def visit_node(self, node):
        self.graph.node[node]['visited'] = True

    def generate_graph(self):
        print('Generating new WorldMap')
        graph = nx.Graph()
        node_coords = []
        tile_coords = [tile for tile in product(range(1, self.width - 1), range(1, self.height - 1))]
        random.shuffle(tile_coords)
        for location in tile_coords:
            for node in node_coords:
                if calc_dist(location, node) < self.min_dist:
                    break
            else:
                node_coords.append(location)
        # scale node coordinates to map image locations
        # node_coords = [(int(node[0] * self.scalex), int(node[1] * self.scaley)) for node in node_coords]
        nodes = {pos: {'name': pos, 'position': pos, 'discovered': False, 'visited': False, 'mobtype': next(self.mob_types)} for node_name, pos in enumerate(node_coords)}
        # labels = {node: next(self.mob_types) for node in nodes}
        #
        # node_positions = {k: k for k, v in nodes.items()}

        edges = [(edge[0], edge[1], {'weight': calc_dist(edge[0], edge[1])}) for edge in combinations(node_coords, 2)]

        prune_targets = [edge for edge in edges if self.calc_prune_chance(edge) < random.random()]

        graph.add_nodes_from(nodes.items())
        graph.add_edges_from(edges)

        # prune the prune targets in random order *unless they are the only remaining path to the node*
        random.shuffle(prune_targets)
        for target in prune_targets:
            if len(graph[target[0]]) > 1 and len(graph[target[1]]) > 1:
                graph.remove_edge(*target[:2])

        # recurse if we end up with a unconnected graph
        # TODO: check if the largest subgraph is "large enough" and maybe use it
        if not nx.is_connected(graph):
            print("NOT CONNECTED - generating new worldmap graph")
            self.generate_graph()
        else:
            print("CONNECTED - setting worldmap graph")
            self.graph = graph
            # print(graph)
        # return graph
        # print('TEST')
        # print(graph.nodes())
        # self.graph = graph

        # aspect_ratio = settings.WIDTH / settings.HEIGHT

        # fig = plt.figure(figsize=(10 * aspect_ratio, 10))
        #
        # nx.draw_networkx(graph, node_positions, node_size=1600, node_color='r', font_size=12, with_labels=False,
        #                  width=4)
        # nx.draw_networkx_labels(graph, node_positions, labels, font_size=16, font_color='white')
        #
        # print(plt.gca().get_ylim())
        # plt.gca().set_ylim(0, self.height)
        # print(plt.gca().get_ylim())
        #
        # plt.gca().set_xlim(0, self.width)
        #
        # plt.gca().invert_yaxis()
        #
        # plt.axis('off')
        #
        # buf = BytesIO()
        # fig.savefig(buf, format='png', bbox_inches='tight')
        # buf.seek(0)
        #
        # # image = pg.Surface((width, height), pg.SRCALPHA)
        # image = pg.image.load(buf).convert()  # .convert_alpha()
        # # image = pg.transform.flip(image, False, True)
        # image = pg.transform.scale(image, (settings.WIDTH - border * 2, settings.HEIGHT - border * 2))
        # image.set_colorkey(image.get_at((0, 0)))

        # bg = self.game.worldmap_background.copy()
        # bg = pg.transform.scale(bg, (settings.WIDTH - self.border * 2, settings.HEIGHT - self.border * 2))
        # bg.set_colorkey(bg.get_at((0, 0)))
        # # bg.blit(image, (0, 0))
        #
        # self.image = bg

        # for y in range(0, self.current_map.height, settings.TILESIZE):
        #     start_pos = (0, y + self.camera.offset[1])
        #     end_pos = (settings.WIDTH, y + self.camera.offset[1])
        #     pg.draw.line(self.screen, colors.lightgrey, start_pos, end_pos, line_width)

        # if not nx.is_connected(graph):
        #     print("generating new worldmap graph")
        #     self.generate()
        # else:
        #     self.graph = graph
        #     print(graph)
        # return graph

    def get_node_pos(self, node):
        return int(node[0] * self.game.worldmap.scalex) + 100 + int(self.game.worldmap.scalex / 2), int(
            node[1] * self.game.worldmap.scaley) + 100 + int(self.game.worldmap.scaley / 2)

    def get_closest_node(self, pos):
        # node_coords = [(int(node[0] * self.scalex), int(node[1] * self.scaley)) for node in node_coords]
        available = self.graph.neighbors(self.current_node)
        distances = {node: calc_dist(pos, (int(node[0] * self.scalex) + 100, int(node[1] * self.scaley) + 100)) for node in available}

        # selection validation
        # del distances[self.current_node]
        # print(distances)
        return min(distances, key=distances.get)

    def process_input(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            relative_pos = Vec2(event.pos)  # - Vec2(self.button_up.get_abs_offset()) - Vec2(self.rect.topleft)
            closest_node = self.get_closest_node(relative_pos)
            self.destination_node = closest_node


class Map:
    """ who needs a map? """
    # TODO: this should probably be refactored, currently it's just a container with no methods
    # TODO: get_cave method, which returns the cave that a given (x, y) position is in
    def __init__(self, game, tilewidth, tileheight):
        self.game = game
        self.tilewidth = tilewidth
        self.tileheight = tileheight
        self.width = self.tilewidth * settings.TILESIZE
        self.height = self.tileheight * settings.TILESIZE
        self.generator = CellularAutomata()
        self.data = self.generator.generate_level(self.tilewidth, self.tileheight)
        # self.caves = self.generator.caves

        self.clusters = []

        self.player_start = None


class Wall(pg.sprite.Sprite):
    """ Your basic movement-blocking map element """

    debugname = 'Wall'

    def __init__(self, game, start_pos):
        self.groups = game.all_sprites, game.walls
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((settings.TILESIZE, settings.TILESIZE))
        self.image.fill(colors.brown)
        self.rect = self.image.get_rect()
        self.x, self.y = start_pos
        self.rect.x = self.x  # * settings.TILESIZE
        self.rect.y = self.y  # * settings.TILESIZE


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
        self.wall_probability = 0.35  # probability of a cell becoming a wall, recommended to be between .35 and .55

        self.room_min_size = 16  # size in total number of cells, not dimensions
        self.room_max_size = 500  # size in total number of cells, not dimensions

        self.smooth_edges = True
        self.smoothing = 1

        self.caves = []

    def generate_level(self, map_width, map_height):
        # Creates an empty 2D array or clears existing array

        self.level = [[1 for _ in range(map_height)] for _ in range(map_width)]

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
        # run a heavily weighted Random Walk from point1 to point1
        drunkard_x = point2[0]
        drunkard_y = point2[1]

        while (drunkard_x, drunkard_y) not in current_cave:
            # Choose direction
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
        """ locate all the caves within self.level and store them in self.caves """
        for x in range(0, map_width):
            for y in range(0, map_height):
                if self.level[x][y] == 0:
                    self.flood_fill(x, y)

        for tileset in self.caves:
            for tile in tileset:
                self.level[tile[0]][tile[1]] = 0

    def flood_fill(self, x, y):
        """
        1. flood fill the separate regions of the level
        2. discard the regions that are smaller than a minimum size
        3. create a reference for the rest.
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
            point1 = next(iter(current_cave))  # get an arbitrary element from cave1
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
        # TODO: Move this somewhere for general use
        d = sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)
        return d

    def check_connectivity(self, cave1, cave2):
        # floods cave1, then checks a point in cave2 for the flood

        connected_region = set()
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

        end = next(iter(cave2))

        if end in connected_region:
            return True

        else:
            return False
