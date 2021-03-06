# -*- coding: utf-8 -*-

from collections import defaultdict
from functools import wraps
from itertools import chain

import pygame as pg
from pygame.locals import MOUSEMOTION, MOUSEBUTTONUP, MOUSEBUTTONDOWN, SRCALPHA
from pygame.math import Vector2 as Vec2

import settings
from enemy import Mob
from helpers import get_font_height, calc_dist, render_outlined_text
from map import Wall
from settings import colors, layers, keybinds


def menu(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self.hide_group(self.all_buttons, self.all_windows)
        self.screen.fill(colors.black)
        func(self, *args, **kwargs)
        self.draw_menu_title()
        self.optional_messages()
        if self.game.configs.debug:
            self.debug_messages()
        self.update_visible_elements()
        self.draw_visible_elements()
        self.draw_flashed_messages()
        pg.display.flip()

    return wrapper


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

        # hud
        self.minimap = Minimap(self.game)

        # element group - buttons
        self.all_buttons = set()
        self.main_menu_buttons = set()

        # element group - windows
        self.all_windows = set()
        self.controls_menu_windows = set()
        self.map_menu_windows = set()
        self.skill_menu_windows = set()
        self.character_creation_windows = set()

        self.skills_album = None

    def create_elements(self):
        """ make all the button and window objects and their corresponding groups"""
        # buttons
        start_button = ImageButton(
            self.game, settings.WIDTH // 2, 100,
            groups=[self.all_buttons, self.main_menu_buttons],
            up_img=self.game.button_up,
            down_img=self.game.button_down,
            highlight_img=self.game.button_hover,
            caption='Start')
        start_button.callbacks['click'] = lambda x: self.game.fsm('new_game')

        load_button = ImageButton(
            self.game, settings.WIDTH // 2, 200,
            groups=[self.all_buttons, self.main_menu_buttons],
            up_img=self.game.button_up,
            down_img=self.game.button_down,
            highlight_img=self.game.button_hover,
            caption='Load')
        # start_button.callbacks['click'] = lambda x: self.game.fsm('new_game')

        stats_button = ImageButton(
            self.game, settings.WIDTH // 2, 300,
            groups=[self.all_buttons, self.main_menu_buttons],
            up_img=self.game.button_up,
            down_img=self.game.button_down,
            highlight_img=self.game.button_hover,
            caption='Stats')
        # start_button.callbacks['click'] = lambda x: self.game.fsm('new_game')

        hall_button = ImageButton(
            self.game, settings.WIDTH // 2, 400,
            groups=[self.all_buttons, self.main_menu_buttons],
            up_img=self.game.button_up,
            down_img=self.game.button_down,
            highlight_img=self.game.button_hover,
            caption='Hall of Fame')
        # start_button.callbacks['click'] = lambda x: self.game.fsm('new_game')

        settings_button = ImageButton(
            self.game, settings.WIDTH // 2, 500,
            groups=[self.all_buttons, self.main_menu_buttons],
            up_img=self.game.button_up,
            down_img=self.game.button_down,
            highlight_img=self.game.button_hover,
            caption='Settings')
        # settings_button.callbacks['click'] = lambda x: self.game.fsm('new_game')

        quit_button = ImageButton(
            self.game, settings.WIDTH // 2, 600,
            groups=[self.all_buttons, self.main_menu_buttons],
            up_img=self.game.button_up,
            down_img=self.game.button_down,
            highlight_img=self.game.button_hover,
            caption='Quit')
        quit_button.callbacks['click'] = lambda x: self.game.quit()

        reset_button = ImageButton(
            self.game, 50, settings.HEIGHT - 50,
            groups=[self.all_buttons, self.main_menu_buttons],
            up_img=self.game.button_up,
            down_img=self.game.button_down,
            highlight_img=self.game.button_hover,
            caption='Reset',
            resize=(150, 44),
            align='midleft')
        # quit_button.callbacks['click'] = lambda x: self.game.quit()

        credits_button = ImageButton(
            self.game, settings.WIDTH - 50, settings.HEIGHT - 50,
            groups=[self.all_buttons, self.main_menu_buttons],
            up_img=self.game.button_up,
            down_img=self.game.button_down,
            highlight_img=self.game.button_hover,
            caption='Credits',
            resize=(150, 44),
            align='midright')
        # quit_button.callbacks['click'] = lambda x: self.game.quit()

        # windows
        # keybinds window
        TextScrollwindow(
            self.game,
            [self.all_windows, self.controls_menu_windows],
            settings.WIDTH - 100, settings.HEIGHT - 150,
            (50, 100),
            [k for k in keybinds.keys()],
            [', '.join([pg.key.name(button) for button in v]) for v in keybinds.values()],
            self.game.settings_font, 28)

        # skill cards window
        self.skills_album = CardAlbum(cards=[skill.get_card() for skill in self.game.player.all_skills])
        ScrollableSurface([self.all_windows, self.skill_menu_windows], (settings.WIDTH - 100, settings.card_height * 2 + 15), (50, 100), self.skills_album.image, album=self.skills_album)

    def draw_menu_title(self):
        title = self.game.fsm.current_state
        title = title.replace('_', ' ').upper()
        self.draw_text(title, self.game.hud_font, 32, colors.white, settings.WIDTH // 2, 20, align='center')
        # self.start_button.draw(self.screen)

    def draw_fps(self):
        fps = self.game.clock.get_fps()
        fps = str(int(fps)) if fps != float('inf') else 'inf'
        fps = "FPS: {}".format(fps)
        self.draw_text(fps, self.game.hud_font, 18, colors.white, 5, 5, align='topleft')

    def draw_state(self):
        state = self.game.fsm.current_state
        self.draw_text(state, self.game.hud_font, 18, colors.white, settings.WIDTH - 5, 25, align='topright')

    def draw_mobcount(self):
        mobcount = len(self.game.mobs)
        self.draw_text('Mobs Remaining: {}'.format(mobcount), self.game.hud_font, 18, colors.white, settings.WIDTH - 5, 45, align='topright')

    def draw_food(self):
        food = int(self.game.player.food)
        color = colors.white if food > 30 else colors.orange
        if not food: color = colors.red
        self.draw_text('Food Remaining: {}'.format(food), self.game.hud_font, 18, color, settings.WIDTH - 5, 65, align='topright')

    def draw_debug_warning(self):
        self.draw_text('DEBUG MODE', self.game.hud_font, 18, colors.white, settings.WIDTH - 5, 5, align='topright')

    def draw_messages(self):
        if self.game.message_queue:
            size = 24
            height = get_font_height(pg.font.Font(self.game.hud_font, size))
            y_offset = 525
            x_offset = 5
            for i, message in enumerate(self.game.message_queue.getall()):
                # print(len(message), message[0])
                text, color = message
                self.draw_text(text, self.game.hud_font, size, color, x_offset, i * height + y_offset)

    def draw_flashed_messages(self):
        for i, message in enumerate(self.game.message_flash_queue.get()[::-1]):
            height = pg.font.Font(self.game.message_flash_font, 40).size(message)[1]
            offset = i * height
            self.draw_outlined_text(
                message,
                self.game.message_flash_font,
                40,
                colors.yellow,
                colors.black,
                settings.WIDTH / 2,
                settings.HEIGHT / 2 - settings.HEIGHT * .10 - offset,
                align='center')

    def draw_active_skill(self):
        skill_name = self.game.player.equipped['active_skill'].name
        self.draw_text(skill_name, self.game.settings_font, 24, colors.white, 25, settings.HEIGHT - 25, align='bottomleft')

    def draw_focus_skill(self):
        if self.game.player.focus_skill:
            skill_name = self.game.player.focus_skill.name
            skill_focus = self.game.player.focus_skill.focus
            if skill_focus:
                if self.game.player.focus_skill.passive:
                    skill_focus_val = int(self.game.player.focus_skill.bonuses[skill_focus])
                else:
                    skill_focus_val = int(getattr(self.game.player.focus_skill, skill_focus))
            else:
                skill_focus_val = 'None'

            desc = '{} {} {}'.format(skill_name, skill_focus, skill_focus_val)
        else:
            desc = 'NO FOCUS SKILL'
        self.draw_text(desc, self.game.settings_font, 24, colors.white, settings.WIDTH // 2, settings.HEIGHT - 25, align='midbottom')

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

        # resource globe
        # TODO: cleanup the variables here
        if self.game.player.resource_current < self.game.player.equipped['active_skill'].cost:
            full_img = self.game.mana_full_blink_img
            empty_img = self.game.mana_empty_blink_img
        else:
            full_img = self.game.mana_full_img
            empty_img = self.game.mana_empty_img
        resource_pct = self.game.player.resource_current / self.game.player.resource_max
        height = int(full_img.get_height() * resource_pct)
        current_img = pg.Surface((full_img.get_width(), height), SRCALPHA)
        current_img.fill((0, 0, 0, 0))
        extra_h = 0 - (full_img.get_height() - height)
        current_img.blit(full_img, (0, extra_h))
        spacer = 20
        self.screen.blit(empty_img, (settings.WIDTH - empty_img.get_width() - spacer, settings.HEIGHT - empty_img.get_height() - spacer))
        self.screen.blit(current_img, (settings.WIDTH - full_img.get_width() - spacer, settings.HEIGHT - current_img.get_height() - spacer))

    @staticmethod
    def hide_group(*groups):
        for group in groups:
            for member in group:
                member.visible = False

    @staticmethod
    def show_group(*groups):
        for group in groups:
            for member in group:
                member.visible = True

    def draw_visible_elements(self):
        for button in self.all_buttons:
            if button.visible:
                button.draw(self.screen)

        for window in self.all_windows:
            if window.visible:
                window.draw(self.screen)

    def update_visible_elements(self):
        for button in self.all_buttons:
            if button.visible:
                button.update()

        for window in self.all_windows:
            if window.visible:
                window.update()

    @menu
    def draw_character_creation_menu(self):
        # skill lists
        passive = [skill for skill in self.game.starting_skills if skill.passive]
        move = [skill for skill in self.game.starting_skills if 'movement' in skill.tags]
        melee = [skill for skill in self.game.starting_skills if 'melee' in skill.tags]
        primary = [skill for skill in self.game.starting_skills if 'primary' in skill.tags]

        # skill albums
        rescale = int(settings.card_width / 2), int(settings.card_height / 2)
        passive_album = CardAlbum(cards=[skill.get_card(use_small=True) for skill in passive], num_rows=1)
        move_album = CardAlbum(cards=[skill.get_card(use_small=True) for skill in move], num_rows=1)
        melee_album = CardAlbum(cards=[skill.get_card(use_small=True) for skill in melee], num_rows=1)
        primary_album = CardAlbum(cards=[skill.get_card(use_small=True) for skill in primary], num_rows=1)
        skill_albums = [primary_album, melee_album, move_album, passive_album]

        # scrollable windows
        for i, album in enumerate(skill_albums):
            ScrollableSurface([self.all_windows, self.character_creation_windows], (settings.WIDTH - 100, album.image.get_height()), (50, i * album.image.get_height() + 50), album.image, album=album)

        self.show_group(self.character_creation_windows)

    @menu
    def draw_controls_menu(self):
        self.show_group(self.controls_menu_windows)

    @menu
    def draw_main_menu(self):
        self.show_group(self.main_menu_buttons)

    @menu
    def draw_pause_menu(self):
        pass

    def draw_info_skill(self):
        self.hide_group(self.all_buttons, self.all_windows)

        self.screen.fill(colors.black)
        self.draw_text('SKILL DETAIL', self.game.hud_font, 48, colors.white, settings.WIDTH // 2, settings.HEIGHT // 2, align='center')
        self.draw_menu_title()
        self.optional_messages()
        if self.game.configs.debug:
            self.debug_messages()
        self.draw_flashed_messages()
        pg.display.flip()

    @menu
    def draw_skills_menu(self):
        self.show_group(self.skill_menu_windows)
        self.skills_album.update(new_cards=[skill.get_card() for skill in self.game.player.all_skills])
        for win in self.skill_menu_windows:
            win.new(self.skills_album.image)

    @menu
    def draw_map_menu(self):
        self.show_group(self.map_menu_windows)
        self.screen.blit(self.game.worldmap.image, (100, 100))

        # draw edges
        for edge in self.game.worldmap.graph.edges():
            start_pos = self.game.worldmap.get_node_pos(edge[0])
            end_pos = self.game.worldmap.get_node_pos(edge[1])
            current_reachable = list(self.game.worldmap.graph.neighbors(self.game.worldmap.current_node)) + [self.game.worldmap.current_node]
            #  pg.draw.line(self.screen, colors.cyan, start_pos, end_pos, 4)  # line width
            if self.game.worldmap.graph.node[edge[0]]['discovered'] and self.game.worldmap.graph.node[edge[1]]['discovered']:
                pg.draw.line(self.screen, colors.blue, start_pos, end_pos, 4)  # line blend
            if edge[0] in current_reachable and edge[1] in current_reachable and (edge[0] == self.game.worldmap.current_node or edge[1] == self.game.worldmap.current_node):
                pg.draw.line(self.screen, colors.red, start_pos, end_pos, 4)  # line blend

        # draw nodes
        for node, data in self.game.worldmap.graph.nodes(data=True):
            # print(node)
            # node_pos = (int(self.game.worldmap.current_node[0] * self.game.worldmap.scalex + 100), int(self.game.worldmap.current_node[1] * self.game.worldmap.scaley + 100))
            # node_pos = int(node[0] * self.game.worldmap.scalex) + 100 + int(self.game.worldmap.scalex / 2), int(node[1] * self.game.worldmap.scaley) + 100 + int(self.game.worldmap.scaley / 2)
            node_pos = self.game.worldmap.get_node_pos(node)
            if data['goal']:
                pg.draw.circle(self.screen, colors.orange, node_pos, 20, 10)
            if data['visited']:
                pg.draw.circle(self.screen, colors.blue, node_pos, 10, 5)
            elif data['discovered']:
                pg.draw.circle(self.screen, colors.yellow, node_pos, 10, 5)

        # current and destination nodes
        current_node_pos = int(self.game.worldmap.current_node[0] * self.game.worldmap.scalex) + 100 + int(self.game.worldmap.scalex / 2), int(self.game.worldmap.current_node[1] * self.game.worldmap.scaley) + 100 + int(self.game.worldmap.scaley / 2)
        pg.draw.circle(self.screen, colors.red, current_node_pos, 20, 10)
        if self.game.worldmap.destination_node:
            destination_node_pos = int(self.game.worldmap.destination_node[0] * self.game.worldmap.scalex) + 100 + int(
                self.game.worldmap.scalex / 2), int(
                self.game.worldmap.destination_node[1] * self.game.worldmap.scaley) + 100 + int(
                self.game.worldmap.scaley / 2)
            pg.draw.circle(self.screen, colors.green, destination_node_pos, 20, 10)

    @menu
    def draw_game_over(self):
        self.draw_text('YOU DIED.', self.game.hud_font, 48, colors.white, settings.WIDTH // 2, settings.HEIGHT // 2, align='center')

    @menu
    def draw_placeholder_menu(self, name):
        self.draw_text(name, self.game.hud_font, 48, colors.white, settings.WIDTH // 2, settings.HEIGHT // 2, align='center')

    @menu
    def draw_placeholder_splash(self, name, text=None):
        self.draw_text(name, self.game.hud_font, 48, colors.white, settings.WIDTH // 2, settings.HEIGHT // 2 - 50, align='center')
        if text:
            for i, line in enumerate(text):
                self.draw_text(line, self.game.hud_font, 32, colors.white, settings.WIDTH // 2, settings.HEIGHT // 2 + (i * 32),
                               align='center')

    def draw_icon_bar(self):
        spacer = 12
        font = pg.font.Font(self.game.hud_font, 24)
        font.set_bold(True)
        font_height = get_font_height(font)
        icon_size = self.game.configs.icon_size
        surface = pg.Surface((spacer * 4 + icon_size * 3, spacer * 2 + font_height + icon_size))
        surface.fill(colors.lightgrey)
        highlight_size = 2
        highlight = pg.Surface((highlight_size * 2 + icon_size, highlight_size * 2 + icon_size))
        highlight.fill(colors.red)

        skills = [
            self.game.player.equipped['active_skill'],
            self.game.player.equipped['melee_skill'],
            self.game.player.equipped['move_skill'],
        ]
        for i, skill in enumerate(skills):
            x = icon_size * i + spacer * (i + 1)
            y = spacer + font_height
            if not skill.can_fire:
                surface.blit(highlight, (x - highlight_size, y - highlight_size))
            surface.blit(skill.icon, (x, y))

        names = ['ACTIVE', 'MELEE', 'MOVE']
        for i, name in enumerate(names):
            text = font.render(name, True, colors.red)
            text_rect = text.get_rect()
            text_rect.center = (icon_size * (i + .5) + spacer * (i + 1), (spacer + font_height) // 2)
            surface.blit(text, text_rect)

        surface_rect = surface.get_rect()
        surface_rect.midbottom = settings.WIDTH // 2, settings.HEIGHT - 5
        self.screen.blit(surface, surface_rect)

    def draw_hud(self):
        self.hide_group(self.all_buttons, self.all_windows)

        health_pct = self.game.player.hp_current / self.game.player.hp_max
        self.draw_player_health(5, 25, health_pct)
        self.draw_mobcount()
        self.draw_food()

        # self.draw_active_skill()
        # self.draw_focus_skill()
        self.draw_icon_bar()

        self.draw_messages()
        self.optional_messages()
        if self.game.configs.debug:
            self.debug_messages()
        self.draw_flashed_messages()

    def debug_messages(self):
        self.draw_debug_warning()
        # game fsm state
        self.draw_state()

    def optional_messages(self):
        # fps
        if self.game.configs.show_fps:
            self.draw_fps()

    def draw_text(self, text, font_name, size, color, x, y, align="topleft"):
        font = pg.font.Font(font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(**{align: (x, y)})
        self.screen.blit(text_surface, text_rect)

    def draw_outlined_text(self, text, font_name, size, color, outline_color, x, y, align="topleft"):
        font = pg.font.Font(font_name, size)
        text_surface = font.render(text, True, color)
        final_surface = text_surface.copy()
        outline_surface = font.render(text, True, outline_color)
        for point in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            final_surface.blit(outline_surface, point)
        final_surface.blit(text_surface, (0, 0))
        final_rect = final_surface.get_rect(**{align: (x, y)})
        self.screen.blit(final_surface, final_rect)


class Minimap(pg.sprite.Sprite):
    def __init__(self, game):
        self._layer = layers.ui
        self.groups = game.hud
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        # self.rect = pg.Rect((settings.minimap_width, settings.minimap_height))
        self.image = pg.Surface((settings.minimap_width, settings.minimap_height), SRCALPHA)
        self.image.fill((0, 0, 0, 80))
        self.rect = self.image.get_rect()
        self.rect.topright = (settings.WIDTH - 50, 100)

        self.scalex = self.game.screensize[0] / self.rect.width
        self.scaley = self.game.screensize[1] / self.rect.height

    def update(self):
        # clear to a low-alpha rectangle
        self.image.fill((0, 0, 0, 80))

        sizex = self.rect.width / 30
        sizey = self.rect.height / 30  # magic number for now

        self.offscreen_mob_dirs = set()
        # draw non-player things
        for sprite in chain(self.game.walls, self.game.mobs):
            pos = self.game.camera.apply(sprite)
            player_pos = self.game.camera.apply(self.game.player, hit_rect=True)
            dist = calc_dist(pos, player_pos)
            if dist < self.game.player.vision_radius:
                color = colors.brown if isinstance(sprite, Wall) else colors.red
                self.image.fill(color, [pos[0] / self.scalex, pos[1] / self.scaley, sizex, sizey])
            elif isinstance(sprite, Mob):
                x = 'left' if player_pos.x > pos.x else 'right'
                y = 'up' if player_pos.y > pos.y else 'down'
                self.offscreen_mob_dirs.add(x)
                self.offscreen_mob_dirs.add(y)

        # print(offscreen_mob_dirs)

        # draw player
        # TODO: icon for player location?
        player_pos = self.game.camera.apply(self.game.player, hit_rect=True)
        self.image.fill(colors.green, [
            player_pos[0] / self.scalex,
            player_pos[1] / self.scaley,
            sizex,
            sizey])

    def draw(self, screen):
        bordered = add_border(self.image, 2, colors.white)
        extra_border = 0
        if len(self.offscreen_mob_dirs) < 3:
            extra_border = 12
            bordered = add_border(bordered, 4, colors.yellow, sides=self.offscreen_mob_dirs)
            bordered = add_border(bordered, 4, colors.orange, sides=self.offscreen_mob_dirs)
            bordered = add_border(bordered, 4, colors.red, sides=self.offscreen_mob_dirs)
        # bordered.set_alpha(40)
        x, y = self.rect.topleft
        screen.blit(bordered, (x - extra_border, y - extra_border))


class ImageButton:

    def __init__(self, game, x, y, groups, up_img, down_img, highlight_img, caption='', font=None, resize=None, align='center'):

        # check for mismatched image sizes
        if up_img.get_size() != down_img.get_size() != highlight_img.get_size():
            raise Exception('Button surfaces must all be the same size')

        self.game = game

        for group in groups:
            group.add(self)

        self.up_img = up_img.copy()
        self.down_img = down_img.copy()
        self.highlight_img = highlight_img.copy()

        if resize:
            self.up_img = pg.transform.scale(self.up_img, resize)
            self.down_img = pg.transform.scale(self.down_img, resize)
            self.highlight_img = pg.transform.scale(self.highlight_img, resize)

        self.width, self.height = self.up_img.get_size()

        # self.rect = pg.Rect(x - self.width // 2, y - self.height // 2, self.width, self.height)
        self.rect = self.up_img.get_rect()
        setattr(self.rect, align, (x, y))

        self.caption = caption
        self.font = pg.font.Font(font, self.game.configs.ui_button_text_size)

        self.visible = True
        self.down = False
        self.mouseover = False
        self.last_mousedown_over = False

        caption_surface = self.font.render(self.caption, True, self.game.configs.ui_button_text_color)
        # self.caption_rect = self.caption_surface.get_rect()
        # self.caption_rect.center = self.width // 2, self.height // 2

        # outline caption text
        final_surface = caption_surface.copy()
        outline_surface = self.font.render(self.caption, True, colors.black)
        for point in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            final_surface.blit(outline_surface, point)
        final_surface.blit(caption_surface, (0, 0))
        final_rect = final_surface.get_rect()
        final_rect.center = self.width // 2, self.height // 2

        for image in [self.up_img, self.down_img, self.highlight_img]:
            image.blit(final_surface, final_rect)

        self.callbacks = defaultdict(lambda: lambda event: None)

    def update(self):
        pass

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
                self.game.button_sound.play()
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


class TextScrollwindow(pg.sprite.Sprite):
    def __init__(self, game, groups, width, height, pos, content_left, content_right, font_path, font_size):
        # pygame sprite stuff
        # self._layer = layers.ui
        # self.groups = game.ui_elements
        pg.sprite.Sprite.__init__(self)  # , self.groups)

        # object references
        self.game = game

        for group in groups:
            group.add(self)

        self.content_left = content_left
        self.content_right = content_right
        self.index = 0
        self.highlight_index = None
        self.items_per_screen = 1

        self.visible = True
        self.font = pg.font.Font(font_path, font_size)
        self.bg_color = colors.lightgrey
        self.text_color = colors.white
        self.highlight_color = colors.yellow
        self.text_border_color = colors.black

        self.width = width
        self.height = height
        self.image = pg.Surface((width, height))
        self.image.fill(self.bg_color)
        self.rect = self.image.get_rect()
        self.rect.topleft = pos

        self.button_up = self.image.subsurface(pg.Rect(self.width - 30, 0, 30, 50))
        self.button_down = self.image.subsurface(pg.Rect(self.width - 30, self.height - 50, 30, 50))

    def highlight(self):
        mousex, mousey = pg.mouse.get_pos()
        collision = self.rect.collidepoint((mousex, mousey))
        if collision:
            item_height = self.height // self.items_per_screen
            x, y = self.rect.topleft
            i = (mousey - y) // item_height
            self.highlight_index = i + self.index

    def handle_event(self, event):
        # left click
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            self.highlight()
            button_up_relative_pos = Vec2(event.pos) - Vec2(self.button_up.get_abs_offset()) - Vec2(self.rect.topleft)
            button_down_relative_pos = Vec2(event.pos) - Vec2(self.button_down.get_abs_offset()) - Vec2(self.rect.topleft)
            if self.button_up.get_rect().collidepoint(button_up_relative_pos):
                print('button up clicked')
                if self.index < len(self.content_left) - self.items_per_screen:
                    self.index += 1
            if self.button_down.get_rect().collidepoint(button_down_relative_pos):
                print('button down clicked')
                if self.index:
                    self.index -= 1

        # scroll wheel up
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 4:
            if self.index:
                self.index -= 1
        # scroll wheel down
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 5:
            if self.index < len(self.content_left) - self.items_per_screen:
                self.index += 1

    def update(self, new_content_left=None, new_content_right=None):
        if new_content_left:
            self.content_left = new_content_left
        if new_content_right:
            self.content_right = new_content_right

        self.image.fill(self.bg_color)

        # update content
        # render_list_left = [self.font.render(item, 1, self.text_color) for item in self.content_left][self.index:]
        # render_list_right = [self.font.render(item, 1, self.text_color) for item in self.content_right][self.index:]
        render_list_left = [render_outlined_text(item, self.font, colors.white, colors.black) for item in self.content_left][self.index:]
        render_list_right = [render_outlined_text(item, self.font, colors.white, colors.black) for item in self.content_right][self.index:]
        if render_list_left or render_list_right:
            max_height = max([item.get_height() for item in render_list_left] + [item.get_height() for item in render_list_right])
            self.items_per_screen = self.height // max_height

            for i, item in enumerate(zip(render_list_left, render_list_right)):
                if self.index + i == self.highlight_index:
                    tmp = pg.Surface((self.width - 30, item[0].get_height()))  # magic number button width
                    tmp.convert_alpha()
                    tmp.fill(colors.yellow)
                    tmp.blit(item[0], (5, 0))
                    tmp.blit(item[1], (self.width - item[1].get_width() - 30 - 5, 0))
                    self.image.blit(tmp, (0, i * max_height))
                else:
                    tmp = pg.Surface((self.width - 30, item[0].get_height()))  # magic number button width
                    tmp.convert_alpha()
                    tmp.fill(self.bg_color)
                    tmp.blit(item[0], (5, 0))
                    tmp.blit(item[1], (self.width - item[1].get_width() - 30 - 5, 0))
                    self.image.blit(tmp, (0, i * max_height))

        self.button_up.fill(colors.darkgrey)
        self.button_down.fill(colors.darkgrey)

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class ScrollableSurface(pg.Surface):
    def __init__(self, groups, size, pos, sub_surface, scroll_speed=7, scroll_area=50, album=None):  # scrolling=['x', 'y', 'xy']
        pg.Surface.__init__(self, size)

        for group in groups:
            group.add(self)

        self.pos = pos
        self.scroll_speed = scroll_speed
        self.visible = False
        self.sub_surface = sub_surface
        self.album = album

        self.x_offset = 0
        self.y_offset = 0

        # self.upper_rect = pg.Rect(0, 0, size[0], scroll_area)
        # self.lower_rect = pg.Rect(0, size[1] - scroll_area, size[0], scroll_area)
        self.left_rect = pg.Rect(0, 0, scroll_area, size[1])
        self.right_rect = pg.Rect(size[0] - scroll_area, 0, scroll_area, size[1])

    def new(self, new_surface):
        self.sub_surface = new_surface

    def handle_event(self, event):
        pass

    def update(self):
        (x, y) = self.pos
        (mx, my) = pg.mouse.get_pos()
        # print(self.pos, (mx, my))
        album_relative_pos = (mx - x, my - y)

        if self.album:
            for skill_card, skill_card_rect in self.album.card_rects.items():
                if skill_card_rect.collidepoint(album_relative_pos):
                    cx, cy = skill_card_rect.topleft
                    ax, ay = album_relative_pos
                    card_relative_pos = (ax - cx, ay - cy)
                    # print(skill_card.clickables.items())
                    for name, props in skill_card.clickables.items():
                        if props['rect'].collidepoint(card_relative_pos):
                            clickable = name
                            callback = props['callback']
                            callback_args = props['callback_args']
                            break
                    else:
                        clickable = f'SkillCard {skill_card.skill.name} background'
                        callback = None
                    # print(f'Mouse is over SkillCard for skill {skill_card.skill.name} at {card_relative_pos}, clickable: {clickable}')
                    if pg.mouse.get_pressed()[0]:
                        print(f'Clicked {clickable}')
                        if 'background' in clickable:
                            if skill_card.clickables:
                                skill_card.game.player.focus_skill = skill_card.skill
                            else:
                                skill_card.game.flash_message('Cannot focus: no mods unlocked', 2)
                        else:
                            skill_card.game.player.focus_skill = skill_card.skill
                            callback(callback_args) if callback else print('No callback')

        max_x_offset = self.sub_surface.get_width() - self.get_width()

        # scroll horizontal left
        if self.left_rect.collidepoint(album_relative_pos) and self.x_offset != 0:
            self.x_offset += self.scroll_speed
            self.x_offset = min(self.x_offset, 0)
            print('scrolling left')

        # max offset check

        # scroll horizontal right
        if self.right_rect.collidepoint(album_relative_pos) and -self.x_offset < max_x_offset:
            self.x_offset -= self.scroll_speed
            self.x_offset = -max_x_offset if -self.x_offset > max_x_offset and self.x_offset < 0 else self.x_offset
            print('scrolling right')

        # max offset check

    def draw(self, surface):
        self.blit(self.sub_surface, (self.x_offset, self.y_offset))
        # self.fill(colors.yellow)
        surface.blit(self, self.pos)

    # def get_mouseover_card(self, cards):
    #
    #     for i, card in enumerate(cards):


class CardAlbum:
    def __init__(self, cards, num_rows=2, spacer_x=5, spacer_y=5):  # , rescale=None):
        self.cards = cards

        self.num_rows = num_rows
        self.spacer_x = spacer_x
        self.spacer_y = spacer_y

        self.card_width = None
        self.card_height = None
        # if rescale:
        #     self.card_width, self.card_height = rescale

        self.image = None
        self.card_rects = {}
        self.update(self.cards)

    def __len__(self):
        return len(self.cards)

    def update(self, new_cards):
        if new_cards:
            self.cards = new_cards
            # print('Skills card album now contains {} cards'.format(len(new_cards)))
        for card in self.cards:
            card.update()

        self.card_width = self.cards[0].image.get_width() if not self.card_width else self.card_width
        self.card_height = self.cards[0].image.get_height() if not self.card_height else self.card_height
        num_cards = len(self)
        cards_in_row = num_cards // self.num_rows
        if num_cards % 2 != 0:
            cards_in_row += 1

        spacer_width = self.spacer_x * (cards_in_row + 1)
        cards_width = self.card_width * cards_in_row
        spacer_height = self.spacer_y * (self.num_rows + 1)
        cards_height = self.card_height * self.num_rows
        self.image = pg.Surface((spacer_width + cards_width, spacer_height + cards_height))
        self.image.fill(colors.lightgrey)

        self.card_rects = {}

        for i, card in enumerate(self.cards):
            x = i % cards_in_row
            y = i // cards_in_row
            top = self.spacer_y * (y + 1) + (self.card_height * y)
            left = self.spacer_x * (x + 1) + (self.card_width * x)
            # card_image = pg.transform.scale(card.image, (self.card_width, self.card_height))
            self.image.blit(card.image, (left, top))
            self.card_rects[card] = pg.Rect(left, top, self.card_width, self.card_height)


def add_border(surface, thickness, color, sides=None):
    if not sides:
        new_surface = pg.Surface((2 * thickness + surface.get_width(), 2 * thickness + surface.get_height()))
        new_surface.fill(color)
        new_surface.fill((0, 0, 0, 0), surface.get_rect(topleft=(thickness, thickness)))
        new_surface.blit(surface, (thickness, thickness))
        return new_surface
    else:
        new_surface = pg.Surface((2 * thickness + surface.get_width(), 2 * thickness + surface.get_height()))
        # new_surface.fill((0, 0, 0, 0))
        border = surface.copy()
        border.fill(color)
        border_rect = border.get_rect()
        if 'right' in sides:
            tmp_rect = border_rect.copy()
            tmp_rect.x += 2 * thickness
            tmp_rect.y += thickness
            new_surface.blit(border, tmp_rect)
        if 'left' in sides:
            tmp_rect = border_rect.copy()
            # border_rect.x += 2 * thickness
            tmp_rect.y += thickness
            new_surface.blit(border, tmp_rect)
        if 'up' in sides:
            tmp_rect = border_rect.copy()
            tmp_rect.x += thickness
            # border_rect.y += thickness
            new_surface.blit(border, tmp_rect)
        if 'down' in sides:
            tmp_rect = border_rect.copy()
            tmp_rect.x += thickness
            tmp_rect.y += 2 * thickness
            new_surface.blit(border, tmp_rect)
        new_surface.fill((0, 0, 0, 0), surface.get_rect(topleft=(thickness, thickness)))

        new_surface.blit(surface, (thickness, thickness))
        return new_surface
