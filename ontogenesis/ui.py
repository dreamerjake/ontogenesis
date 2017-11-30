import pygame as pg

import settings


class UI:
    """ Master class for the UI object"""

    def __init__(self, game):
        self.game = game
        self.screen = self.game.screen

        self.state_map = {
            'main_menu': self.draw_main_menu,
            'playing': self.draw_hud,
            'paused': self.draw_pause_menu,
        }

    def draw(self):
        current_state = self.game.fsm.current_state
        self.state_map[current_state]()

    def draw_menu_title(self):
        title = self.game.fsm.current_state
        title = title.replace('_', ' ').upper()
        self.draw_text(title, self.game.hud_font, 32, settings.WHITE, settings.WIDTH // 2, 20, align='center')

    def draw_fps(self):
        fps = self.game.clock.get_fps()
        fps = str(int(fps)) if fps != float('inf') else 'inf'
        fps = "FPS: {}".format(fps)
        self.draw_text(fps, self.game.hud_font, 18, settings.WHITE, 5, 5, align='topleft')

    def draw_state(self):
        state = self.game.fsm.current_state
        self.draw_text(state, self.game.hud_font, 18, settings.WHITE, settings.WIDTH - 5, 25, align='topright')

    def draw_debug_warning(self):
        self.draw_text('DEBUG MODE', self.game.hud_font, 18, settings.WHITE, settings.WIDTH - 5, 5, align='topright')

    def draw_player_health(self, x, y, pct):
        if pct < 0:
            pct = 0
        bar_length = 100
        bar_height = 20
        fill = pct * bar_length
        outline_rect = pg.Rect(x, y, bar_length, bar_height)
        fill_rect = pg.Rect(x, y, fill, bar_height)
        if pct > 0.6:
            col = settings.GREEN
        elif pct > 0.3:
            col = settings.YELLOW
        else:
            col = settings.RED
        pg.draw.rect(self.screen, col, fill_rect)
        pg.draw.rect(self.screen, settings.WHITE, outline_rect, 2)

    def draw_main_menu(self):
        self.screen.fill(settings.BLACK)
        self.draw_menu_title()
        self.optional_messages()
        if self.game.debug:
            self.debug_messages()
        pg.display.flip()

    def draw_pause_menu(self):
        self.screen.fill(settings.BLACK)
        self.draw_menu_title()
        self.optional_messages()
        if self.game.debug:
            self.debug_messages()
        pg.display.flip()

    def draw_hud(self):
        health_pct = self.game.player.hp_current / self.game.player.hp_max
        self.draw_player_health(5, 25, health_pct)
        self.optional_messages()
        if self.game.debug:
            self.debug_messages()

    def debug_messages(self):
        self.draw_debug_warning()
        self.draw_state()

    def optional_messages(self):
        if self.game.show_fps:
            self.draw_fps()

    def draw_text(self, text, font_name, size, color, x, y, align="topleft"):
        font = pg.font.Font(font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(**{align: (x, y)})
        self.screen.blit(text_surface, text_rect)

