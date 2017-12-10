# -*- coding: utf-8 -*-

from os import path
import sys
import time

import networkx as nx
import pygame as pg
from pygame.locals import FULLSCREEN
from pygame.math import Vector2 as Vec2

from helpers import calc_dist
from map import Map, WorldMap, Camera, Wall
from player import Player
from enemy import Mob, Collider
from ui import UI
import settings
from settings import colors, game_configs


class MessageQueue:
    def __init__(self, max_size):
        self._queue = []
        self.max_size = max_size

    def __len__(self):
        self.reap()
        return len(self._queue)

    def __bool__(self):
        return len(self) > 0

    def reap(self):
        self._queue = [item for item in self._queue if item[0] > time.time()]

    def put(self, message, ttl):
        self.reap()
        self._queue.append((time.time() + ttl, message))
        if len(self._queue) > self.max_size:
            self._queue.pop()

    def get(self):
        self.reap()
        return [item[1] for item in self._queue]


def timeit(method):
    """ basic timing decorator that prints debug messages to stdout if SYSTEM_DEBUG is on"""
    def timed(*args, **kwargs):
        if not settings.SYSTEM_DEBUG:
            return method(*args, **kwargs)
        ts = time.time()
        result = method(*args, **kwargs)
        te = time.time()

        print('{} completed in {:.2f} ms'.format(method.__qualname__, (te - ts) * 1000))

        return result

    return timed


class Spritesheet:
    """ Helper class for working with spritesheets"""
    def __init__(self, filename):
        self.spritesheet = pg.image.load(filename).convert_alpha()

    def get_image(self, x, y, width, height, rot=None, scale_to=None):
        """ Gets a single image from the spritesheet"""
        image = pg.Surface((width, height), pg.SRCALPHA)
        image.blit(self.spritesheet, (0, 0), (x, y, width, height))
        if scale_to:
            image = pg.transform.scale(image, scale_to)
        if rot:
            image = pg.transform.rotate(image, rot)
        return image


class StateMachine:
    """
    A very simple FSM class.
    adapted from https://news.ycombinator.com/item?id=14634947

    Params:
        initial: Initial state
        table: A dict (current, event) -> target
    """

    def __init__(self, game, initial, table):
        self.current_state = initial
        self.state_table = table
        self.game = game

    def __call__(self, event):
        """Trigger one state transition."""
        # self.current_state = self.state_table[self.current_state, event]
        next_state = self.state_table.get((self.current_state, event), self.current_state)
        changed = self.current_state != next_state
        if self.game.configs.debug and changed:
            debug_msg = "State change event: {} - current state: {} - next state: {} (Changed={})"
            print(debug_msg.format(event, self.current_state, next_state, changed))
        if changed:
            self.current_state = next_state


