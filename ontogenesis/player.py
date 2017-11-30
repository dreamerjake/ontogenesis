import pygame as pg

import settings


class Player(pg.sprite.Sprite):
    def __init__(self, game, start):
        # pygame sprite stuff
        self._layer = settings.PLAYER_LAYER
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)

        # object references
        self.game = game

        # assets
        self.standing_frames = None
        self.load_images()

        # graphics
        self.image = self.standing_frames[0]

        # physics
        self.rect = self.image.get_rect()
        self.vx, self.vy = 0, 0
        self.x, self.y = start

        # default stats
        self.speed = 100
        self.hp_current = 80
        self.hp_max = 100
        self.regen = 1  # hp per second

        # item management
        self.inventory = []
        self.equipped = {
            'armor': None,
            'weapon': None,
        }

    def load_images(self):
        # TODO: use metadata file
        self.standing_frames = [self.game.player_move_spritesheet.get_image(256, 0, 64, 64)]

    def process_input(self):
        self.vx, self.vy = 0, 0
        keys = pg.key.get_pressed()
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

    def collide_with_walls(self, direction):
        if direction == 'x':
            hits = pg.sprite.spritecollide(self, self.game.walls, False)
            if hits:
                if self.vx > 0:  # sprite was moving to the right prior to collision
                    self.x = hits[0].rect.left - self.rect.width
                if self.vx < 0:
                    self.x = hits[0].rect.right
                self.vx = 0
                self.rect.x = self.x
        if direction == 'y':
            hits = pg.sprite.spritecollide(self, self.game.walls, False)
            if hits:
                if self.vy > 0:
                    self.y = hits[0].rect.top - self.rect.height
                if self.vy < 0:
                    self.y = hits[0].rect.bottom
                self.vy = 0
                self.rect.y = self.y

    def update(self):
        self.hp_current = min(self.hp_current + (self.regen * self.game.delta_time), self.hp_max)
        self.process_input()
        self.x += self.vx * self.game.delta_time
        self.y += self.vy * self.game.delta_time
        self.rect.x = self.x
        self.collide_with_walls('x')
        self.rect.y = self.y
        self.collide_with_walls('y')
