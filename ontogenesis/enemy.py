# -*- coding: utf-8 -*-

from random import randint

import pygame as pg
from pygame.math import Vector2 as Vec2

from helpers import calc_dist
import settings
from settings import layers, colors


class Collider:
    # TODO: merge this into master mobile class
    @staticmethod
    def collide_hit_rect(one, two):
        return one.hit_rect.colliderect(two.rect)

    def collide(self, group, direction):

        if direction == 'x':
            hits = pg.sprite.spritecollide(self, group, False, self.collide_hit_rect)
            if hits:
                if hits[0].rect.centerx > self.hit_rect.centerx:  # sprite was moving to the right prior to collision
                    self.pos.x = hits[0].rect.left - self.hit_rect.width / 2
                if hits[0].rect.centerx < self.hit_rect.centerx:
                    self.pos.x = hits[0].rect.right + self.hit_rect.width / 2
                self.vel.x = 0
                self.hit_rect.centerx = self.pos.x

        if direction == 'y':
            hits = pg.sprite.spritecollide(self, group, False, self.collide_hit_rect)
            if hits:
                if hits[0].rect.centery > self.hit_rect.centery:
                    self.pos.y = hits[0].rect.top - self.hit_rect.height / 2
                if hits[0].rect.centery < self.hit_rect.centery:
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
        self.pos = Vec2(start_pos)
        self.rot = 0
        self.avoid_radius = 100

        # default stats
        self.speed = 80
        self.hp_current = 100
        self.hp_max = 100
        self.hps_regen = 0
        self.collision_damage = 10
        self.collision_knockback = 20
        self.vision_distance = 300

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

    def avoid(self, entity_group, radius):
        """ spreads the mobs out and also effectively causes them to surround the target """
        for entity in entity_group:
            if entity != self:
                dist = self.pos - entity.pos
                if 0 < dist.length() < radius:
                    self.acc += dist.normalize() * 10  # had to play with the 10x factor a bit

    def update(self):
        # health regen/degen
        if self.hps_regen != 0:
            self.hp_current = min(self.hp_current + (self.hps_regen * self.game.delta_time), self.hp_max)

        # face the player if he's close enough to be seen
        player_dist = calc_dist(self.pos, self.game.player.pos)
        if player_dist <= self.vision_distance:
            self.rotate(Vec2(self.game.player.hit_rect.center))
        else:
            self.rot = randint(0, 360)
            self.image = pg.transform.rotate(self.orig_image, self.rot)
        self.acc = Vec2(self.speed, 0).rotate(-self.rot)

        # update image
        # TODO: give these guys some animation
        self.rect = self.image.get_rect(center=self.rect.center)
        self.rect.center = self.pos

        # ajdust angle tp spread out from other mobs
        self.avoid(self.game.mobs, self.avoid_radius)

        # run forwards
        if player_dist <= self.vision_distance:
            self.acc.scale_to_length(self.speed)
            self.acc += self.vel * -1
            self.vel += self.acc * self.game.delta_time
            self.pos += self.vel * self.game.delta_time + 0.5 * self.acc * self.game.delta_time ** 2
        else:
            self.acc.scale_to_length(self.speed * .3)
            self.acc += self.vel * -1
            self.vel += self.acc * self.game.delta_time
            self.pos += self.vel * self.game.delta_time + 0.5 * self.acc * self.game.delta_time ** 2

        # wall collision
        self.hit_rect.centerx = self.pos.x
        self.collide(self.game.walls, 'x')
        self.hit_rect.centery = self.pos.y
        self.collide(self.game.walls, 'y')

        # mouseover highlighting
        if self.rect.collidepoint(pg.mouse.get_pos() - self.game.camera.offset):
            # self.image = self.get_outline
            self.image.blit(self.get_outline(), self.image.get_rect())

        # death conditions check
        if self.hp_current <= 0:
            self.kill()

    def draw_health(self):
        hp_pct = self.hp_current / self.hp_max * 100
        if hp_pct > 60:
            col = colors.green
        elif hp_pct > 30:
            col = colors.yellow
        else:
            col = colors.red
        width = int(self.rect.width * hp_pct / 100)
        healthbar = pg.Rect(0, 0, width, 10)  # settings mob healthbar height?
        if hp_pct < 100:
            pg.draw.rect(self.image, col, healthbar)

    def get_outline(self, color=colors.red, threshold=127):
        """Returns an outlined image of the same size.  The image argument must
        either be a convert surface with a set colorkey, or a convert_alpha
        surface. The color argument is the color which the outline will be drawn.
        In surfaces with alpha, only pixels with an alpha higher than threshold will
        be drawn.  Colorkeyed surfaces will ignore threshold.
        https://github.com/Mekire/pygame-image-outline/blob/master/example.py"""
        # TODO: maybe find a better home for this? (actor superclass?)
        mask = pg.mask.from_surface(self.image, threshold)
        # mask = mask.scale(tuple(int(x * 1.1) for x in mask.get_size()))
        outline_image = pg.Surface(self.image.get_size()).convert_alpha()
        outline_image.fill((0, 0, 0, 0))
        # outline_image.blit(self.image, outline_image.get_rect())
        for point in mask.outline():
            outline_image.set_at(point, color)
        return outline_image

