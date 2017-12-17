# -*- coding: utf-8 -*-

from collections import defaultdict
from random import randint

import pygame as pg
from pygame.math import Vector2 as Vec2

import settings
from helpers import calc_dist
from settings import layers, colors


def draw_text(text, font_name, size, color):
    font = pg.font.Font(font_name, size)
    font.set_bold(True)
    return font.render(text, True, color)
    #text_rect = text_surface.get_rect(**{align: (x, y)})
    #screen.blit(text_surface, text_rect)


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


class FloatingMessage(pg.sprite.Sprite):
    def __init__(self, game, start_pos, image, duration=500):
        self._layer = layers.ui
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)

        self.game = game
        self.image = image
        self.rect = self.image.get_rect(center=start_pos)
        self.duration = duration
        self.created = pg.time.get_ticks()

    def update(self):
        self.rect.centery -= 1
        if pg.time.get_ticks() - self.created > self.duration:
            self.kill()


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

        # state
        self.last_damage = defaultdict(int)

        # default stats
        self.speed = 80
        self.hp_current = 100
        self.hp_max = 100
        self.hps_regen = 0
        self.collision_damage = 10
        self.collision_knockback = 20
        self.vision_distance = 300
        self.xp_value = 10

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

    def take_damage(self, source):
        if pg.time.get_ticks() - self.last_damage[source] > source.damage_rate:
            self.hp_current -= source.damage
            self.last_damage[source] = pg.time.get_ticks()
            FloatingMessage(self.game, self.rect.midtop, draw_text(str(source.damage), self.game.hud_font, 24, colors.white))
            return True
        return False

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
            self.game.player.gain_xp(self.xp_value)
            self.kill()

    def draw_health(self):
        hp_pct = self.hp_current / self.hp_max * 100
        width = int(settings.TILESIZE * hp_pct / 100)
        pos = self.rect.topleft + self.game.camera.offset
        pos.x = (self.rect.centerx - width // 2) + self.game.camera.offset.x
        healthbar = pg.Rect(*pos, width, 8)  # settings mob healthbar height?
        missing = pg.Rect(*pos, settings.TILESIZE, 8)
        if hp_pct < 100:
            pg.draw.rect(self.game.effects_screen, colors.red, missing)
            pg.draw.rect(self.game.effects_screen, colors.green, healthbar)

    # def draw_indicator(self):
    #     # print('drawing damage numbers')
    #     text = '42'
    #     font_name = self.game.hud_font
    #     size = 16
    #     color = colors.white
    #     x, y = self.rect.midtop
    #     draw_text(self.game.effects_screen, text, font_name, size, color, x, y, align='midbottom')

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


class Zombie(Mob):
    debugname = 'Mob (Zombie)'


class GiantLizard(Mob):

    debugname = 'Mob (Giant Lizard)'

    def __init__(self, game, start_pos):
        super().__init__(game, start_pos)

        # stat adjustment relative to zombie
        self.hit_rect = self.hit_rect.inflate(10, 10)
        self.speed *= 1.3
        self.collision_damage *= 1.3
        self.collision_knockback *= 1.3
        self.vision_distance *= .7
        self.xp_value *= 1.3

        self.image = self.game.mob_lizard_image
        self.orig_image = self.image
