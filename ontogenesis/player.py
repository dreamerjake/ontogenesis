# -*- coding: utf-8 -*-

from collections import defaultdict
from itertools import cycle, chain
from math import atan2, degrees, pi
from os import path

import pygame as pg
from pygame.math import Vector2 as Vec2

import settings
from enemy import Collider
from helpers import require_attributes, get_direction
from settings import layers, colors
from skill import Skill, PassiveSkill, LightningSkill, MeleeSkill, DashSkill


class Equippable:
    """ Mixin that allows for wearing items and passive skills """
    def __init__(self):
        super().__init__()
        require_attributes(self, ['equipped'])

    def add_bonuses(self, equippable):
        for bonus in equippable.bonuses:
            old = getattr(self, bonus)
            new = old + equippable.bonuses[bonus]
            print(f'adding {equippable.name} - {bonus}: {old} => {new}')
            setattr(self, bonus, getattr(self, bonus) + equippable.bonuses[bonus])

    def remove_bonuses(self, equippable):
        for bonus in equippable.bonuses:
            old = getattr(self, bonus)
            new = old - equippable.bonuses[bonus]
            print(f'removing {equippable.name} - {bonus}: {old} => {new}')
            setattr(self, bonus, getattr(self, bonus) - equippable.bonuses[bonus])

    def sum_bonuses(self):
        bonuses = defaultdict(float)
        for slot, equip in self.equipped.items():
            if equip:
                if isinstance(equip, list):  # see if the slot can hold multiple things
                    for item in equip:
                        for bonus in item.bonuses:
                            bonuses[bonus] += item.bonuses[bonus]
                else:
                    for bonus in equip.bonuses:
                        bonuses[bonus] += equip.bonuses[bonus]
        return bonuses

    def equip(self, slot, equippable):
        # TODO: add a matching unequip method if it becomes necessary
        print('equipping', equippable)
        current = self.equipped[slot]
        equippable.owner = self
        # setattr(equippable, 'owner', self)
        # print(equippable.owner, equippable)
        # print('focus options', equippable.focus_options)
        # append the item if the slot can hold multiple items
        if isinstance(current, list):
            current.append(equippable)
            self.add_bonuses(equippable)
        # swap with current if the slot only holds 1 item
        elif self.equipped[slot]:
            self.equipped[slot] = equippable
            self.add_bonuses(equippable)
            self.remove_bonuses(current)
        # just add the item if the slot is empty
        else:
            self.equipped[slot] = equippable
            self.add_bonuses(equippable)
        # self.calc_all_skills()
        if isinstance(equippable, Skill):
            equippable.set_focus_options()

    def unequip_all(self):
        for slot, equip in self.equipped.items():
            if equip:
                if isinstance(equip, list):  # see if the slot can hold multiple things
                    for item in equip:
                        item.owner = None
                else:
                    equip.owner = None

        self.equipped = {
            'armor': None,
            'weapon': None,
            'active_skill': None,
            'passives': []
        }


