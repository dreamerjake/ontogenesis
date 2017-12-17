# -*- coding: utf-8 -*-

from random import randint

import pygame as pg
from pygame.math import Vector2 as Vec2

from helpers import get_closest_sprite, calc_dist
from settings import layers


class Skill:
    # base class for the skill mixin system
    stat_attrs = {'passive', 'xp_current'}  # handle 'bonuses' separately

    def __init__(self, game):
        self.game = game
        self.owner = None
        self.bonuses = {}

    def __repr__(self):
        return 'Skill "{}": {}'.format(self.name, self.stats)

    @property
    def stats(self):
        return {attr: getattr(self, attr) for attr in self.stat_attrs if hasattr(self, attr)}

    @property
    def focus_options(self):
        # return self.owner
        return self.owner.game.unlocked_mods.intersection(self.mods)

    def gain_xp(self, xp):
        mult = 1 + (xp * .01)
        if self.passive:
            self.bonuses[self.focus] *= mult
        else:
            setattr(self, self.focus, getattr(self, self.focus) * mult)


class MovingDamageArea(pg.sprite.Sprite):
    def __init__(self, game, owner, image, damage, pos, vel, duration, align='center', moves_with_owner=False):
        self._layer = layers.projectile
        self.groups = game.all_sprites, game.aoe
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.owner = owner
        self.image = image
        self.rect = self.image.get_rect()
        self.pos = Vec2(pos)
        self.rect.center = pos
        self.vel = vel
        self.duration = duration
        self.damage = damage
        self.damage_rate = 2000
        self.spawn_time = pg.time.get_ticks()
        self.moves_with_owner = moves_with_owner
        self.align = align

    def update(self):
        if self.moves_with_owner:
            self.pos += self.owner.vel * self.game.delta_time
        else:
            self.pos += self.vel * self.game.delta_time
        # self.rect.center = self.pos
        setattr(self.rect, self.align, self.pos)
        timed_out = pg.time.get_ticks() - self.spawn_time > self.duration
        if timed_out:
            self.owner.attacking = False
            self.kill()


class Projectile(pg.sprite.Sprite):
    def __init__(self, game, image, damage, pos, vel, duration, kickback):
        self.groups = game.all_sprites, game.projectiles
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = image
        self.rect = self.image.get_rect()
        self.pos = Vec2(pos)
        self.rect.center = pos
        self.vel = vel
        self.duration = duration
        self.kickback = kickback
        self.damage = damage
        self.damage_rate = 2000
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

        # print(midl)
        return midl

    points = get_points(*start_pos, *end_pos)
    pg.draw.lines(surface, (100 + randint(0, 100), 100 + randint(0, 100), 255), True, points)


class PassiveSkill(Skill):
    def __init__(self, game, name, **bonuses):
        super().__init__(game=game)
        self.passive = True
        self.name = name
        self.bonuses = {bonus: value for bonus, value in bonuses.items()}
        self.mods = set(self.bonuses.keys())
        self.focus = None


class MeleeSkill(Skill):
    mods = {'ticks_per_sec', 'tick_damage', 'range'}
    aligns = {
        'up': 'midbottom',
        'down': 'midtop',
        'left': 'midright',
        'right': 'midleft'
    }

    def __init__(self, game, image):
        super().__init__(game=game)
        # basic
        self.image = image
        self.name = 'Melee'
        self.passive = False
        self.xp_current = 0
        self.xp_growth_rate = .1
        self.fire_delay = 600
        # self.kickback = 0

        # state
        self.focus = next(iter(self.mods))
        self.last_fired = 0

        # projectile
        self.proj_damage = 10
        self.proj_speed = 0
        self.proj_duration = 300

    @property
    def rotated_img(self):
        images = {
            'up': pg.transform.flip(self.image, False, False),
            'down': pg.transform.flip(self.image, False, True),
            'left': pg.transform.rotate(self.image, 90),
            'right': pg.transform.rotate(self.image, 270)
        }
        return images[self.owner.facing]

    @property
    def can_fire(self):
        return pg.time.get_ticks() - self.last_fired > self.fire_delay

    def fire(self):
        spawn_point = self.owner.projectile_spawn
        proj_direction = Vec2(1, 0).rotate(-self.owner.rot)
        proj_vel = proj_direction * self.proj_speed
        proj_vel += self.owner.vel  # no need to save

        if self.can_fire:
            MovingDamageArea(
                game=self.game,
                owner=self.owner,
                image=self.rotated_img,
                damage=self.proj_damage,
                pos=spawn_point,
                vel=proj_vel,
                duration=self.proj_duration,
                align=self.aligns[self.owner.facing],
                moves_with_owner=True)
            self.last_fired = pg.time.get_ticks()
            self.owner.attacking = True


class LightningSkill(Skill):

    mods = {'ticks_per_sec', 'tick_damage', 'range'}

    def __init__(self, game):
        super().__init__(game=game)
        # basic
        self.name = 'Lightning'
        self.passive = False
        self.xp_current = 0
        self.xp_growth_rate = .1

        # state
        self.focus = next(iter(self.mods))
        # self.last_tick = pg.time.get_ticks()

        # channeling specific
        self.ticks_per_sec = 2
        self.tick_damage = 10
        self.tick_cost = 5

        # targeting
        self.range = 300

    @property
    def damage(self):
        return self.tick_damage

    @property
    def damage_rate(self):
        return 1000 / self.ticks_per_sec

    @property
    def cost(self):
        return self.tick_cost

    def fire(self):
        if self.owner.resource_current >= self.tick_cost:
            target = get_closest_sprite(self.owner.game.mobs, pg.mouse.get_pos() - self.owner.game.camera.offset, radius=100)
            if target and calc_dist(self.owner.pos, target.pos) < self.range:
                offset = self.owner.game.camera.offset
                to_pos = target.hit_rect.center + offset
                # from_pos = self.owner.pos + self.owner.proj_offset.rotate(-self.owner.rot) + offset
                from_pos = self.owner.projectile_spawn + offset
                draw_lightning(self.owner.game.effects_screen, from_pos, to_pos)
                # now = pg.time.get_ticks()
                # if now - self.last_tick > 1000 // self.ticks_per_sec:
                if target.take_damage(self):
                    self.owner.resource_current -= self.tick_cost
                    print('ZAPPED {} for {}'.format(target, self.tick_damage))
                    # self.last_tick = now
        else:
            print('OOM - cannot use skill {}'.format(self.name))
