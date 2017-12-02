from types import SimpleNamespace

# game settings
HEIGHT = 768
WIDTH = 1024
TITLE = "Ontogenesis"
FULLSCREEN = False
SYSTEM_DEBUG = True

# configs
game_configs = SimpleNamespace(
    show_fps=True,
    debug=True,
    debug_exclude=['Wall'],
    flash_messages_queuesize=2
)

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
    cyan=(0, 255, 255)
)

# map settings
BGCOLOR = colors.darkgrey
TILESIZE = 32
MAP_HEIGHT = 100
MAP_WIDTH = 100

# Layers
layers = SimpleNamespace(
    wall=1,
    player=2,
    bullet=3,
    mob=2,
    effects=4,
    items=1,
)
