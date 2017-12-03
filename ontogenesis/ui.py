from collections import defaultdict

import pygame as pg
from pygame.locals import MOUSEMOTION, MOUSEBUTTONUP, MOUSEBUTTONDOWN

import settings
from settings import colors


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

        self.start_button = Button(
            self.game, settings.WIDTH // 2, 100,
            up_img=self.game.button_up,
            down_img=self.game.button_down,
            highlight_img=self.game.button_hover,
            caption='Start')
        self.start_button.callbacks['click'] = lambda x: self.game.fsm('new_game')

        # button groups
        self.all_buttons = [self.start_button]
        self.main_menu_buttons = [self.start_button]

    def draw(self):
        current_state = self.game.fsm.current_state
        self.state_map[current_state]()

    def draw_menu_title(self):
        title = self.game.fsm.current_state
        title = title.replace('_', ' ').upper()
        self.draw_text(title, self.game.hud_font, 32, colors.white, settings.WIDTH // 2, 20, align='center')
        self.start_button.draw(self.screen)

    def draw_fps(self):
        fps = self.game.clock.get_fps()
        fps = str(int(fps)) if fps != float('inf') else 'inf'
        fps = "FPS: {}".format(fps)
        self.draw_text(fps, self.game.hud_font, 18, colors.white, 5, 5, align='topleft')

    def draw_state(self):
        state = self.game.fsm.current_state
        self.draw_text(state, self.game.hud_font, 18, colors.white, settings.WIDTH - 5, 25, align='topright')

    def draw_debug_warning(self):
        self.draw_text('DEBUG MODE', self.game.hud_font, 18, colors.white, settings.WIDTH - 5, 5, align='topright')

    def draw_flashed_messages(self):
        for i, message in enumerate(self.game.message_flash_queue.get()[::-1]):
            height = pg.font.Font(self.game.message_flash_font, 40).size(message)[1]
            offset = i * height
            self.draw_text(
                # 'FLASHED MESSAGE',
                message,
                self.game.message_flash_font,
                40,
                colors.yellow,
                settings.WIDTH / 2,
                settings.HEIGHT / 2 - settings.HEIGHT * .10 - offset,
                align='center')

    def draw_player_health(self, x, y, pct):
        if pct < 0:
            pct = 0
        bar_length = 100
        bar_height = 20
        fill = pct * bar_length
        outline_rect = pg.Rect(x, y, bar_length, bar_height)
        fill_rect = pg.Rect(x, y, fill, bar_height)
        if pct > 0.6:
            col = colors.green
        elif pct > 0.3:
            col = colors.yellow
        else:
            col = colors.red
        pg.draw.rect(self.screen, col, fill_rect)
        pg.draw.rect(self.screen, colors.white, outline_rect, 2)

    @staticmethod
    def hide_buttons(button_group):
        for button in button_group:
            button.visible = False

    @staticmethod
    def show_buttons(button_group):
        for button in button_group:
            button.visible = True

    def draw_main_menu(self):
        self.hide_buttons(self.all_buttons)
        self.show_buttons(self.main_menu_buttons)
        self.screen.fill(colors.black)
        self.draw_menu_title()
        self.optional_messages()
        if self.game.configs.debug:
            self.debug_messages()
        self.draw_flashed_messages()
        pg.display.flip()

    def draw_pause_menu(self):
        self.hide_buttons(self.all_buttons)
        # self.show_buttons(self.main_menu_buttons)
        self.screen.fill(colors.black)
        self.draw_menu_title()
        self.optional_messages()
        if self.game.configs.debug:
            self.debug_messages()
        self.draw_flashed_messages()
        pg.display.flip()

    def draw_hud(self):
        self.hide_buttons(self.all_buttons)
        health_pct = self.game.player.hp_current / self.game.player.hp_max
        self.draw_player_health(5, 25, health_pct)
        self.optional_messages()
        if self.game.configs.debug:
            self.debug_messages()
        self.draw_flashed_messages()

    def debug_messages(self):
        self.draw_debug_warning()
        self.draw_state()

    def optional_messages(self):
        if self.game.configs.show_fps:
            self.draw_fps()

    def draw_text(self, text, font_name, size, color, x, y, align="topleft"):
        font = pg.font.Font(font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(**{align: (x, y)})
        self.screen.blit(text_surface, text_rect)


class Button:

    def __init__(self, game, x, y, up_img, down_img, highlight_img, caption='', font=None):

        # check for mismatched image sizes
        if up_img.get_size() != down_img.get_size() != highlight_img.get_size():
            raise Exception('Button surfaces must all be the same size')

        self.game = game

        self.up_img = up_img
        self.down_img = down_img
        self.highlight_img = highlight_img

        self.width, self.height = self.up_img.get_size()

        self.rect = pg.Rect(x - self.width // 2, y - self.height // 2, self.width, self.height)

        self.caption = caption
        self.font = pg.font.Font(font, self.game.configs.ui_button_text_size)

        self.visible = True
        self.down = False
        self.mouseover = False
        self.last_mousedown_over = False

        self.caption_surface = self.font.render(self.caption, True, self.game.configs.ui_button_text_color)
        self.caption_rect = self.caption_surface.get_rect()
        self.caption_rect.center = self.width // 2, self.height // 2

        for image in [self.up_img, self.down_img, self.highlight_img]:
            image.blit(self.caption_surface, self.caption_rect)

        self.callbacks = defaultdict(lambda: lambda x: None)

    def draw(self, surface):
        if self.visible:
            if self.down:
                surface.blit(self.down_img, self.rect)
            elif self.mouseover:
                surface.blit(self.highlight_img, self.rect)
            else:
                surface.blit(self.up_img, self.rect)

    def handle_event(self, event):
        if not self.visible or event.type not in (MOUSEMOTION, MOUSEBUTTONUP, MOUSEBUTTONDOWN):
            return

        mouse_inside = self.rect.collidepoint(event.pos)
        exited = False

        # mouse enters button
        if not self.mouseover and mouse_inside:
            self.mouseover = True
            self.callbacks['enter'](event)

        # mouse exits button
        elif self.mouseover and not mouse_inside:
            self.mouseover = False
            exited = True  # call 'enter' callback later, since we want 'move' callback to be handled first

        if mouse_inside:
            # mouse moves over button
            if event.type == MOUSEMOTION:
                self.callbacks['move'](event)

            # mouse down over button
            elif event.type == MOUSEBUTTONDOWN:
                self.down = True
                self.last_mousedown_over = True
                self.callbacks['down'](event)

        # mouse up/down outside button => next up won't cause click
        elif event.type in (MOUSEBUTTONUP, MOUSEBUTTONDOWN):
            self.last_mousedown_over = False

        click = False

        if event.type == MOUSEBUTTONUP:
            if self.last_mousedown_over:
                click = True
            self.last_mousedown_over = False

            if self.down:
                self.down = False
                self.callbacks['up'](event)

            if click:
                self.down = False
                self.callbacks['click'](event)

        if exited:
            self.callbacks['exit'](event)
