# -*- coding: utf-8 -*-

from types import SimpleNamespace

import pygame as pg

# game settings
HEIGHT = 768
WIDTH = 1024
card_width = 63 * 3
card_height = 88 * 3
TITLE = "Ontogenesis"
FULLSCREEN = False
SYSTEM_DEBUG = True

# keybinds
keybinds = {
    # system
    'quit': [pg.K_ESCAPE],
    'next': [pg.K_RETURN],
    'toggle music': [pg.K_F2],
    'toggle fps cap': [pg.K_F8],
    'toggle fullscreen': [pg.K_F10],
    'toggle debug': [pg.K_F12],

    # menu
    'pause': [pg.K_p],
    'view skills': [pg.K_k],
    'view map': [pg.K_m],
    'view controls': [pg.K_c],
    'display bonuses': [pg.K_9],

    # cheat
    'cheat - travel': [pg.K_F9],
    'cheat - kill mobs': [pg.K_0],

    # player
    'move up': [pg.K_UP, pg.K_w],
    'move down': [pg.K_DOWN, pg.K_s],
    'move left': [pg.K_LEFT, pg.K_a],
    'move right': [pg.K_RIGHT, pg.K_d],
    'use skill - melee': [pg.K_SPACE],
    'use skill - movement': [pg.K_LCTRL],
    'switch focus skill': [pg.K_PAGEDOWN],
    'switch focus bonus': [pg.K_PAGEUP],
    # 'fire': []

    # test format
    # 'down': {
    #     'category': 'movement',
    #     'binds': [pg.K_DOWN, pg.K_s],
    # }
}

# define some colors as (R, G, B) tuples
colors = SimpleNamespace(
    white=(255, 255, 255),
    black=(0, 0, 0),
    darkgrey=(40, 40, 40),
    lightgrey=(100, 100, 100),
    green=(0, 255, 0),
    red=(255, 0, 0),
    yellow=(255, 255, 0),
    brown=(106, 55, 5),
    cyan=(0, 255, 255),
    blue=(0, 0, 255),
    orange=(255, 165, 0)
)

# configs
game_configs = SimpleNamespace(
    control_scheme='4d',
    fps=60,
    show_fps=True,
    debug=False,
    debug_exclude=['Wall'],
    flash_messages_queuesize=2,
    messages_queuesize=6,
    ui_button_text_color=colors.white,
    ui_button_text_size=32,
)

# map settings
BGCOLOR = colors.darkgrey
TILESIZE = 32
MAP_HEIGHT = 30
MAP_WIDTH = 60
safe_spawn_dist = 300
cluster_dist = 20
pack_size = 3
minimap_width = 150
minimap_height = 150

# Layers
layers = SimpleNamespace(
    wall=1,
    player=2,
    projectile=3,
    mob=2,
    ui=4
    # effects=4,
    # items=1,
)
