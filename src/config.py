# ASTEROIDE MULTIPLAYER v3.0
WIDTH  = 1280
HEIGHT = 800
FPS    = 60

SHIP_RADIUS       = 15
SHIP_TURN_SPEED   = 220.0
SHIP_THRUST       = 220.0
SHIP_FRICTION     = 0.995
SHIP_FIRE_RATE    = 0.18
SHIP_BULLET_SPEED = 420.0
SHIP_MAX_HP       = 4

SPECIAL_HOLD_TIME = 1.2
BURST_BULLETS     = 5
BURST_INTERVAL    = 0.07
CHARGED_RADIUS    = 8
CHARGED_SPEED     = 380.0
SCATTER_COUNT     = 7
SCATTER_SPREAD    = 35.0

BULLET_RADIUS = 3
BULLET_TTL    = 1.1
MAX_BULLETS   = 8

AST_VEL_MIN = 35.0
AST_VEL_MAX = 100.0
AST_SIZES = {
    "L": {"r": 46, "score": 20,  "split": ["M", "M"]},
    "M": {"r": 24, "score": 50,  "split": ["S", "S"]},
    "S": {"r": 12, "score": 100, "split": []},
}

UFO_SPAWN_EVERY  = 20.0
UFO_SPEED        = 80.0
UFO_FIRE_EVERY   = 1.4
UFO_BULLET_SPEED = 240.0
UFO_BULLET_TTL   = 1.8
UFO_BIG   = {"r": 18, "score": 200,  "aim": 0.2}
UFO_SMALL = {"r": 12, "score": 1000, "aim": 0.6}

SAFE_SPAWN_TIME = 2.5
WAVE_DELAY      = 2.0

PLAYER_COLORS = [
    (100, 200, 255),
    (255, 120, 80),
    (100, 255, 130),
    (255, 220, 60),
]

WHITE = (240, 240, 240)
GRAY  = (120, 120, 120)
DIM   = (50,  50,  50)
BLACK = (0,   0,   0)

GAME_OVER_FADE_DURATION = 1.2
RANDOM_SEED = None
