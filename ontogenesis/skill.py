# -*- coding: utf-8 -*-

import pygame as pg
from pygame.math import Vector2 as Vec2


class Skill:
    # base class for the skill mixin system
    display_attrs = ['name', 'passive', 'xp_current']  # handle 'bonuses' separately

    @property
    def display_attrs(self):
        display = {attr: getattr(self, attr) for attr in self.display_attrs if hasattr(self, attr)}
        return display


class Projectile(pg.sprite.Sprite):
    def __init__(self, game, damage, pos, speed, direction, duration, kickback):
        self.groups = game.all_sprites, game.projectiles
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = self.game.bullet_img
        self.rect = self.image.get_rect()
        self.pos = Vec2(pos)
        self.rect.center = pos
        self.vel = direction * speed
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
print(toughness_skill.display_attrs)