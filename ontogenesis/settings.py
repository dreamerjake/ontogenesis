# -*- coding: utf-8 -*-

from types import SimpleNamespace

import pygame as pg

# game settings
HEIGHT = 768
WIDTH = 1024
TITLE = "Ontogenesis"
FULLSCREEN = False
SYSTEM_DEBUG = True

# keybinds
keybinds = {
    pg.K_ESCAPE: 'test_keyfunction',
    pg.K_SPACE: 'test_keyfunction'
    # 'forwards': [pg.K_UP, pg.K_w]
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
    ui_button_text_color=colors.white,
    ui_button_text_size=32
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
    # bullet=3,
    mob=2,
    ui=3
    # effects=4,
    # items=1,
)
