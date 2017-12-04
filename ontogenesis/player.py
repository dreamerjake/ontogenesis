import pygame as pg
from pygame.math import Vector2 as Vec2

import settings
from settings import layers
from skill import Projectile


class Player(pg.sprite.Sprite):

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
        self.load_images()

        # graphics
        self.image = self.standing_frames[0]
        self.orig_image = self.image

        # physics
        self.rect = self.image.get_rect(center=start_pos)
        self.hit_rect = pg.Rect(0, 0, settings.TILESIZE - 5, settings.TILESIZE - 5)
        self.hit_rect.center = self.rect.center
        self.vx, self.vy = 0, 0
        # self.x, self.y = start_pos
        self.pos = Vec2(start_pos)
        self.rot = 0
        self.proj_offset = Vec2(10, 10)  # hardcoded to the placeholder graphics

        # default stats
        self.speed = 100
        self.hp_current = 80
        self.hp_max = 100
        self.hps_regen = 1  # hp per second

        # item management
        self.inventory = []
        self.equipped = {
            'armor': None,
            'weapon': None,
        }

    def load_images(self):
        self.standing_frames = [self.game.player_move_spritesheet.get_image(256, 0, 64, 64, rot=-90)]

    def process_input(self):
        self.vx, self.vy = 0, 0  # this might be a problem later on, if external forces can effect player position
        keys = pg.key.get_pressed()
        # mouse_x, mouse_y = pg.mouse.get_pos()

        # movement
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            self.vx = -self.speed
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            self.vx = self.speed
        if keys[pg.K_UP] or keys[pg.K_w]:
            self.vy = -self.speed
        if keys[pg.K_DOWN] or keys[pg.K_s]:
            self.vy = self.speed

        # skills
        if keys[pg.K_SPACE]:
            damage = 10
            direction = Vec2(1, 0).rotate(-self.rot)
            speed = 500
            duration = 500
            pos = self.pos + self.proj_offset.rotate(-self.rot)
            kickback = 200
            Projectile(game=self.game, damage=damage, pos=pos, speed=speed, direction=direction, duration=duration, kickback=kickback)
            if kickback:
                kickback_vector = Vec2(-kickback, 0).rotate(-self.rot)
                self.vx += kickback_vector.x
                self.vy += kickback_vector.y

        # diagonal movement fix
        if self.vx != 0 and self.vy != 0:
            self.vx *= 0.7071
            self.vy *= 0.7071

    @staticmethod
    def collide_hit_rect(one, two):
        return one.hit_rect.colliderect(two.rect)

    def collide_with_walls(self, direction):

        if direction == 'x':
            hits = pg.sprite.spritecollide(self, self.game.walls, False, self.collide_hit_rect)
            if hits:

                if not self.game.sfx_channel.get_sound():
                    self.game.sfx_channel.play(self.game.player_sound_ow)

                if self.vx > 0:  # sprite was moving to the right prior to collision
                    self.pos.x = hits[0].rect.left - self.hit_rect.width / 2
                if self.vx < 0:
                    self.pos.x = hits[0].rect.right + self.hit_rect.width / 2
                self.vx = 0
                self.hit_rect.centerx = self.pos.x

        if direction == 'y':
            hits = pg.sprite.spritecollide(self, self.game.walls, False, self.collide_hit_rect)
            if hits:

                if not self.game.sfx_channel.get_sound():
                    self.game.sfx_channel.play(self.game.player_sound_ow)

                if self.vy > 0:
                    self.pos.y = hits[0].rect.top - self.hit_rect.height / 2
                if self.vy < 0:
                    self.pos.y = hits[0].rect.bottom + self.hit_rect.height / 2
                self.vy = 0
                self.hit_rect.centery = self.pos.y

    def rotate(self, target):
        """ face the target """
        self.rot = (target - self.hit_rect.center).angle_to(Vec2(1, 0))
        self.image = pg.transform.rotate(self.orig_image, self.rot)

    def update(self):
        if self.hps_regen != 0:
            self.hp_current = min(self.hp_current + (self.hps_regen * self.game.delta_time), self.hp_max)
        self.process_input()
        self.rotate(Vec2(pg.mouse.get_pos()) - self.game.camera.offset)

        self.pos.x += self.vx * self.game.delta_time
        self.pos.y += self.vy * self.game.delta_time

        self.hit_rect.centerx = self.pos.x
        self.collide_with_walls('x')
        self.hit_rect.centery = self.pos.y
        self.collide_with_walls('y')
        self.rect.center = self.hit_rect.center
