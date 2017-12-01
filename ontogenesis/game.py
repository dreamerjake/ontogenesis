from os import path
import sys
import time

import pygame as pg
from pygame.locals import FULLSCREEN

from map import Map, Camera
from player import Player
from ui import UI
import settings


# debug timings decorator
def timeit(method):
    def timed(*args, **kwargs):
        if not settings.DEBUG:
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

    def get_image(self, x, y, width, height):
        """ Gets a single image from the spritesheet"""
        image = pg.Surface((width, height), pg.SRCALPHA)
        image.blit(self.spritesheet, (0, 0), (x, y, width, height))
        image = pg.transform.scale(image, (width // 2, height // 2))
        return image


class StateMachine:
    """
    A very simple FSM class.
    adapted from https://news.ycombinator.com/item?id=14634947

    Params:
        initial: Initial state
        table: A dict (current, event) -> target
    """

    def __init__(self, initial, table, owner):
        self.current_state = initial
        self.state_table = table
        self.owner = owner

    def __call__(self, event):
        """Trigger one state transition."""
        next_state = self.state_table.get((self.current_state, event), self.current_state)
        changed = self.current_state != next_state
        if settings.DEBUG:
            debug_msg = "{} | State change event: {} - current state: {} - next state: {} (Changed={})"
            print(debug_msg.format(self.owner.name, event, self.current_state, next_state, changed))
        if changed:
            self.current_state = next_state


class Game:
    """ The master Game object"""

    state_table = {
        ('main_menu', 'new_game'): 'playing',
        ('main_menu', 'quit'): 'quit',

        ('playing', 'quit'): 'quit',
        ('playing', 'pause'): 'paused',

        ('paused', 'pause'): 'playing',
        ('paused', 'quit'): 'quit',
    }

    @timeit
    def __init__(self, name):
        self.name = name

        # pygame initialization
        # pg.mixer.pre_init(44100, -16, 4, 2048)
        pg.init()

        # state machine
        self.fsm = StateMachine(initial='main_menu', table=self.state_table, owner=self)

        # display
        self.fullscreen = settings.FULLSCREEN
        self.available_resolutions = pg.display.list_modes()
        self.screensize = (settings.WIDTH, settings.HEIGHT)
        self.screen = self.screen_update()
        pg.display.set_caption(settings.TITLE)

        # time
        self.clock = pg.time.Clock()
        self.delta_time = None

        # configs
        self.debug = settings.DEBUG
        self.show_fps = settings.SHOW_FPS

        # components
        self.ui = UI(self)
        self.player = None
        self.camera = None

        # sprite groups
        self.all_sprites = pg.sprite.LayeredUpdates()
        self.walls = pg.sprite.Group()
        self.mobs = pg.sprite.Group()

        # map stuff
        self.map = Map(self, settings.MAP_WIDTH, settings.MAP_HEIGHT)
        self.player_start = self.map.player_start

        # assets
        self.hud_font = None
        self.player_move_spritesheet = None
        self.load_assets()

    def new(self):
        # we've generated a map object in the init method, so no need to create one now

        self.player = Player(self, self.player_start)
        if self.debug:
            print("Spawned Player at {}".format(self.player_start))

        self.camera = Camera(self.map.width, self.map.height)

    def run(self):
        state_map = {
            'main_menu': self.ui.draw,
            'playing': self.play,
            'paused': self.ui.draw,
            'quit': self.quit
        }

        self.new()

        while True:
            self.delta_time = self.clock.tick(60) / 1000
            self.events()
            state_map[self.fsm.current_state]()

    def play(self):
        self.update()
        self.draw()

    @staticmethod
    def quit():
        pg.quit()
        sys.exit()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.fsm('quit')
            if event.type == pg.KEYDOWN:
                # system controls
                if event.key == pg.K_ESCAPE:
                    self.fsm('quit')
                if event.key == pg.K_p:
                    self.fsm('pause')
                if event.key == pg.K_RETURN:
                    self.fsm('new_game')
                if event.key == pg.K_F10:
                    self.fullscreen = not self.fullscreen
                    self.screen_update()
                if event.key == pg.K_F12:
                    self.debug = not self.debug

    def screen_update(self):
        if self.fullscreen:
            screen = pg.display.set_mode(self.screensize, FULLSCREEN)
        else:
            screen = pg.display.set_mode(self.screensize)
        return screen

    def update(self):
        """ update logic for main game loop """
        self.all_sprites.update()
        self.camera.update(target=self.player, hit_rect=True)

    def draw_grid(self, line_width=1):
        """ draws a grid of lines to display the boundaries of empty tiles """
        for x in range(0, self.map.width, settings.TILESIZE):
            start_pos = (x + self.camera.offset[0], 0)
            end_pos = (x + self.camera.offset[0], settings.HEIGHT)
            pg.draw.line(self.screen, settings.LIGHTGREY, start_pos, end_pos, line_width)

        for y in range(0, self.map.height, settings.TILESIZE):
            start_pos = (0, y + self.camera.offset[1])
            end_pos = (settings.WIDTH, y + self.camera.offset[1])
            pg.draw.line(self.screen, settings.LIGHTGREY, start_pos, end_pos, line_width)

    def draw(self):
        self.screen.fill(settings.BGCOLOR)

        if self.debug:
            self.draw_grid()

        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, self.camera.apply(sprite))

        if self.debug:
            pg.draw.rect(self.screen, settings.WHITE, self.camera.apply(self.player), 2)
            pg.draw.rect(self.screen, settings.GREEN, self.camera.apply(self.player, hit_rect=True), 2)

        self.ui.draw()

        # pg.draw.circle(self.screen, settings.WHITE, pg.mouse.get_pos(), 10, 1)

        pg.display.flip()

    @timeit
    def load_assets(self):
        game_folder = path.dirname(__file__)
        assets_folder = path.join(game_folder, 'assets')
        fonts_folder = path.join(assets_folder, 'fonts')
        images_folder = path.join(assets_folder, 'images')
        player_images_folder = path.join(images_folder, 'player')

        self.hud_font = path.join(fonts_folder, 'Dense-Regular.ttf')

        self.player_move_spritesheet = Spritesheet(path.join(player_images_folder, 'player-move.png'))
