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
        self.get_keys()
        self.x += self.vx * self.game.delta_time
        self.y += self.vy * self.game.delta_time
        self.rect.x = self.x
        self.collide_with_walls('x')
        self.rect.y = self.y
        self.collide_with_walls('y')
