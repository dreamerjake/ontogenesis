from os import path
import sys

import pygame as pg

from map import CellularAutomata, Wall
from player import Player
from ui import UI
import settings


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

    def __init__(self, name):
        # pygame initialization
        # pg.mixer.pre_init(44100, -16, 4, 2048)
        pg.init()

        self.name = name

        # state machine
        self.fsm = StateMachine(initial='main_menu', table=self.state_table, owner=self)

        # display
        self.screen = pg.display.set_mode((settings.WIDTH, settings.HEIGHT))
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

        # sprite groups
        self.all_sprites = pg.sprite.LayeredUpdates()
        self.walls = pg.sprite.Group()
        self.mobs = pg.sprite.Group()

        # map stuff
        self.map_generator = CellularAutomata()
        self.map = None
        self.player_start = None

        # assets
        self.hud_font = None
        self.player_move_spritesheet = None
        self.load_assets()

    def new(self):
        self.map = self.map_generator.generate_level(settings.MAP_WIDTH, settings.MAP_HEIGHT)
        for x in range(settings.WIDTH // settings.TILESIZE):
            for y in range(settings.HEIGHT // settings.TILESIZE):

                if self.map[x][y] == 1:
                    Wall(self, x, y)

                    if settings.DEBUG:
                        print("Spawned Wall at ({}, {})".format(x, y))

                elif self.player_start is None:
                    tile_center_x = x * settings.TILESIZE + settings.TILESIZE / 2
                    tile_center_y = y * settings.TILESIZE + settings.TILESIZE / 2
                    self.player_start = (tile_center_x, tile_center_y)

                    if settings.DEBUG:
                        print("Player starting coordinates set to: {}".format(self.player_start))

        self.player = Player(self, self.player_start)

        if settings.DEBUG:
            print("Spawned Player at {}".format(self.player_start))

        # self.camera = Camera(self.map.width, self.map.height)

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
                if event.key == pg.K_ESCAPE:
                    self.fsm('quit')
                if event.key == pg.K_p:
                    self.fsm('pause')
                if event.key == pg.K_RETURN:
                    self.fsm('new_game')

    def update(self):
        """update logic for main game loop"""
        self.all_sprites.update()
        # self.camera.update(self.player)

    def draw_grid(self):
        for x in range(0, settings.WIDTH, settings.TILESIZE):
            pg.draw.line(self.screen, settings.LIGHTGREY, (x, 0), (x, settings.HEIGHT))
        for y in range(0, settings.HEIGHT, settings.TILESIZE):
            pg.draw.line(self.screen, settings.LIGHTGREY, (0, y), (settings.WIDTH, y))

    def draw(self):
        self.screen.fill(settings.BGCOLOR)
        if settings.DEBUG:
            self.draw_grid()
        self.all_sprites.draw(self.screen)

        if self.debug:
            pg.draw.rect(self.screen, settings.WHITE, self.player, 2)
            pg.draw.rect(self.screen, settings.GREEN, self.player.hit_rect, 2)

        self.ui.draw()
        pg.display.flip()

    def draw_text(self, text, font_name, size, color, x, y, align="topleft"):
        font = pg.font.Font(font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(**{align: (x, y)})
        self.screen.blit(text_surface, text_rect)

    def load_assets(self):
        game_folder = path.dirname(__file__)
        assets_folder = path.join(game_folder, 'assets')
        fonts_folder = path.join(assets_folder, 'fonts')
        images_folder = path.join(assets_folder, 'images')
        player_images_folder = path.join(images_folder, 'player')

        self.hud_font = path.join(fonts_folder, 'Dense-Regular.ttf')

        self.player_move_spritesheet = Spritesheet(path.join(player_images_folder, 'player-move.png'))