class Player(pg.sprite.Sprite, Collider, Equippable):

    debugname = "Player"

    def __init__(self, game, start_pos):
        # pygame sprite stuff
        self._layer = layers.player
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        super().__init__()

        # object references
        self.game = game

        # assets
        self.standing_frames = None
        self.moving_frames = None
        self.attacking_frames = None
        self.load_images()

        # graphics
        self.last_update = pg.time.get_ticks()
        self.frame_delay = 200
        self.image = next(self.standing_frames['down'])
        self.orig_image = self.image

        # physics
        self.rect = self.image.get_rect(center=start_pos)
        self.hit_rect = pg.Rect(0, 0, settings.TILESIZE - 5, settings.TILESIZE - 5)
        self.hit_rect.center = self.rect.center
        self.vel = Vec2(0, 0)
        # self.vx, self.vy = 0, 0
        # self.x, self.y = start_pos
        self.pos = Vec2(start_pos)
        self.rot = 0
        self.proj_offset = Vec2(15, 15)  # hardcoded to the placeholder graphics

        # state
        self.dead = False
        self.last_shot = 0
        self.last_skill_change = 0
        self.focus_skill = None
        self.attacking = False
        # self.move_state = 'normal'
        self.speed_mul = 1.0
        # self.last_positions = Queue(maxsize=10)

        # default stats
        self.skill_change_delay = 100
        self.xp_total = 0
        self.speed = 100
        self.hp_current = 80
        self.hp_max = 100
        self.hps_regen = 1  # hp per second
        self.resource_current = 50
        self.resource_max = 100
        self.rps_regen = 3  # resource per second
        self.eating_rate = 1  # food per second

        self.starving_penalties = {
            'speed': 50
        }

        # item management
        self.food = 100
        self.inventory = []
        self.equipped = {
            'armor': None,
            'weapon': None,
            'active_skill': None,
            'melee_skill': None,
            'move_skill': None,
            'passives': []
        }
        # self.focus_skill = choice([self.equipped['active_skill']] + self.equipped['passives'])

        self.load_placeholder_skills()
        self.all_skills_gen = cycle(self.all_skills)

    @property
    def can_change_skills(self):
        return pg.time.get_ticks() - self.last_skill_change > self.skill_change_delay

    @property
    def all_skills(self):
        active_skills = [self.equipped['active_skill'], self.equipped['melee_skill'], self.equipped['move_skill']]
        passive_skills = self.equipped['passives']
        skill_chain = chain(active_skills, passive_skills)
        return skill_chain

    # def calc_all_skills(self):
    #     active_skills = [self.equipped['active_skill'], self.equipped['melee_skill'], self.equipped['move_skill']]
    #     passive_skills = self.equipped['passives']
    #     return chain(active_skills, passive_skills)
    #     self.all_skills = cycle()
        # return skills

    @property
    def moving(self):
        return self.vel.length() > 0

    @property
    def facing(self):
        return get_direction(self.mouse_angle, ['up', 'right', 'down', 'left'])

    @property
    def mouse_angle(self):
        x1, y1 = self.game.camera.apply(self).center
        x2, y2 = Vec2(pg.mouse.get_pos())
        # print ((x1, y1), (x2, y2))
        dx = x2 - x1
        dy = y2 - y1
        rads = atan2(dy, dx)
        rads %= 2 * pi
        degs = int(degrees(rads)) + 90
        return degs % 360

    @property
    def passive_names(self):
        return [skill.name for skill in self.equipped['passives']]
        # self.passives_window.update(new_content=[skill.name for skill in self.game.player.equipped['passives']])

    @property
    def projectile_spawn(self):
        spawn_points = {
            'up': self.rect.midtop,
            'down': self.rect.midbottom,
            'left': self.rect.midleft,
            'right': self.rect.midright
        }
        return spawn_points[self.facing]

    def load_placeholder_skills(self):
        """manually set starting skills"""
        lightning_skill = LightningSkill(self.game)
        melee_skill = MeleeSkill(self.game, self.game.sword_img)
        running_skill = PassiveSkill(self.game, 'Running', speed=10)
        toughness_skill = PassiveSkill(self.game, 'Toughness', hp_max=10)
        dash_skill = DashSkill(self.game)

        for skill in [running_skill, toughness_skill]:
            self.equip('passives', skill)
        self.equip('active_skill', lightning_skill)
        self.equip('melee_skill', melee_skill)
        self.equip('move_skill', dash_skill)

    def load_images(self):
        self.load_link()
        # self.standing_frames = [self.game.player_move_spritesheet.get_image(256, 0, 64, 64, rot=-90)]
        # self.moving_frames = cycle([
        #     self.game.player_wobble_spritesheet.get_image(0, 0, 64, 64, rot=-90, scale_to=(48, 48)),
        #     self.game.player_wobble_spritesheet.get_image(64, 0, 64, 64, rot=-90, scale_to=(48, 48)),
        #     self.game.player_wobble_spritesheet.get_image(128, 0, 64, 64, rot=-90, scale_to=(48, 48)),
        #     self.game.player_wobble_spritesheet.get_image(192, 0, 64, 64, rot=-90, scale_to=(48, 48)),
        #     self.game.player_wobble_spritesheet.get_image(256, 0, 64, 64, rot=-90, scale_to=(48, 48)),
        #     self.game.player_wobble_spritesheet.get_image(320, 0, 64, 64, rot=-90, scale_to=(48, 48)),
        #     self.game.player_wobble_spritesheet.get_image(384, 0, 64, 64, rot=-90, scale_to=(48, 48)),
        #     self.game.player_wobble_spritesheet.get_image(448, 0, 64, 64, rot=-90, scale_to=(48, 48))
        # ])

    def load_link(self):
        link_dir = path.join(self.game.game_folder, 'assets', 'images', 'placeholder')
        size = 48
        self.standing_frames = {
            'left': cycle([
                pg.transform.scale(pg.image.load(path.join(link_dir, 'link_side_0.png')), (size, size)),
            ]),

            'right': cycle([
                pg.transform.scale(pg.transform.flip(pg.image.load(path.join(link_dir, 'link_side_0.png')), True, False), (size, size)),
            ]),

            'up': cycle([
                pg.transform.scale(pg.image.load(path.join(link_dir, 'link_up_0.png')), (size, size)),
            ]),

            'down': cycle([
                pg.transform.scale(pg.image.load(path.join(link_dir, 'link_down_0.png')), (size, size)),
            ])
        }
        self.moving_frames = {
            'left': cycle([
                pg.transform.scale(pg.image.load(path.join(link_dir, 'link_side_0.png')), (size, size)),
                pg.transform.scale(pg.image.load(path.join(link_dir, 'link_side_1.png')), (size, size))
            ]),

            'right': cycle([
                pg.transform.scale(pg.transform.flip(pg.image.load(path.join(link_dir, 'link_side_0.png')), True, False), (size, size)),
                pg.transform.scale(pg.transform.flip(pg.image.load(path.join(link_dir, 'link_side_1.png')), True, False), (size, size))
            ]),

            'up': cycle([
                pg.transform.scale(pg.image.load(path.join(link_dir, 'link_up_0.png')), (size, size)),
                pg.transform.scale(pg.image.load(path.join(link_dir, 'link_up_1.png')), (size, size))
            ]),

            'down': cycle([
                pg.transform.scale(pg.image.load(path.join(link_dir, 'link_down_0.png')), (size, size)),
                pg.transform.scale(pg.image.load(path.join(link_dir, 'link_down_1.png')), (size, size))
            ])
        }
        self.attacking_frames = {
            'left': cycle([
                pg.transform.scale(pg.image.load(path.join(link_dir, 'link_attack_side_0.png')), (size, size)),
            ]),

            'right': cycle([
                pg.transform.scale(pg.transform.flip(pg.image.load(path.join(link_dir, 'link_attack_side_0.png')), True, False), (size, size)),
            ]),

            'up': cycle([
                pg.transform.scale(pg.image.load(path.join(link_dir, 'link_attack_up_0.png')), (size, size)),
            ]),

            'down': cycle([
                pg.transform.scale(pg.image.load(path.join(link_dir, 'link_attack_down_0.png')), (size, size)),
            ])
        }

    def animate(self):
        now = pg.time.get_ticks()
        if now - self.last_update > self.frame_delay:
            if self.attacking:
                self.image = next(self.attacking_frames[self.facing])
            elif self.moving:
                self.image = next(self.moving_frames[self.facing])
            else:
                self.image = next(self.standing_frames[self.facing])
            self.rect = self.image.get_rect()
            self.last_update = now

    def process_input(self):
        self.vel = Vec2(0, 0)  # this might be a problem later on, if external forces can effect player position
        keys = pg.key.get_pressed()

        # rotational movement
        if self.game.configs.control_scheme == 'rotational':
            if keys[pg.K_LEFT] or keys[pg.K_a]:
                self.vel = Vec2(self.speed, 0).rotate(-self.rot - 90)
            if keys[pg.K_RIGHT] or keys[pg.K_d]:
                self.vel = Vec2(self.speed, 0).rotate(-self.rot + 90)
            if keys[pg.K_UP] or keys[pg.K_w]:
                self.vel = Vec2(self.speed, 0).rotate(-self.rot)
            if keys[pg.K_DOWN] or keys[pg.K_s]:
                self.vel = Vec2(-self.speed, 0).rotate(-self.rot)  # no backwards speed penalty

        if self.game.configs.control_scheme == '4d':
            if keys[pg.K_LEFT] or keys[pg.K_a]:
                self.vel += Vec2(self.speed, 0).rotate(180)
            if keys[pg.K_RIGHT] or keys[pg.K_d]:
                self.vel += Vec2(self.speed, 0).rotate(0)
            if keys[pg.K_UP] or keys[pg.K_w]:
                self.vel += Vec2(self.speed, 0).rotate(270)
            if keys[pg.K_DOWN] or keys[pg.K_s]:
                self.vel += Vec2(-self.speed, 0).rotate(270)  # no backwards speed penalty

        # skills
        # switch focus skill
        if keys[pg.K_PAGEDOWN]:
            if self.can_change_skills:
                self.focus_skill = next(self.all_skills_gen)
                self.last_skill_change = pg.time.get_ticks()

        # switch focus bonus
        if keys[pg.K_PAGEUP]:
            if self.can_change_skills and self.focus_skill:
                self.focus_skill.next_focus()
                self.last_skill_change = pg.time.get_ticks()

        # active skill
        if pg.mouse.get_pressed()[0]:
            self.equipped['active_skill'].fire()

        # melee attack
        if keys[pg.K_SPACE] or pg.mouse.get_pressed()[2]:
            self.equipped['melee_skill'].fire()

        # movement skill
        if keys[pg.K_LCTRL]:
            self.equipped['move_skill'].fire()

    def rotate(self, target):
        """ face the target """
        self.rot = (target - self.hit_rect.center).angle_to(Vec2(1, 0))
        # self.image = pg.transform.rotate(self.orig_image, self.rot)
        # self.rect = self.image.get_rect()

    def gain_xp(self, xp):
        self.xp_total += xp
        # print(f'player gained {xp} xp')
        if self.focus_skill:
            self.focus_skill.gain_xp(xp)
            # print(f'{self.focus_skill.name} gained {xp} experience in {self.focus_skill.focus}')
            self.game.message(f'{self.focus_skill.name} gained {xp} experience in {self.focus_skill.focus}', colors.yellow)
        else:
            self.game.message(f'No focus set - experience wasted', colors.orange)

    def gain_food(self, food):
        self.food += food
        self.game.message(f'Gained {food} food', colors.green)

    def die(self):
        print('Player Died')
        # self.game.new()
        self.dead = True
        self.game.fsm('die')
        # print(sys.getrefcount(self))
        # self.kill()
        # print(get_referrers(self))

    def update(self):
        # print(self.moving, self.rot, self.mouse_angle, self.facing)

        # health and resource regen/degen
        if self.hps_regen != 0:
            self.hp_current = min(self.hp_current + (self.hps_regen * self.game.delta_time), self.hp_max)
        if self.rps_regen != 0:
            self.resource_current = min(self.resource_current + (self.rps_regen * self.game.delta_time), self.resource_max)
        # TODO: regen of health/resource consumes extra food
        if self.eating_rate != 0:
            self.food = max(0, self.food - (self.eating_rate * self.game.delta_time))

        if self.food == 0:
            for penalty in self.starving_penalties:
                setattr(self, penalty, self.starving_penalties[penalty])

        # handle controls
        self.process_input()

        # face the mouse
        self.rotate(self.game.mouse_pos)

        # animate
        self.animate()

        # move
        # self.pos += self.vel * (self.game.delta_time * self.speed_mul)
        if self.moving:
            self.vel.scale_to_length(self.speed / self.game.configs.fps)
            # print(type(self.pos))
            self.pos += self.vel

        # collide with walls
        self.hit_rect.centerx = self.pos.x
        self.collide(self.game.walls, 'x')
        self.hit_rect.centery = self.pos.y
        self.collide(self.game.walls, 'y')
        self.rect.center = self.hit_rect.center

        # death condition checks
        if self.hp_current <= 0:
            self.die()
