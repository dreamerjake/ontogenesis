from os import path
import sys
import time

import pygame as pg
from pygame.locals import FULLSCREEN

from map import Map, Camera, Wall
from player import Player
from enemy import Mob
from ui import UI
import settings
from settings import colors
from settings import game_configs as configs


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
        if configs.debug:
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
        pg.mixer.pre_init(44100, -16, 4, 2048)  # frequency, size, channels, buffersize
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

        # debug and logging
        self.suppressed_debug_messages = 0

        # configs
        self.configs = configs

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

        self.generate_maptiles()

        self.player = self.spawn(Player, self.player_start)
        self.test_zombie = self.spawn(Mob, (self.player_start[0] + 300, self.player_start[1]))

        self.camera = Camera(self.map.width, self.map.height)

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

    def generate_maptiles(self):
        """
        loops through self.map.data and spawns walls
        currently, this function also sets the player start position when it finds an empty tile
            - this is kind of an efficiency hack since we're looping through the data anyways,
              but might need to be replaced later to separate functionality or as part of procedural gen
        """
        for x in range(self.map.tilewidth):
            for y in range(self.map.tileheight):

                if self.map.data[x][y] == 1:
                    self.spawn(Wall, (x * settings.TILESIZE, y * settings.TILESIZE))

                elif self.player_start is None:
                    tile_center_x = x * settings.TILESIZE + settings.TILESIZE / 2
                    tile_center_y = y * settings.TILESIZE + settings.TILESIZE / 2
                    self.player_start = (int(tile_center_x), int(tile_center_y))

                    if self.configs.debug:
                        print("Player starting coordinates set to: {}".format(self.player_start))

    def run(self):
        state_map = {
            'main_menu': self.ui.draw,
            'playing': self.play,
            'paused': self.ui.draw,
            'quit': self.quit
        }

        self.new()

        pg.mixer.music.play(loops=-1)

        while True:
            self.delta_time = self.clock.tick(60) / 1000
            self.events()
            state_map[self.fsm.current_state]()

    def play(self):
        self.update()
        self.draw()

    # @staticmethod
    def quit(self):
        if settings.SYSTEM_DEBUG:
            print('Suppressed Debug Messages: {}'.format(self.suppressed_debug_messages))
        pg.quit()
        sys.exit()

    def events(self):
        """ Event processing for the game object - handles system controls"""
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
                if event.key == pg.K_F10:
                    self.fullscreen = not self.fullscreen
                    self.screen_update()
                if event.key == pg.K_F12:
                    self.configs.debug = not self.configs.debug
                if event.key == pg.K_F2:
                    pg.mixer.music.set_volume(0)

    def screen_update(self):
        """ Create the display - called on Game init and display settings change"""
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
            pg.draw.line(self.screen, colors.lightgrey, start_pos, end_pos, line_width)

        for y in range(0, self.map.height, settings.TILESIZE):
            start_pos = (0, y + self.camera.offset[1])
            end_pos = (settings.WIDTH, y + self.camera.offset[1])
            pg.draw.line(self.screen, colors.lightgrey, start_pos, end_pos, line_width)

    def draw(self):
        self.screen.fill(settings.BGCOLOR)

        if self.configs.debug:
            self.draw_grid()

        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, self.camera.apply(sprite))

        # show various object boundaries in debug mode
        if self.configs.debug:
            # player.rect as white box
            pg.draw.rect(self.screen, colors.white, self.camera.apply(self.player), 2)

            # player.hit_rect as green box
            pg.draw.rect(self.screen, colors.green, self.camera.apply(self.player, hit_rect=True), 2)

            # circle around detected mouse position
            pg.draw.circle(self.screen, colors.white, pg.mouse.get_pos(), 10, 1)

        self.ui.draw()

        pg.display.flip()

    @timeit
    def load_assets(self):
        # TODO: structure for mapping asset variables to filenames

        # folders
        game_folder = path.dirname(__file__)
        assets_folder = path.join(game_folder, 'assets')
        fonts_folder = path.join(assets_folder, 'fonts')
        audio_folder = path.join(assets_folder, 'audio')
        music_folder = path.join(audio_folder, 'music')
        images_folder = path.join(assets_folder, 'images')
        player_images_folder = path.join(images_folder, 'player')
        player_audio_folder = path.join(audio_folder, 'player')
        mob_images_folder = path.join(images_folder, 'mob')

        # fonts
        self.hud_font = path.join(fonts_folder, 'Dense-Regular.ttf')

        # spritesheets
        self.player_move_spritesheet = Spritesheet(path.join(player_images_folder, 'player-move.png'))

        # static images
        self.mob_zombie_image = pg.image.load(path.join(mob_images_folder, 'zombie1.png'))

        # sound effects
        pg.mixer.music.load(path.join(music_folder, 'action.mp3'))
        self.player_sound_ow = pg.mixer.Sound(path.join(player_audio_folder, 'ow.wav'))
