# -*- coding: utf-8 -*-

from itertools import cycle
from random import randint

import pygame as pg
from pygame.math import Vector2 as Vec2
from pygame.locals import SRCALPHA

import settings
from helpers import get_closest_sprite, calc_dist, get_font_height
from settings import layers, colors


class Skill:
    # base class for the skill mixin system
    stat_attrs = set()  # handle 'bonuses' separately

    def __init__(self, game):
        self.game = game
        self.owner = None
        self.bonuses = {}
        self.focus = None
        self.focus_options = None
        self.focus_options_cycle = None

    def __repr__(self):
        return 'Skill "{}": {}'.format(self.name, self.stats)

    @property
    def stats(self):
        return {attr: getattr(self, attr) for attr in self.stat_attrs if hasattr(self, attr)}

    def set_focus_options(self):
        # return self.owner
        options = self.owner.game.unlocked_mods.intersection(self.mods)
        if options:
            self.focus_options = options
            self.focus_options_cycle = cycle(options)
        else:
            self.focus_options = set()
            self.focus_options_cycle = cycle([None])

    def set_focus(self, new_focus):
        print(f'attempting to set skill {self.name} focus to {new_focus}')
        if new_focus == self.focus:
            print(f'skill {self.name} focus is already set to {new_focus} - no change')
        elif new_focus in self.focus_options:
            self.focus = new_focus
            print(f'skill {self.name} focus set to {new_focus}')
        else:
            print(f'cannot set skill {self.name} focus to {new_focus}')

    def next_focus(self):
        self.focus = next(self.focus_options_cycle)

    def gain_xp(self, xp):
        mult = 1 + (xp * .01)
        if self.focus:
            if self.passive:
                if self.owner:
                    self.owner.remove_bonuses(self)
                self.bonuses[self.focus] *= mult
                if self.owner:
                    self.owner.add_bonuses(self)

            else:
                setattr(self, self.focus, getattr(self, self.focus) * mult)

    def get_card(self):
        return SkillCard(self.game, self)

    # def generate_card(self):
    #     card_width = settings.card_width  # cards[0].width
    #     card_height = settings.card_height  # cards[0].height
    #     card_font_size = 24
    #     folder = path.join(self.game.game_folder, 'assets', 'images', 'placeholder')
    #     # temp_card = pg.transform.scale(pg.image.load(path.join(folder, 'trading_card.jpg')), (card_width, card_height))
    #     card = pg.Surface((card_width, card_height))
    #     font = pg.font.Font(self.game.card_font, card_font_size)
    #     font.set_bold(True)
    #     font_height = get_font_height(font)
    #
    #     name = self.name
    #     if self.passive:
    #         skilltype = 'passive'
    #         contents = [(bonus, bonus in self.game.unlocked_mods, bonus == self.focus) for bonus in self.bonuses]
    #     else:
    #         skilltype = 'active'
    #         contents = [(stat, stat in self.game.unlocked_mods, stat == self.focus) for stat in self.stats]
    #
    #     card.fill(colors.yellow if self.game.player.focus_skill == self else colors.white)
    #     card.blit(font.render(name, True, colors.black), (0, 0))
    #     card.blit(font.render(f'Type: {skilltype}', True, colors.blue), (0, font_height))
    #     for i, attribute in enumerate(contents, start=2):
    #         item, learned, focus = attribute
    #         color = colors.green if learned else colors.red
    #         card.blit(font.render(item, True, color, colors.orange if focus else None), (0, i * font_height))
    #
    #     # total xp invested
    #     # total kills?
    #     # current focus
    #     return card


class MovingDamageArea(pg.sprite.Sprite):
    def __init__(self, game, name, owner, image, damage, pos, vel, duration, align='center', moves_with_owner=False):
        self._layer = layers.projectile
        self.groups = game.all_sprites, game.aoe
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.owner = owner
        self.name = name
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
            self.pos += self.owner.vel
        else:
            self.pos += self.vel
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


