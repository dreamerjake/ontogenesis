# -*- coding: utf-8 -*-
from random import randint

import pygame as pg
from pygame.math import Vector2 as Vec2

from helpers import get_closest_sprite, calc_dist


class Skill:
    # base class for the skill mixin system
    stat_attrs = {'passive', 'xp_current'}  # handle 'bonuses' separately

    def __init__(self):
        self.owner = None
        self.bonuses = {}

    def __repr__(self):
        return 'Skill "{}": {}'.format(self.name, self.stats)

    @property
    def stats(self):
        return {attr: getattr(self, attr) for attr in self.stat_attrs if hasattr(self, attr)}

    def gain_xp(self, xp):
        mult = 1 + (xp * .01)
        if self.passive:
            self.bonuses[self.focus] *= mult
        else:
            setattr(self, self.focus, getattr(self, self.focus) * mult)


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
    min_dist = 10
    max_amp = 5

    def get_points(sx, sy, x, y):
        # min distance check
        if abs(sx - x) < min_dist and abs(sy - y) < min_dist:
            return [(sx, sy)]

        # halfway point calculations
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


class PassiveSkill(Skill):
    def __init__(self):
        super().__init__()
        self.passive = True


class LightningSkill(Skill):

    mods = {'ticks_per_sec', 'tick_damage', 'range'}

    def __init__(self):
        super().__init__()
        # basic
        self.name = 'Lightning'
        self.passive = False
        self.xp_current = 0
        self.xp_growth_rate = .1

        # state
        self.focus = next(iter(self.mods))
        self.last_tick = pg.time.get_ticks()

        # channeling specific
        self.ticks_per_sec = 2
        self.tick_damage = 10
        self.tick_cost = 5

        # targeting
        self.range = 300

    def fire(self):
        if self.owner.resource_current >= self.tick_cost:
            target = get_closest_sprite(self.owner.game.mobs, pg.mouse.get_pos() - self.owner.game.camera.offset, radius=100)
            if target and calc_dist(self.owner.pos, target.pos) < self.range:
                target_pos = target.hit_rect.center
                draw_lightning(self.owner.game.effects_screen, self.owner.pos + self.owner.proj_offset.rotate(-self.owner.rot), target_pos)
                now = pg.time.get_ticks()
                if now - self.last_tick > 1000 // self.ticks_per_sec:
                    target.hp_current -= self.tick_damage
                    self.owner.resource_current -= self.tick_cost
                    print('ZAPPED {} for {}'.format(target, self.tick_damage))
                    self.last_tick = now
        else:
            print('OOM - cannot use skill {}'.format(self.name))


lightning_skill = LightningSkill()


run_skill = PassiveSkill()
run_skill.name = 'Run'
run_skill.bonuses = {'speed': 10}
run_skill.focus = 'speed'
# run_skill.xp_current = 0
# run_skill.xp_growth_rate = .1

toughness_skill = PassiveSkill()
toughness_skill.name = 'Toughness'
toughness_skill.bonuses = {'hp_max': 10}
toughness_skill.focus = 'hp_max'
# toughness_skill.xp_current = 0
# toughness_skill.xp_growth_rate = .1
