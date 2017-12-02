import pygame as pg

import settings
from settings import layers


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
        self.x, self.y = start_pos

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
        self.standing_frames = [self.game.player_move_spritesheet.get_image(256, 0, 64, 64)]

    def process_input(self):
        self.vx, self.vy = 0, 0  # this might be a problem later on, if external forces can effect player position
        keys = pg.key.get_pressed()
        # mouse_x, mouse_y = pg.mouse.get_pos()
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            self.vx = -self.speed
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            self.vx = self.speed
        if keys[pg.K_UP] or keys[pg.K_w]:
            self.vy = -self.speed
        if keys[pg.K_DOWN] or keys[pg.K_s]:
            self.vy = self.speed

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

                # TODO: set a timeout on playing sounds
                self.game.player_sound_ow.play()

                if self.vx > 0:  # sprite was moving to the right prior to collision
                    self.x = hits[0].rect.left - self.hit_rect.width / 2
                if self.vx < 0:
                    self.x = hits[0].rect.right + self.hit_rect.width / 2
                self.vx = 0
                self.hit_rect.centerx = self.x

        if direction == 'y':
            hits = pg.sprite.spritecollide(self, self.game.walls, False, self.collide_hit_rect)
            if hits:

                # TODO: set a timeout on playing sounds
                self.game.player_sound_ow.play()

                if self.vy > 0:
                    self.y = hits[0].rect.top - self.hit_rect.height / 2
                if self.vy < 0:
                    self.y = hits[0].rect.bottom + self.hit_rect.height / 2
                self.vy = 0
                self.hit_rect.centery = self.y

    def rotate(self):
        # face the mouse position
        # TODO: use the cleaner method from the Mob class
        adj_pos = self.game.camera.apply(self).center
        _, angle = (pg.mouse.get_pos() - pg.math.Vector2(adj_pos)).as_polar()
        self.image = pg.transform.rotate(self.orig_image, -angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self):
        if self.hps_regen != 0:
            self.hp_current = min(self.hp_current + (self.hps_regen * self.game.delta_time), self.hp_max)
        self.process_input()
        self.rotate()
        # self.rect.center = self.x, self.y
        self.x += self.vx * self.game.delta_time
        self.y += self.vy * self.game.delta_time
        self.hit_rect.centerx = self.x
        self.collide_with_walls('x')
        self.hit_rect.centery = self.y
        self.collide_with_walls('y')
        self.rect.center = self.hit_rect.center
