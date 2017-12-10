# -*- coding: utf-8 -*-
from random import randint

import pygame as pg
from pygame.math import Vector2 as Vec2


class Skill:
    # base class for the skill mixin system
    display_attrs = ['name', 'passive', 'xp_current']  # handle 'bonuses' separately

    def __init__(self):
        self.bonuses = {}

    @property
    def display(self):
        display = {attr: getattr(self, attr) for attr in self.display_attrs if hasattr(self, attr)}
        return display


class Projectile(pg.sprite.Sprite):
    def __init__(self, game, damage, pos, vel, duration, kickback):
        self.groups = game.all_sprites, game.projectiles
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = self.game.bullet_img
        self.rect = self.image.get_rect()
        self.pos = Vec2(pos)
        self.rect.center = pos
        self.vel = vel
        self.duration = duration
        self.kickback = kickback
        self.damage = damage
        self.spawn_time = pg.time.get_ticks()

    def update(self):
        self.pos += self.vel * self.game.delta_time
        self.rect.center = self.pos
        timed_out = pg.time.get_ticks() - self.spawn_time > self.duration
        hit_wall = pg.sprite.spritecollideany(self, self.game.walls)
        if any([timed_out, hit_wall]):
            self.kill()


def draw_lightning(surface, start_pos, end_pos):
    # print('ZAPPING!')
    min_dist = 10
    max_amp = 5

    def get_points(sx, sy, x, y):
        if abs(sx - x) < min_dist and abs(sy - y) < min_dist:
            return [(sx, sy)]
        midx = (sx + x) / 2 + randint(-max_amp, max_amp)
        midy = (sy + y) / 2 + randint(-max_amp, max_amp)
        upper = get_points(sx, sy, midx, midy)
        lower = get_points(x, y, midx, midy)
        upper.extend(lower)
        midl = [(midx, midy)]
        midl.extend(upper)
        return midl

    points = get_points(*start_pos, *end_pos)
    pg.draw.lines(surface, (100 + randint(0, 100), 100 + randint(0, 100), 255), True, points)


run_skill = Skill()
run_skill.name = 'Run'
run_skill.passive = True
run_skill.bonuses = {'speed': 10}
run_skill.xp_current = 0
run_skill.xp_growth_rate = .1

toughness_skill = Skill()
toughness_skill.name = 'Toughness'
toughness_skill.passive = True
toughness_skill.bonuses = {'hp_max': 10}
toughness_skill.xp_current = 0
toughness_skill.xp_growth_rate = .1
