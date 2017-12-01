from types import SimpleNamespace

# game settings
HEIGHT = 768
WIDTH = 1024
TITLE = "Ontogenesis"
FULLSCREEN = False

# configs
SHOW_FPS = True
DEBUG = True

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
    cyan=(0, 255, 255))

# map settings
BGCOLOR = colors.darkgrey
TILESIZE = 32
MAP_HEIGHT = 100
MAP_WIDTH = 100

# Layers
WALL_LAYER = 1
PLAYER_LAYER = 2
BULLET_LAYER = 3
MOB_LAYER = 2
EFFECTS_LAYER = 4
ITEMS_LAYER = 1