class MeleeSkill(Skill):
    mods = {'proj_damage', 'proj_speed', 'proj_duration', 'cooldown'}

    aligns = {
        'up': 'midbottom',
        'down': 'midtop',
        'left': 'midright',
        'right': 'midleft'
    }

    def __init__(self, game, image):
        super().__init__(game=game)
        self.stat_attrs = self.stat_attrs.union(self.mods)

        # basic
        self.image = image
        self.name = 'Melee'
        self.passive = False
        self.xp_current = 0
        self.xp_growth_rate = .1
        self.cooldown = 600
        # self.kickback = 0

        # state
        # self.focus = next(iter(self.mods))
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
        return pg.time.get_ticks() - self.last_fired > self.cooldown

    def fire(self):
        spawn_point = self.owner.projectile_spawn
        proj_direction = Vec2(1, 0).rotate(-self.owner.rot)
        proj_vel = proj_direction * self.proj_speed
        proj_vel += self.owner.vel  # no need to save

        if self.can_fire:
            MovingDamageArea(
                game=self.game,
                name=self.name,
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

    mods = {'ticks_per_sec', 'tick_damage', 'range', 'lock_range'}

    def __init__(self, game):
        super().__init__(game=game)
        self.stat_attrs = self.stat_attrs.union(self.mods)

        # basic
        self.name = 'Lightning'
        self.passive = False
        self.xp_current = 0
        self.xp_growth_rate = .1

        # state
        # self.focus = next(iter(self.mods))
        # self.last_tick = pg.time.get_ticks()

        # channeling specific
        self.ticks_per_sec = 2
        self.tick_damage = 10
        self.tick_cost = 5

        # targeting
        self.range = 300
        self.lock_range = 100

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
            target = get_closest_sprite(self.owner.game.mobs, pg.mouse.get_pos() - self.owner.game.camera.offset, radius=self.lock_range)
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


class DashSkill(Skill):

    mods = {'cooldown', 'duration', 'speed_mult'}

    def __init__(self, game):
        super().__init__(game=game)
        self.stat_attrs = self.stat_attrs.union(self.mods)

        # basic
        self.name = 'Dash'
        self.passive = False
        self.xp_current = 0
        self.xp_growth_rate = .1

        # state
        self.active = False
        # self.focus = next(iter(self.mods))
        self.last_fired = 0

        # stats
        self.cooldown = 1000
        self.duration = 300
        self.speed_mult = 2

    @property
    def can_fire(self):
        return pg.time.get_ticks() - self.last_fired > self.cooldown and not self.active

    def fire(self):
        if self.can_fire:
            self.activate()

    def activate(self):
        print(f'activating {self}')
        self.active = True
        self.last_fired = pg.time.get_ticks()
        self.owner.speed *= self.speed_mult
        self.game.active_skills.append(self)

    def deactivate(self):
        print(f'de-activating {self}')
        self.active = False
        self.owner.speed *= 1 / self.speed_mult
        self.game.active_skills.remove(self)

    def update(self):
        if self.active:
            Shadow(self.game, self.owner, self.duration)
            if pg.time.get_ticks() - self.last_fired > self.duration:
                self.deactivate()


class Shadow(pg.sprite.Sprite):
    def __init__(self, game, target, duration):
        self._layer = layers.player
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game

        self.image = target.image.copy()
        self.rect = self.image.get_rect()
        self.pos = target.pos
        self.rect.center = self.pos
        self.duration = duration

        # state
        self.created = pg.time.get_ticks()

    def update(self):
        elapsed = pg.time.get_ticks() - self.created
        if elapsed > self.duration:
            self.kill()
        else:
            # lifespan = elapsed / self.duration
            self.image.fill((255, 255, 255, 128), None, pg.BLEND_RGBA_MULT)
            # self.game.effects_screen.blit()


class SkillCard:
    def __init__(self, game, skill):
        self.game = game
        self.width = settings.card_width  # cards[0].width
        self.height = settings.card_height  # cards[0].height
        self.font_size = 24
        self.image = pg.Surface((self.width, self.height))
        self.font = pg.font.Font(self.game.card_font, self.font_size)
        self.font.set_bold(True)
        self.font_height = get_font_height(self.font)
        self.skill = skill
        self.skilltype = None
        self.contents = None
        self.clickables = {}

        self.update()

    def update(self):
        if self.skill.passive:
            self.skilltype = 'passive'
            self.contents = [(bonus, bonus in self.game.unlocked_mods, bonus == self.skill.focus) for bonus in self.skill.bonuses]
        else:
            self.skilltype = 'active'
            self.contents = [(stat, stat in self.game.unlocked_mods, stat == self.skill.focus) for stat in self.skill.stats]

        self.image.fill(colors.yellow if self.game.player.focus_skill == self.skill else colors.white)

        name_text = self.font.render(self.skill.name + ' *FOCUS*' if self.game.player.focus_skill == self.skill else self.skill.name, True, colors.black)
        name_text_loc = (0, 0)
        self.image.blit(name_text, name_text_loc)

        # test = self.skilltype
        # def name_text_callback():
        #     print('Name text callback triggered')
        #     print(self, test)
        # self.clickables['name_text'] = {
        #     'rect': pg.Rect(name_text_loc, name_text.get_size()),
        #     'callback': name_text_callback,
        # }

        # name_text_rect = name_text.get_rect()
        # self.image.blit(self.font.render(self.skill.name, True, colors.black), (0, 0))
        self.image.blit(self.font.render(f'Type: {self.skilltype}', True, colors.blue), (0, self.font_height))
        for i, attribute in enumerate(self.contents, start=2):
            item, learned, focus = attribute
            color = colors.green if learned else colors.red
            pos = (0, i * self.font_height)
            item_text = self.font.render(item + ' *FOCUS*' if self.skill.focus == item else item, True, color, colors.orange if focus else None)
            item_textbox = pg.Surface((self.width, item_text.get_height()), SRCALPHA)
            item_textbox.blit(item_text, (0, 0
                                          ))
            self.image.blit(item_textbox, pos)
            self.clickables[item] = {
                'rect': pg.Rect(pos, item_textbox.get_size()),
                'callback': self.skill.set_focus,
                'callback_args': item,
            }

    # def get_clickable_rects(self):
    #     return self.clickables
