# -*- coding: utf-8 -*-

import sys
import time
from gc import get_referrers
from os import path
from random import choice

import networkx as nx
import pygame as pg
from pygame.locals import FULLSCREEN
from pygame.math import Vector2 as Vec2

import settings
from enemy import Mob, Collider
from helpers import calc_dist
from map import Map, WorldMap, Camera, Wall
from player import Player
from settings import colors, game_configs
from ui import UI


class SaveGame:
    pass


class TimeoutQueue:
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
            self._queue.pop(0)

    def get(self):
        self.reap()
        return [item[1] for item in self._queue]


class MessageQueue:
    def __init__(self, max_size):
        self._queue = []
        self.max_size = max_size

    def __bool__(self):
        return len(self._queue) > 0

    def put(self, message):
        self._queue.append(message)
        if len(self._queue) > self.max_size:
            self._queue.pop(0)

    def getall(self):
        return self._queue

    def clear(self):
        self._queue = []


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
    def __init__(self, filename, sprite_size=None):
        self.spritesheet = pg.image.load(filename).convert_alpha()
        if sprite_size:
            self.sprite_width, self.sprite_height = sprite_size

    def get_image(self, x, y, width, height, rot=None, scale_to=None):
        """ Gets a single image from the spritesheet"""
        image = pg.Surface((width, height), pg.SRCALPHA)
        image.blit(self.spritesheet, (0, 0), (x, y, width, height))
        if scale_to:
            image = pg.transform.scale(image, scale_to)
        if rot:
            image = pg.transform.rotate(image, rot)
        return image

    def get_row(self, row, **kwargs):
        images = []
        for i in range(self.spritesheet.get_width() // self.sprite_width):
            image = self.get_image(i * self.sprite_width, row * self.sprite_height, self.sprite_width, self.sprite_height, **kwargs)
            images.append(image)
        return images


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
            print(f'Changing state: {self.current_state} => {next_state}')
            self.current_state = next_state


class Game:
    """ The master Game object"""

    @timeit
    def __init__(self, name):
        self.name = name

        # pygame initialization
        pg.mixer.pre_init(44100, -16, 4, 2048)  # frequency, size, channels, buffersize
        pg.init()
        pg.mixer.music.set_volume(0)
        self.sfx_channel = pg.mixer.Channel(0)

        # configs
        self.configs = game_configs

        # display
        self.fullscreen = settings.FULLSCREEN
        self.available_resolutions = pg.display.list_modes()
        self.screensize = (settings.WIDTH, settings.HEIGHT)
        self.screen = self.screen_update()
        self.effects_screen = self.screen.copy().convert_alpha()
        self.light_filter = pg.Surface(self.screen.get_size())
        self.light_filter.fill(colors.black)
        self.current_music = None

        # time
        self.clock = pg.time.Clock()
        self.delta_time = None
        self.delayed_events = []
        self.active_skills = []

        # messages, debug, and logging
        self.suppressed_debug_messages = 0
        self.message_flash_queue = TimeoutQueue(self.configs.flash_messages_queuesize)
        self.message_queue = MessageQueue(max_size=self.configs.messages_queuesize)

        # assets
        self.hud_font = None
        self.message_flash_font = None
        self.settings_font = None
        self.player_move_spritesheet = None
        self.load_assets()

        # sprite groups
        self.all_sprites = pg.sprite.LayeredUpdates()
        self.hud = pg.sprite.Group()
        self.walls = pg.sprite.Group()
        self.mobs = pg.sprite.Group()
        self.projectiles = pg.sprite.Group()
        self.aoe = pg.sprite.Group()

        # components
        self.ui = UI(self)
        self.worldmap = None
        self.player = None
        self.camera = None

        # save
        self.save = None
        self.unlocked_mods = {'speed', 'range', 'duration', 'ticks_per_sec', 'rps_regen', 'targets'}

        # map stuff
        self.current_map = None
        # self.player_start = self.map.player_start

        # state machine
        self.state_table = {
            # menus
            ('main_menu', 'new_game'): 'create_char',
            ('main_menu', 'next'): 'create_char',

            ('create_char', 'next'): 'select_focus',
            ('create_char', 'back'): 'main_menu',

            # mandatory choices
            ('select_focus', 'next'): 'intro',
            ('select_destination', 'next'): 'playing',

            # in-game menus
            ('skills_menu', 'next'): 'playing',
            ('skills_menu', 'view_skills'): 'playing',
            ('skills_menu', 'paused'): 'paused',
            ('skills_menu', 'info'): 'skill_detail',
            ('skills_menu', 'view_map'): 'map_menu',

            ('skill_detail', 'view_skills'): 'skills_menu',
            ('skill_detail', 'view_map'): 'map_menu',
            ('skill_detail', 'back'): 'skills_menu',  # universal back button?

            ('controls_menu', 'next'): 'playing',
            ('controls_menu', 'view_controls'): 'playing',

            ('map_menu', 'paused'): 'paused',
            ('map_menu', 'view_skills'): 'skills_menu',
            ('map_menu', 'view_map'): 'playing',
            ('map_menu', 'next'): 'playing',
            ('map_menu', 'reach_goal'): 'goal',

            # gameplay
            ('playing', 'paused'): 'paused',
            ('playing', 'die'): 'game_over',
            ('playing', 'view_skills'): 'skills_menu',
            ('playing', 'view_map'): 'map_menu',
            ('playing', 'view_controls'): 'controls_menu',
            ('playing', 'reach_goal'): 'goal',
            ('playing', 'select_destination'): 'select_destination',

            ('paused', 'paused'): 'playing',
            ('paused', 'view_skills'): 'skills_menu',
            ('paused', 'view_map'): 'map_menu',

            # splashes
            ('goal', 'next'): 'main_menu',
            ('game_over', 'next'): 'main_menu',
            ('intro', 'next'): 'controls_menu',
        }
        self.fsm = StateMachine(game=self, initial='main_menu', table=self.state_table)

    @property
    def mouse_pos(self):
        return Vec2(pg.mouse.get_pos()) - self.camera.offset

    def intro(self):
        with open(self.intro_text) as f:
            lines = [line.strip() for line in f]
        self.ui.draw_placeholder_splash('THE INTRO', text=lines)

    def controls_menu(self):
        self.ui.draw_controls_menu()

    def map_menu(self):
        self.ui.draw_map_menu()

    def skill_detail(self):
        self.ui.draw_info_skill()

    def skills_menu(self):
        self.ui.draw_skills_menu()

    def goal(self):
        self.ui.draw_placeholder_splash('GOAL REACHED')

    def game_over(self):
        # TODO: autotransition after x seconds
        self.ui.draw_game_over()

    def main_menu(self):
        self.ui.draw_main_menu()

    def select_focus(self):
        self.ui.draw_skills_menu()

    def select_destination(self):
        self.ui.draw_map_menu()

    def create_char(self):
        if not self.player or self.player.dead:
            self.new()
        self.ui.draw_placeholder_menu('CHARACTER CREATION')

    def playing(self):
        if self.current_music != self.music_action:
            pg.mixer.music.load(self.music_action)
            pg.mixer.music.play(loops=-1)
            self.current_music = self.music_action

        self.update()
        self.draw()

    def paused(self):
        self.ui.draw_pause_menu()

    def clear_map(self):
        # clean up old sprites, except the current player
        for sprite in self.all_sprites:
            if sprite != self.player:
                sprite.kill()

    def check_player_refs(self):
        if self.player:
            referrers = get_referrers(self.player)
            print('Player exists with {} references'.format(sys.getrefcount(self.player)))
            for referrer in referrers:
                print(referrer)
                if hasattr(referrer, '__name__'):
                    print(referrer.__name__)
                elif hasattr(referrer, '__qualname__'):
                    print(referrer.__qualname__)
                else:
                    print(type(referrer))

    @timeit
    def new(self):
        self.ui.draw_placeholder_splash("LOADING SCREEN")
        pg.display.flip()

        # clean up old sprites
        # self.check_player_refs()
        for sprite in self.all_sprites:
            sprite.kill()
        # self.check_player_refs()

        # reset stuff
        self.all_sprites = pg.sprite.LayeredUpdates()
        self.hud = pg.sprite.Group()
        self.walls = pg.sprite.Group()
        self.mobs = pg.sprite.Group()
        self.projectiles = pg.sprite.Group()
        self.aoe = pg.sprite.Group()
        self.worldmap = None
        self.camera = None
        self.delayed_events = []
        self.message_queue.clear()

        # self.check_player_refs()
        if self.player:
            self.player.unequip_all()
        # self.check_player_refs()
        self.player = None

        print('Starting New Game')

        # get a clean ui instance
        self.ui = UI(self)

        # fire up the intro music
        self.current_music = self.music_intro
        pg.mixer.music.load(self.current_music)
        pg.mixer.music.play(loops=-1)

        # self.generate_maptiles()

        # get fresh game elements
        self.worldmap = WorldMap(self)
        # TODO: build a groups param into the WorldMap class
        self.ui.all_windows.add(self.worldmap)
        self.ui.map_menu_windows.add(self.worldmap)
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

        self.ui.create_elements()

    def travel(self):
        # TODO: splash screen if travel loading becomes significant
        if self.worldmap.destination_node:
            if self.worldmap.graph.node[self.worldmap.destination_node]['goal']:
                self.fsm('reach_goal')
                return
            # generate new current map
            self.clear_map()
            self.current_map = self.worldmap.graph.node[self.worldmap.current_node]['map']
            self.generate_maptiles()
            self.player.pos = self.current_map.player_start

            # update worldmap nodes
            self.worldmap.current_node = self.worldmap.destination_node
            self.worldmap.destination_node = None
            self.worldmap.visit_node(self.worldmap.current_node)
            self.worldmap.discover_node(self.worldmap.current_node, neighbors=True)

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
        mob_types = [self.worldmap.graph.node[self.worldmap.current_node]['mobtype']]

        if self.worldmap.destination_node:
            mob_types += [self.worldmap.graph.node[self.worldmap.destination_node]['mobtype']]

        for x in range(self.current_map.tilewidth):
            for y in range(self.current_map.tileheight):

                if self.current_map.data[x][y] == 1:
                    self.spawn(Wall, (x * settings.TILESIZE, y * settings.TILESIZE))

                elif self.current_map.player_start is None:
                    tile_center_x = x * settings.TILESIZE + settings.TILESIZE / 2
                    tile_center_y = y * settings.TILESIZE + settings.TILESIZE / 2
                    self.current_map.player_start = Vec2(int(tile_center_x), int(tile_center_y))

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
                self.spawn(choice(mob_types), (x, y))

    def run(self):

        self.new()

        while True:
            if self.configs.fps:
                self.delta_time = self.clock.tick(self.configs.fps) / 1000
            else:
                self.delta_time = self.clock.tick() / 1000
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
            # self.ui.start_button.handle_event(event)
            for button in self.ui.all_buttons:
                if button.visible:
                    button.handle_event(event)

            for window in self.ui.all_windows:
                if window.visible:
                    window.handle_event(event)

            if self.worldmap.visible:
                self.worldmap.handle_event(event)

            if event.type == pg.QUIT:
                self.quit()
            if event.type == pg.KEYDOWN:
                # TODO: mapping structure for keydown binds
                # if event.key == pg.K_ESCAPE:
                #     self.quit()
                if event.key == pg.K_p:
                    self.fsm('paused')
                # if event.key == pg.K_RETURN:
                #     self.fsm(self.new())
                if event.key == pg.K_c:
                    self.fsm('view_controls')
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
                if event.key == pg.K_0:
                    self.mobs.empty()
                if event.key == pg.K_8:
                    print(f'Total Experience Gained: {self.player.xp_total}')
                if event.key == pg.K_RETURN:
                    if self.fsm.current_state == 'select_destination' and not self.worldmap.destination_node:
                        # force the player to pick a destination
                        self.flash_message('SELECT A DESTINATION', 1)
                    elif self.fsm.current_state == 'select_focus' and self.player and not self.player.focus_skill:
                        # force the player to pick a focus skill
                        self.flash_message('SELECT A FOCUS SKILL', 1)
                    elif self.fsm.current_state == 'select_focus' and self.player and not self.player.focus_skill.focus:
                        # force the player to pick a focus skill modifier
                        self.flash_message('SELECT A FOCUS SKILL MODIFIER', 1)
                    else:
                        self.fsm('next')
                if event.key == pg.K_k:
                    self.fsm('view_skills')
                if event.key == pg.K_F1:
                    self.fsm('info')
                if event.key == pg.K_m:
                    self.fsm('view_map')
                if event.key == pg.K_F9:
                    self.travel()
                if event.key == pg.K_F8:
                    self.configs.fps = 0 if self.configs.fps else 60
                    msg = 'MAX FPS SET TO 60' if self.configs.fps else 'MAX FPS REMOVED'
                    self.flash_message(msg, 1)

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
        for skill in self.active_skills:
            skill.update()

        # projectiles hit mobs
        hits = pg.sprite.groupcollide(self.mobs, self.projectiles, False, True)
        for hit in hits:
            hit.take_damage(hits[hit][0])
            # hit.hp_current -= hits[hit][0].damage

        # mobs take area damage
        hits = pg.sprite.groupcollide(self.mobs, self.aoe, False, False)
        for hit in hits:
            hit.take_damage(hits[hit][0])
            # hit.hp_current -= hits[hit][0].damage

        # mobs hit player
        hits = pg.sprite.spritecollide(self.player, self.mobs, False, Collider.collide_hit_rect)
        for hit in hits:
            # self.player.hp_current -= hit.collision_damage
            self.player.take_damage(hits[0])
        if hits:
            # if :
            self.player.pos += Vec2(hits[0].collision_knockback, 0).rotate(-hits[0].rot)

        if len(self.mobs) == 0:
            print('All mobs defeated')
            self.flash_message('All Mobs Defeated', 3)
            if not self.worldmap.destination_node:
                self.fsm('select_destination')
            else:
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

    def render_light(self):
        self.light_filter.fill(colors.black)
        self.light_rect.center = self.camera.apply(self.player).center
        self.light_filter.blit(self.light_image, self.light_rect)
        self.screen.blit(self.light_filter, (0, 0), special_flags=pg.BLEND_MULT)

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

        self.screen.blit(self.effects_screen, (0, 0))

        if not self.configs.debug:
            self.render_light()

        # TODO: merge these
        self.hud.update()
        # self.hud.draw(self.screen)
        for hud_sprite in self.hud:
            hud_sprite.draw(self.screen)
        self.ui.draw_hud()

        pg.display.flip()

    def message(self, message, color=colors.white):
        self.message_queue.put((message, color))

    def flash_message(self, message, ttl):
        # TODO: add message to debug output
        self.message_flash_queue.put(message, ttl)

    def save(self):
        new_save = SaveGame()
        self.save = new_save

    def load(self, save):
        self.save = save

    @timeit
    def load_assets(self):
        # TODO: structure for mapping asset variables to filenames

        # folders
        if getattr(sys, 'frozen', False):
            self.game_folder = path.dirname(sys.executable)
        else:
            self.game_folder = path.dirname(path.realpath(__file__))
        assets_folder = path.join(self.game_folder, 'assets')
        fonts_folder = path.join(assets_folder, 'fonts')
        audio_folder = path.join(assets_folder, 'audio')
        music_folder = path.join(audio_folder, 'music')
        images_folder = path.join(assets_folder, 'images')
        player_images_folder = path.join(images_folder, 'player')
        player_audio_folder = path.join(audio_folder, 'player')
        ui_audio_folder = path.join(audio_folder, 'ui')
        mob_images_folder = path.join(images_folder, 'mob')
        ui_images_folder = path.join(images_folder, 'ui')
        skill_images_folder = path.join(images_folder, 'skill')
        map_images_folder = path.join(images_folder, 'map')
        placeholder_images_folder = path.join(images_folder, 'placeholder')
        text_folder = path.join(assets_folder, 'text')

        # fonts
        self.hud_font = path.join(fonts_folder, 'Dense-Regular.ttf')
        self.card_font = path.join(fonts_folder, 'Dense-Regular.ttf')
        self.message_flash_font = path.join(fonts_folder, 'Angerpoise-Lampshade.ttf')
        self.settings_font = path.join(fonts_folder, 'Joystix-Monospace.ttf')

        # spritesheets
        self.player_move_spritesheet = Spritesheet(path.join(player_images_folder, 'player-move.png'))
        self.player_wobble_spritesheet = Spritesheet(path.join(player_images_folder, 'player-wobble.png'))
        self.robot_spritesheet = Spritesheet(path.join(placeholder_images_folder, 'celarobotkanova.png'), sprite_size=(120, 180))
        self.eightdir_spritesheet = Spritesheet(path.join(placeholder_images_folder, '8dirguy.png'), sprite_size=(61, 121))

        # static images
        self.icon = pg.image.load(path.join(images_folder, 'letter_j_icon_small.png'))
        self.worldmap_background = pg.image.load(path.join(map_images_folder, 'newmap.png')).convert_alpha()
        self.light_image = pg.transform.scale2x(pg.image.load(path.join(images_folder, 'light_med.png')).convert_alpha())
        # self.light_image = pg.transform.scale(self.light_image, ___)
        self.light_rect = self.light_image.get_rect()
        self.mob_zombie_image = pg.image.load(path.join(mob_images_folder, 'zombie1.png'))
        self.mob_lizard_image = pg.transform.scale(pg.image.load(path.join(mob_images_folder, 'lizard.png')).convert_alpha(), (64, 64))
        self.bullet_img = pg.image.load(path.join(skill_images_folder, 'bullet.png'))
        self.sword_img = pg.transform.scale(pg.image.load(path.join(placeholder_images_folder, 'sword_0.png')).convert_alpha(), (48, 48))
        self.button_up = pg.image.load(path.join(ui_images_folder, 'up.png'))
        self.button_down = pg.image.load(path.join(ui_images_folder, 'down.png'))
        self.button_hover = pg.image.load(path.join(ui_images_folder, 'hover.png'))

        icon_size = self.configs.icon_size
        self.lightning_icon = pg.transform.scale(pg.image.load(path.join(skill_images_folder, 'lightning_icon.png')), (icon_size, icon_size)).convert_alpha()
        self.dash_icon = pg.transform.scale(pg.image.load(path.join(skill_images_folder, 'dash_icon.png')), (icon_size, icon_size)).convert_alpha()
        self.toughness_icon = pg.transform.scale(pg.image.load(path.join(skill_images_folder, 'toughness_icon.png')), (icon_size, icon_size)).convert_alpha()
        self.meditation_icon = pg.transform.scale(pg.image.load(path.join(skill_images_folder, 'meditation_icon.png')), (icon_size, icon_size)).convert_alpha()
        self.melee_icon = pg.transform.scale(pg.image.load(path.join(skill_images_folder, 'melee_icon.png')), (icon_size, icon_size)).convert_alpha()

        globe_size = 160
        self.mana_full_img = pg.transform.scale(pg.image.load(path.join(ui_images_folder, 'mana_full.png')), (globe_size, globe_size)).convert_alpha()
        self.mana_empty_img = pg.transform.scale(pg.image.load(path.join(ui_images_folder, 'mana_empty.png')), (globe_size, globe_size)).convert_alpha()
        self.mana_full_blink_img = pg.transform.scale(pg.image.load(path.join(ui_images_folder, 'mana_full_blink.png')), (globe_size, globe_size)).convert_alpha()
        self.mana_empty_blink_img = pg.transform.scale(pg.image.load(path.join(ui_images_folder, 'mana_empty_blink.png')), (globe_size, globe_size)).convert_alpha()

        # sound effects
        self.music_intro = path.join(music_folder, 'soliloquy.mp3')
        self.music_action = path.join(music_folder, 'action.mp3')
        self.player_sound_ow = pg.mixer.Sound(path.join(player_audio_folder, 'ow.wav'))
        self.button_sound = pg.mixer.Sound(path.join(ui_audio_folder, 'button.wav'))

        # text
        self.intro_text = path.join(text_folder, 'intro_scene.txt')

        # startup values for display/mixer
        pg.display.set_caption(settings.TITLE)
        pg.display.set_icon(self.icon)


if __name__ == '__main__':
    Game(name="Dev Game").run()
