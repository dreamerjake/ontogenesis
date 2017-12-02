import pygame as pg

import settings
from settings import layers


class Mob(pg.sprite.Sprite):

    debugname = 'Mob (Zombie Placeholder)'

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
        self.pos = start_pos
        self.rot = 0

        # self.vx, self.vy = 0, 0

        self.x, self.y = start_pos

        # default stats
        self.speed = 100
        self.hp_current = 80
        self.hp_max = 100
        self.hps_regen = 1

        # item management
        self.inventory = []

    def load_images(self):
        self.standing_frames = [self.game.mob_zombie_image]

    def rotate(self, target):
        """
        Turn to face the target

        :param target: pygame.math.Vector2
        :return: None
        """

        self.rot = (target - self.hit_rect.center).angle_to(pg.math.Vector2(1, 0))
        self.image = pg.transform.rotate(self.orig_image, self.rot)
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self):
        if self.hps_regen != 0:
            self.hp_current = min(self.hp_current + (self.hps_regen * self.game.delta_time), self.hp_max)
        # self.process_input()
        self.rotate(pg.math.Vector2(self.game.player.hit_rect.center))
        # self.rect.center = self.x, self.y
        # self.x += self.vx * self.game.delta_time
        # self.y += self.vy * self.game.delta_time
        # self.hit_rect.centerx = self.x
        # self.collide_with_walls('x')
        # self.hit_rect.centery = self.y
        # self.collide_with_walls('y')
        # self.rect.center = self.hit_rect.center
