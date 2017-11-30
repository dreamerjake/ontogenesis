import pygame as pg

import settings


class Player(pg.sprite.Sprite):
    def __init__(self, game, start):
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((settings.TILESIZE, settings.TILESIZE))
        self.image.fill(settings.YELLOW)
        self.rect = self.image.get_rect()
        self.vx, self.vy = 0, 0
        self.x, self.y = start
        # self.rect.x = self.x * settings.TILESIZE
        # self.rect.y = self.y * settings.TILESIZE

        # default stats
        self.speed = 100

    def get_keys(self):
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

    def move(self):
        pass

    def update(self):
        self.get_keys()
        self.x += self.vx * self.game.delta_time
        self.y += self.vy * self.game.delta_time
        self.rect.topleft = self.x, self.y
