import pygame as pg
from pygame.math import Vector2 as Vec2

import settings
from settings import layers


class Collider:
    # TODO: merge this into master mobile class
    @staticmethod
    def collide_hit_rect(one, two):
        return one.hit_rect.colliderect(two.rect)

    def collide(self, group, direction):

        if direction == 'x':
            hits = pg.sprite.spritecollide(self, group, False, self.collide_hit_rect)
            if hits:
                if self.vel.x > 0:  # sprite was moving to the right prior to collision
                    self.pos.x = hits[0].rect.left - self.hit_rect.width / 2
                if self.vel.x < 0:
                    self.pos.x = hits[0].rect.right + self.hit_rect.width / 2
                self.vel.x = 0
                self.hit_rect.centerx = self.pos.x

        if direction == 'y':
            hits = pg.sprite.spritecollide(self, group, False, self.collide_hit_rect)
            if hits:
                if self.vel.y > 0:
                    self.pos.y = hits[0].rect.top - self.hit_rect.height / 2
                if self.vel.y < 0:
                    self.pos.y = hits[0].rect.bottom + self.hit_rect.height / 2
                self.vel.y = 0
                self.hit_rect.centery = self.pos.y


class Mob(pg.sprite.Sprite, Collider):

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
        self.vel = Vec2(0, 0)
        self.acc = Vec2(0, 0)
        self.pos = start_pos
        self.rot = 0

        # default stats
        self.speed = 80
        self.hp_current = 80
        self.hp_max = 100
        self.hps_regen = 0

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

        self.rot = (target - self.hit_rect.center).angle_to(Vec2(1, 0))
        self.image = pg.transform.rotate(self.orig_image, self.rot)

    def update(self):
        if self.hps_regen != 0:
            self.hp_current = min(self.hp_current + (self.hps_regen * self.game.delta_time), self.hp_max)
        self.rotate(Vec2(self.game.player.hit_rect.center))
        self.rect = self.image.get_rect(center=self.rect.center)
        self.rect.center = self.pos
        self.acc = Vec2(self.speed, 0).rotate(-self.rot)
        self.acc += self.vel * -1
        self.vel += self.acc * self.game.delta_time
        self.pos += self.vel * self.game.delta_time + 0.5 * self.acc * self.game.delta_time ** 2

        self.hit_rect.centerx = self.pos.x
        self.collide(self.game.walls, 'x')
        self.hit_rect.centery = self.pos.y
        self.collide(self.game.walls, 'y')