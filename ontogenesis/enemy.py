import pygame as pg

import settings
from settings import layers


class Mob(pg.sprite.Sprite):

    debugname = "Mob Zombie Placeholder"

    def __init__(self, game, start_pos):
        # pygame sprite stuff
        self._layer = layers.mob
        self.groups = game.all_sprites, game.mobs
        pg.sprite.Sprite.__init__(self, self.groups)

        # object references
        self.game = game

        # assets
        self.standing_frames = None
        self.load_images()

        # graphics
        self.image = self.standing_frames[0]
        self.orig_image = self.image

        # physics
        self.rect = self.image.get_rect(center=start_pos)
        self.hit_rect = pg.Rect(0, 0, settings.TILESIZE - 5, settings.TILESIZE - 5)
        self.hit_rect.center = self.rect.center
        self.vx, self.vy = 0, 0
        self.x, self.y = start_pos

        # default stats
        self.speed = 100
        self.hp_current = 80
        self.hp_max = 100
        self.regen = 1  # hp per second

    def load_images(self):
        self.standing_frames = [self.game.mob_zombie_image]