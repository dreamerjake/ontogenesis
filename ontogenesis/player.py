from collections import defaultdict
from itertools import cycle

import pygame as pg
from pygame.math import Vector2 as Vec2

from enemy import Collider
from helpers import require_attributes
import settings
from settings import layers
from skill import Projectile, run_skill, toughness_skill


class Equippable:
    """ Mixin that allows for wearing items and passive skills """
    def __init__(self):
        super().__init__()
        require_attributes(self, ['equipped'])

    def add_bonuses(self, equippable):
        for bonus in equippable.bonuses:
            setattr(self, bonus, getattr(self, bonus) + equippable.bonuses[bonus])

    def remove_bonuses(self, equippable):
        for bonus in equippable:
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
                    for bonus in equip:
                        bonuses[bonus] += equip.bonuses[bonus]
        return bonuses

    def equip(self, slot, equippable):
        # TODO: add a matching unequip method if it becomes necessary
        current = self.equipped[slot]

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


class Player(pg.sprite.Sprite, Collider, Equippable):

    debugname = "Player"

    def __init__(self, game, start_pos):
        # pygame sprite stuff
        self._layer = layers.player
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)

        # object references
        self.game = game

        # assets
        self.standing_frames = None
        self.moving_frames = None
        self.load_images()

        # graphics
        self.last_update = pg.time.get_ticks()
        self.frame_delay = 200
        self.image = self.standing_frames[0]
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
        self.proj_offset = Vec2(25, 15)  # hardcoded to the placeholder graphics

        # state
        self.last_shot = pg.time.get_ticks()
        self.focus_skill = None

        # default stats
        self.speed = 100
        self.hp_current = 80
        self.hp_max = 100
        self.hps_regen = 1  # hp per second
        self.fire_delay = 200

        # item management
        self.inventory = []
        self.equipped = {
            'armor': None,
            'weapon': None,
            'passives': []
        }

        for skill in [run_skill, toughness_skill]:
            print(self.sum_bonuses())
            self.equip('passives', skill)
            print(self.sum_bonuses())

    def load_images(self):
        self.standing_frames = [self.game.player_move_spritesheet.get_image(256, 0, 64, 64, rot=-90)]
        self.moving_frames = cycle([
            self.game.player_wobble_spritesheet.get_image(0, 0, 64, 64, rot=-90, scale_to=(48, 48)),
            self.game.player_wobble_spritesheet.get_image(64, 0, 64, 64, rot=-90, scale_to=(48, 48)),
            self.game.player_wobble_spritesheet.get_image(128, 0, 64, 64, rot=-90, scale_to=(48, 48)),
            self.game.player_wobble_spritesheet.get_image(192, 0, 64, 64, rot=-90, scale_to=(48, 48)),
            self.game.player_wobble_spritesheet.get_image(256, 0, 64, 64, rot=-90, scale_to=(48, 48)),
            self.game.player_wobble_spritesheet.get_image(320, 0, 64, 64, rot=-90, scale_to=(48, 48)),
            self.game.player_wobble_spritesheet.get_image(384, 0, 64, 64, rot=-90, scale_to=(48, 48)),
            self.game.player_wobble_spritesheet.get_image(448, 0, 64, 64, rot=-90, scale_to=(48, 48))
        ])

    def process_input(self):
        # self.vx, self.vy = 0, 0  # this might be a problem later on, if external forces can effect player position
        self.vel = Vec2(0, 0)
        keys = pg.key.get_pressed()

        # 4-d movement
        # if keys[pg.K_LEFT] or keys[pg.K_a]:
        #     self.vx = -self.speed
        # if keys[pg.K_RIGHT] or keys[pg.K_d]:
        #     self.vx = self.speed
        # if keys[pg.K_UP] or keys[pg.K_w]:
        #     self.vy = -self.speed
        # if keys[pg.K_DOWN] or keys[pg.K_s]:
        #     self.vy = self.speed

        # rotational movement
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            self.vel = Vec2(self.speed, 0).rotate(-self.rot - 90)
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            self.vel = Vec2(self.speed, 0).rotate(-self.rot + 90)
        if keys[pg.K_UP] or keys[pg.K_w]:
            self.vel = Vec2(self.speed, 0).rotate(-self.rot)
        if keys[pg.K_DOWN] or keys[pg.K_s]:
            self.vel = Vec2(-self.speed, 0).rotate(-self.rot)  # no backwards speed penalty

        # skills
        if keys[pg.K_SPACE] or pg.mouse.get_pressed()[0]:
            if pg.time.get_ticks() - self.last_shot > self.fire_delay:  # TODO: can_fire function
                damage = 10
                direction = Vec2(1, 0).rotate(-self.rot)
                speed = 500
                duration = 500
                pos = self.pos + self.proj_offset.rotate(-self.rot)
                kickback = 200
                Projectile(game=self.game, damage=damage, pos=pos, speed=speed, direction=direction, duration=duration, kickback=kickback)
                if kickback:
                    kickback_vector = Vec2(-kickback, 0).rotate(-self.rot)
                    self.vel += kickback_vector
                self.last_shot = pg.time.get_ticks()
                # kickback for 4-d movement
                # self.vx += kickback_vector.x
                # self.vy += kickback_vector.y

        # diagonal movement fix for 4-d movement
        # if self.vx != 0 and self.vy != 0:
        #     self.vx *= 0.7071
        #     self.vy *= 0.7071

    # @staticmethod
    # def collide_hit_rect(one, two):
    #     return one.hit_rect.colliderect(two.rect)
    #
    # def collide_with_walls(self, direction):
    #
    #     if direction == 'x':
    #         hits = pg.sprite.spritecollide(self, self.game.walls, False, self.collide_hit_rect)
    #         if hits:
    #
    #             if not self.game.sfx_channel.get_sound():
    #                 self.game.sfx_channel.play(self.game.player_sound_ow)
    #
    #             if self.vx > 0:  # sprite was moving to the right prior to collision
    #                 self.pos.x = hits[0].rect.left - self.hit_rect.width / 2
    #             if self.vx < 0:
    #                 self.pos.x = hits[0].rect.right + self.hit_rect.width / 2
    #             self.vx = 0
    #             self.hit_rect.centerx = self.pos.x
    #
    #     if direction == 'y':
    #         hits = pg.sprite.spritecollide(self, self.game.walls, False, self.collide_hit_rect)
    #         if hits:
    #
    #             if not self.game.sfx_channel.get_sound():
    #                 self.game.sfx_channel.play(self.game.player_sound_ow)
    #
    #             if self.vy > 0:
    #                 self.pos.y = hits[0].rect.top - self.hit_rect.height / 2
    #             if self.vy < 0:
    #                 self.pos.y = hits[0].rect.bottom + self.hit_rect.height / 2
    #             self.vy = 0
    #             self.hit_rect.centery = self.pos.y

    def rotate(self, target):
        """ face the target """
        self.rot = (target - self.hit_rect.center).angle_to(Vec2(1, 0))
        self.image = pg.transform.rotate(self.orig_image, self.rot)
        self.rect = self.image.get_rect()

    def die(self):
        print('Player Died')
        self.game.new()
        self.game.fsm('die')

    def update(self):
        # health regen/degen
        if self.hps_regen != 0:
            self.hp_current = min(self.hp_current + (self.hps_regen * self.game.delta_time), self.hp_max)

        # handle controls
        self.process_input()

        # animate
        now = pg.time.get_ticks()
        if now - self.last_update > self.frame_delay:
            self.orig_image = next(self.moving_frames)
            self.last_update = now

        # face the mouse
        self.rotate(Vec2(pg.mouse.get_pos()) - self.game.camera.offset)

        # move
        self.pos += self.vel * self.game.delta_time

        # # 4-d movement system wall collisons
        # self.pos.x += self.vx * self.game.delta_time
        # self.pos.y += self.vy * self.game.delta_time
        # self.hit_rect.centerx = self.pos.x
        # self.collide_with_walls('x')
        # self.hit_rect.centery = self.pos.y
        # self.collide_with_walls('y')
        # self.rect.center = self.hit_rect.center

        # collide with walls
        self.hit_rect.centerx = self.pos.x
        self.collide(self.game.walls, 'x')
        self.hit_rect.centery = self.pos.y
        self.collide(self.game.walls, 'y')
        self.rect.center = self.hit_rect.center

        if self.hp_current <= 0:
            self.die()