class Game:
    """ The master Game object"""

    @timeit
    def __init__(self, name):
        self.name = name

        # pygame initialization
        pg.mixer.pre_init(44100, -16, 4, 2048)  # frequency, size, channels, buffersize
        pg.init()
        self.sfx_channel = pg.mixer.Channel(0)

        # configs
        self.configs = game_configs

        # display
        self.fullscreen = settings.FULLSCREEN
        self.available_resolutions = pg.display.list_modes()
        self.screensize = (settings.WIDTH, settings.HEIGHT)
        self.screen = self.screen_update()
        self.effects_screen = self.screen.copy().convert_alpha()
        self.current_music = None

        # time
        self.clock = pg.time.Clock()
        self.delta_time = None
        self.delayed_events = []

        # messages, debug, and logging
        self.suppressed_debug_messages = 0
        self.message_flash_queue = MessageQueue(self.configs.flash_messages_queuesize)

        # assets
        self.hud_font = None
        self.message_flash_font = None
        self.settings_font = None
        self.player_move_spritesheet = None
        self.load_assets()

        # sprite groups
        self.all_sprites = pg.sprite.LayeredUpdates()
        # self.ui_elements = pg.sprite.Group()
        self.hud = pg.sprite.Group()
        self.walls = pg.sprite.Group()
        self.mobs = pg.sprite.Group()
        self.projectiles = pg.sprite.Group()

        # components
        self.ui = UI(self)
        self.worldmap = None
        self.player = None
        self.camera = None

        # map stuff
        self.current_map = None
        # self.player_start = self.map.player_start

        # state machine
        self.state_table = {
            # menus
            ('main_menu', 'new_game'): 'playing',
            ('main_menu', 'next'): 'playing',

            ('skills_menu', 'next'): 'playing',
            ('skills_menu', 'view_skills'): 'playing',
            ('skills_menu', 'paused'): 'paused',
            ('skills_menu', 'info'): 'skill_detail',
            ('skills_menu', 'view_map'): 'map_menu',

            ('skill_detail', 'view_skills'): 'skills_menu',
            ('skill_detail', 'view_map'): 'map_menu',
            ('skill_detail', 'back'): 'skills_menu',  # universal back button?

            ('map_menu', 'paused'): 'paused',
            ('map_menu', 'view_skills'): 'skills_menu',
            ('map_menu', 'view_map'): 'playing',
            ('map_menu', 'next'): 'playing',

            # gameplay
            ('playing', 'paused'): 'paused',
            ('playing', 'die'): 'game_over',
            ('playing', 'view_skills'): 'skills_menu',
            ('playing', 'view_map'): 'map_menu',

            ('paused', 'paused'): 'playing',
            ('paused', 'view_skills'): 'skills_menu',
            ('paused', 'view_map'): 'map_menu',

            # splashes
            ('game_over', 'next'): 'main_menu',
        }
        self.fsm = StateMachine(game=self, initial='main_menu', table=self.state_table)

    def map_menu(self):
        self.ui.draw_map_menu()
        return 'stay'

    def skill_detail(self):
        self.ui.draw_info_skill()
        return 'stay'

    def skills_menu(self):
        self.ui.draw_skills_menu()
        return 'stay'

    def game_over(self):
        # TODO: autotransition after x seconds
        self.ui.draw_game_over()
        return 'stay'

    def main_menu(self):
        self.ui.draw_main_menu()
        return 'stay'

    def playing(self):
        if self.current_music != self.music_action:
            pg.mixer.music.load(self.music_action)
            pg.mixer.music.play(loops=-1)
            self.current_music = self.music_action

        self.update()
        self.draw()
        return 'stay'

    def paused(self):
        self.ui.draw_pause_menu()
        return 'stay'

    def clear_map(self):
        # clean up old sprites, except the current player
        for sprite in self.all_sprites:
            if sprite != self.player:
                sprite.kill()

    @timeit
    def new(self):
        # clean up old sprites
        for sprite in self.all_sprites:
            sprite.kill()

        print('Starting New Game')

        # get a clean ui instance
        self.ui.new()

        # fire up the intro music
        self.current_music = self.music_intro
        pg.mixer.music.load(self.current_music)
        pg.mixer.music.play(loops=-1)

        # self.generate_maptiles()

        # get fresh game elements
        self.worldmap = WorldMap(self)
        self.ui.all_windows.append(self.worldmap)
        self.ui.map_menu_windows = [self.worldmap]
        # for node in self.worldmap.graph.nodes():
        # atts = nx.get_node_attributes(self.worldmap.graph, 'map')
        # print(atts)
        atts = {node: {'map': Map(self, settings.MAP_WIDTH, settings.MAP_HEIGHT)} for node in self.worldmap.graph.nodes()}
        # atts['map'] = Map(self, settings.MAP_WIDTH, settings.MAP_HEIGHT)
        # print(atts)
        nx.set_node_attributes(self.worldmap.graph, atts)
        # print(atts)
        # print(nx.get_node_attributes(self.worldmap.graph, 'map'))
        # print(nx.get_node_attributes(self.worldmap.graph, 'map')[self.worldmap.current_node])
        self.current_map = nx.get_node_attributes(self.worldmap.graph, 'map')[self.worldmap.current_node]
        # self.player_start = self.current_map.player_start

        self.generate_maptiles()

        self.player = self.spawn(Player, self.current_map.player_start)
        self.camera = Camera(self.current_map.width, self.current_map.height)

    def travel(self):
        # TODO: splash screen if travel loading becomes significant
        if self.worldmap.destination_node:
            # update worldmap nodes
            self.worldmap.current_node = self.worldmap.destination_node
            self.worldmap.destination_node = None
            self.worldmap.visit_node(self.worldmap.current_node)
            self.worldmap.discover_node(self.worldmap.current_node, neighbors=True)

            # generate new current map
            self.clear_map()
            self.current_map = self.worldmap.graph.node[self.worldmap.current_node]['map']
            self.generate_maptiles()
            self.player.pos = self.current_map.player_start

            # clear out all the map-specific delayed effects
            self.delayed_events = [event for event in self.delayed_events if not event[2]]

        else:
            # TODO: send the state to a 'choose destination' screen
            print('NO DESTINATION SET')

    def spawn(self, entity, start_pos):
        """
        universal function to spawn a new sprite of any type
        mainly exists to provide a target for debugging hooks
        """
        if self.configs.debug:
            if entity.debugname not in self.configs.debug_exclude:
                print('Spawned {} at {}'.format(entity.debugname, start_pos))
            else:
                self.suppressed_debug_messages += 1

        return entity(self, start_pos)

    def delay_event(self, delay, event, map_specific):
        self.delayed_events.append((pg.time.get_ticks() + delay, event, map_specific))

    def trigger_delayed_events(self):
        for trigger_time, event, map_specific in self.delayed_events:
            if trigger_time <= pg.time.get_ticks():
                event()
        self.delayed_events = [tup for tup in self.delayed_events if tup[0] > pg.time.get_ticks()]

    @timeit
    def generate_maptiles(self):
        """
        loops through self.map.data and spawns walls
        currently, this function also sets the player start position when it finds an empty tile
            - this is kind of an efficiency hack since we're looping through the data anyways,
              but might need to be replaced later to separate functionality or as part of procedural gen
        """
        for x in range(self.current_map.tilewidth):
            for y in range(self.current_map.tileheight):

                if self.current_map.data[x][y] == 1:
                    self.spawn(Wall, (x * settings.TILESIZE, y * settings.TILESIZE))

                elif self.current_map.player_start is None:
                    tile_center_x = x * settings.TILESIZE + settings.TILESIZE / 2
                    tile_center_y = y * settings.TILESIZE + settings.TILESIZE / 2
                    self.current_map.player_start = (int(tile_center_x), int(tile_center_y))

                    if self.configs.debug:
                        print("Player starting coordinates set to: {}".format(self.current_map.player_start))

                else:
                    # distance from player spawn
                    player_dist = calc_dist((x * settings.TILESIZE, y * settings.TILESIZE), self.current_map.player_start)
                    # distance from other clusters
                    cluster_space = not any([calc_dist((x, y), cluster) < settings.cluster_dist for cluster in self.current_map.clusters])
                    if player_dist > settings.safe_spawn_dist and cluster_space:  # random.random() > .9:
                        # self.spawn(Mob, (x * settings.TILESIZE, y * settings.TILESIZE))
                        self.current_map.clusters.append((x, y))

        for cluster in self.current_map.clusters:
            for i in range(settings.pack_size):
                x = (cluster[0] * settings.TILESIZE + i) + (settings.TILESIZE // 2)
                y = (cluster[1] * settings.TILESIZE + i) + (settings.TILESIZE // 2)
                self.spawn(Mob, (x, y))

    def run(self):

        self.new()

        while True:
            self.delta_time = self.clock.tick(self.configs.fps) / 1000
            self.events()
            method = getattr(self, self.fsm.current_state)
            # if self.fsm.current_state not in ['game_over']:
            self.fsm(method())

    def quit(self):
        if settings.SYSTEM_DEBUG:
            print('Suppressed Debug Messages: {}'.format(self.suppressed_debug_messages))
        pg.quit()
        sys.exit()

    def events(self):
        """ Event processing for the game object - handles system controls"""
        for event in pg.event.get():
            # print(event)
            self.ui.start_button.handle_event(event)

            for window in self.ui.all_windows:
                if window.visible:
                    window.process_input(event)

            if self.worldmap.visible:
                self.worldmap.process_input(event)

            if event.type == pg.QUIT:
                self.quit()
            if event.type == pg.KEYDOWN:
                # TODO: mapping structure for keydown binds
                if event.key == pg.K_ESCAPE:
                    self.quit()
                if event.key == pg.K_p:
                    self.fsm('paused')
                # if event.key == pg.K_RETURN:
                #     self.fsm(self.new())
                if event.key == pg.K_F10:
                    self.fullscreen = not self.fullscreen
                    self.screen_update()
                if event.key == pg.K_F12:
                    self.configs.debug = not self.configs.debug
                if event.key == pg.K_F2:
                    volume = pg.mixer.music.get_volume()
                    msg = 'MUSIC MUTED' if volume else 'MUSIC UNMUTED'
                    pg.mixer.music.set_volume(not volume)
                    self.flash_message(msg, 2)
                if event.key == pg.K_9:
                    print(self.player.sum_bonuses())
                if event.key == pg.K_RETURN:
                    self.fsm('next')
                if event.key == pg.K_k:
                    self.fsm('view_skills')
                if event.key == pg.K_F1:
                    self.fsm('info')
                if event.key == pg.K_m:
                    self.fsm('view_map')
                if event.key == pg.K_F9:
                    self.travel()

    def screen_update(self):
        """ Create the display - called on Game init and display settings change"""
        if self.fullscreen:
            screen = pg.display.set_mode(self.screensize, FULLSCREEN)
        else:
            screen = pg.display.set_mode(self.screensize)

        return screen

    def update(self):
        """ update logic for main game loop """
        self.effects_screen.fill((0, 0, 0, 0))

        self.all_sprites.update()
        self.camera.update(target=self.player, hit_rect=True)

        self.trigger_delayed_events()

        # projectiles hit mobs
        hits = pg.sprite.groupcollide(self.mobs, self.projectiles, False, True)
        for hit in hits:
            hit.hp_current -= hits[hit][0].damage

        # mobs hit player
        hits = pg.sprite.spritecollide(self.player, self.mobs, False, Collider.collide_hit_rect)
        for hit in hits:
            self.player.hp_current -= hit.collision_damage
        if hits:
            # if :
            self.player.pos += Vec2(hits[0].collision_knockback, 0).rotate(-hits[0].rot)

        if len(self.mobs) == 0:
            print('All mobs defeated')
            self.travel()

    def draw_grid(self, line_width=1):
        """ draws a grid of lines to display the boundaries of empty tiles """
        for x in range(0, self.current_map.width, settings.TILESIZE):
            start_pos = (x + self.camera.offset[0], 0)
            end_pos = (x + self.camera.offset[0], settings.HEIGHT)
            pg.draw.line(self.screen, colors.lightgrey, start_pos, end_pos, line_width)

        for y in range(0, self.current_map.height, settings.TILESIZE):
            start_pos = (0, y + self.camera.offset[1])
            end_pos = (settings.WIDTH, y + self.camera.offset[1])
            pg.draw.line(self.screen, colors.lightgrey, start_pos, end_pos, line_width)

    def draw(self):
        self.screen.fill(settings.BGCOLOR)

        if self.configs.debug:
            self.draw_grid()

        for sprite in self.all_sprites:
            if isinstance(sprite, Mob):
                sprite.draw_health()
            self.screen.blit(sprite.image, self.camera.apply(sprite))

        # show various object boundaries in debug mode
        if self.configs.debug:
            # player.rect as white box
            pg.draw.rect(self.screen, colors.white, self.camera.apply(self.player), 2)

            # player.hit_rect as green box
            pg.draw.rect(self.screen, colors.green, self.camera.apply(self.player, hit_rect=True), 2)

            # mob rects, hit_rects as white & green boxes
            for mob in self.mobs:
                pg.draw.rect(self.screen, colors.white, self.camera.apply(mob), 2)
                pg.draw.rect(self.screen, colors.green, self.camera.apply(mob, hit_rect=True), 2)

            # white circle around detected mouse position
            pg.draw.circle(self.screen, colors.white, pg.mouse.get_pos(), 10, 1)

        # messing around with isometry
        # new_screen = pg.transform.rotate(self.screen, -45)
        # new_screen = pg.transform.scale(new_screen, (new_screen.get_width(), new_screen.get_height() // 2))
        # self.screen.blit(new_screen, (0, 0))

        # TODO: merge these
        self.hud.update()
        self.hud.draw(self.screen)
        self.ui.draw_hud()

        self.screen.blit(self.effects_screen, (0, 0))

        pg.display.flip()

    def flash_message(self, message, ttl):
        # TODO: add message to debug output
        self.message_flash_queue.put(message, ttl)

    @timeit
    def load_assets(self):
        # TODO: structure for mapping asset variables to filenames

        # folders
        if getattr(sys, 'frozen', False):
            game_folder = path.dirname(sys.executable)
        else:
            game_folder = path.dirname(path.realpath(__file__))
        # game_folder = path.curdir(__file__)
        print(game_folder)
        assets_folder = path.join(game_folder, 'assets')
        fonts_folder = path.join(assets_folder, 'fonts')
        audio_folder = path.join(assets_folder, 'audio')
        music_folder = path.join(audio_folder, 'music')
        images_folder = path.join(assets_folder, 'images')
        player_images_folder = path.join(images_folder, 'player')
        player_audio_folder = path.join(audio_folder, 'player')
        mob_images_folder = path.join(images_folder, 'mob')
        ui_images_folder = path.join(images_folder, 'ui')
        skill_images_folder = path.join(images_folder, 'skill')
        map_images_folder = path.join(images_folder, 'map')

        # fonts
        self.hud_font = path.join(fonts_folder, 'Dense-Regular.ttf')
        self.message_flash_font = path.join(fonts_folder, 'Angerpoise-Lampshade.ttf')
        self.settings_font = path.join(fonts_folder, 'Joystix-Monospace.ttf')

        # spritesheets
        self.player_move_spritesheet = Spritesheet(path.join(player_images_folder, 'player-move.png'))
        self.player_wobble_spritesheet = Spritesheet(path.join(player_images_folder, 'player-wobble.png'))

        # static images
        self.icon = pg.image.load(path.join(images_folder, 'letter_j_icon_small.png'))
        self.worldmap_background = pg.image.load(path.join(map_images_folder, 'newmap.png')).convert_alpha()
        self.mob_zombie_image = pg.image.load(path.join(mob_images_folder, 'zombie1.png'))
        self.bullet_img = pg.image.load(path.join(skill_images_folder, 'bullet.png'))
        self.button_up = pg.image.load(path.join(ui_images_folder, 'up.png'))
        self.button_down = pg.image.load(path.join(ui_images_folder, 'down.png'))
        self.button_hover = pg.image.load(path.join(ui_images_folder, 'hover.png'))

        # sound effects
        self.music_intro = path.join(music_folder, 'soliloquy.mp3')
        self.music_action = path.join(music_folder, 'action.mp3')
        self.player_sound_ow = pg.mixer.Sound(path.join(player_audio_folder, 'ow.wav'))

        # startup values for display/mixer
        pg.display.set_caption(settings.TITLE)
        pg.display.set_icon(self.icon)


if __name__ == '__main__':
    Game(name="Dev Game").run()
