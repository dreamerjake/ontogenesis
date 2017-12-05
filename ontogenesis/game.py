from os import path
import sys
import time

import pygame as pg
from pygame.locals import FULLSCREEN

from map import Map, Camera, Wall
from player import Player
from enemy import Mob
from ui import UI, Minimap
import settings
from settings import colors
from settings import game_configs as configs


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

    def get_image(self, x, y, width, height, rot=None, scale_to=(64, 64)):
        """ Gets a single image from the spritesheet"""
        image = pg.Surface((width, height), pg.SRCALPHA)
        image.blit(self.spritesheet, (0, 0), (x, y, width, height))
        # image = pg.transform.scale(image, (width // 2, height // 2))
        # image = pg.transform.scale(image, scale_to)
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
        self.sfx_channel = pg.mixer.Channel(0)

        # configs
        self.configs = configs

        # state machine
        self.fsm = StateMachine(initial='main_menu', table=self.state_table, owner=self)

        # display
        self.fullscreen = settings.FULLSCREEN
        self.available_resolutions = pg.display.list_modes()
        self.screensize = (settings.WIDTH, settings.HEIGHT)
        self.screen = self.screen_update()

        # time
        self.clock = pg.time.Clock()
        self.delta_time = None

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
        self.player = None
        self.camera = None

        # map stuff
        self.map = Map(self, settings.MAP_WIDTH, settings.MAP_HEIGHT)
        self.player_start = self.map.player_start

    def new(self):

        self.generate_maptiles()

        self.player = self.spawn(Player, self.player_start)

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

    @timeit
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

                else:
                    # distance from player spawn
                    player_dist = self.map.generator.distance_formula((x, y), self.player_start)
                    cluster_space = not any([self.map.generator.distance_formula((x, y), cluster) < settings.cluster_dist for cluster in self.map.clusters])
                    if player_dist > settings.safe_spawn_dist and cluster_space:  # random.random() > .9:
                        # self.spawn(Mob, (x * settings.TILESIZE, y * settings.TILESIZE))
                        self.map.clusters.append((x, y))

        # print(self.map.clusters)
        for cluster in self.map.clusters:
            for _ in range(settings.pack_size):
                x = (cluster[0] * settings.TILESIZE) + (settings.TILESIZE // 2)
                y = (cluster[1] * settings.TILESIZE) + (settings.TILESIZE // 2)
                self.spawn(Mob, (x, y))

    def run(self):
        state_map = {
            'main_menu': self.ui.draw,
            'playing': self.play,
            'paused': self.ui.draw,
            'quit': self.quit
        }

        self.new()

        pg.mixer.music.play(loops=-1)  # fire up the intro music

        while True:
            self.delta_time = self.clock.tick(self.configs.fps) / 1000
            self.events()
            state_map[self.fsm.current_state]()

    def play(self):
        self.update()
        self.draw()

    def quit(self):
        if settings.SYSTEM_DEBUG:
            print('Suppressed Debug Messages: {}'.format(self.suppressed_debug_messages))
        pg.quit()
        sys.exit()

    def events(self):
        """ Event processing for the game object - handles system controls"""
        for event in pg.event.get():
            self.ui.start_button.handle_event(event)
            if event.type == pg.QUIT:
                self.fsm('quit')
            if event.type == pg.KEYDOWN:
                # TODO: mapping structure for keydown binds
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
                    volume = pg.mixer.music.get_volume()
                    msg = 'MUSIC MUTED' if volume else 'MUSIC UNMUTED'
                    pg.mixer.music.set_volume(not volume)
                    self.flash_message(msg, 2)

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

        hits = pg.sprite.groupcollide(self.mobs, self.projectiles, False, True)
        for hit in hits:
            hit.hp_current -= hits[hit][0].damage

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
            if isinstance(sprite, Mob):
                sprite.draw_health()
            if not isinstance(sprite, Minimap):
                # TODO: generalize this to all UI elements (add a static flag?)
                self.screen.blit(sprite.image, self.camera.apply(sprite))
            else:
                self.screen.blit(sprite.image, sprite.rect)

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

            # circle around detected mouse position
            pg.draw.circle(self.screen, colors.white, pg.mouse.get_pos(), 10, 1)

        self.ui.draw()

        pg.display.flip()

    def flash_message(self, message, ttl):
        # TODO: debug message
        self.message_flash_queue.put(message, ttl)

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
        ui_images_folder = path.join(images_folder, 'ui')
        skill_images_folder = path.join(images_folder, 'skill')

        # fonts
        self.hud_font = path.join(fonts_folder, 'Dense-Regular.ttf')
        self.message_flash_font = path.join(fonts_folder, 'Angerpoise-Lampshade.ttf')
        self.settings_font = path.join(fonts_folder, 'Joystix-Monospace.ttf')

        # spritesheets
        self.player_move_spritesheet = Spritesheet(path.join(player_images_folder, 'player-move.png'))
        self.player_wobble_spritesheet = Spritesheet(path.join(player_images_folder, 'player-wobble.png'))

        # static images
        self.icon = pg.image.load(path.join(images_folder, 'letter_j_icon_small.png'))
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
        pg.mixer.music.load(self.music_intro)
