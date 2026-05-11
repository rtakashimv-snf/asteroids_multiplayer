# ASTEROIDE MULTIPLAYER v2.0
# Shared math, drawing, and random helper utilities.

import math
from random import random, uniform
from typing import Iterable, Tuple

import pygame as pg

import config as C

Vec = pg.math.Vector2


def wrap_pos(pos: Vec) -> Vec:
    return Vec(pos.x % C.WIDTH, pos.y % C.HEIGHT)


def angle_to_vec(deg: float) -> Vec:
    rad = math.radians(deg)
    return Vec(math.cos(rad), math.sin(rad))


def rand_unit_vec() -> Vec:
    a = uniform(0, math.tau)
    return Vec(math.cos(a), math.sin(a))


def rand_edge_pos() -> Vec:
    if random() < 0.5:
        x = uniform(0, C.WIDTH)
        y = 0 if random() < 0.5 else C.HEIGHT
    else:
        x = 0 if random() < 0.5 else C.WIDTH
        y = uniform(0, C.HEIGHT)
    return Vec(x, y)


def draw_poly(surface: pg.Surface, pts: Iterable[Tuple[int, int]],
              color=None, width: int = 1):
    color = color or C.WHITE
    pg.draw.polygon(surface, color, list(pts), width=width)


def draw_circle(surface: pg.Surface, pos: Vec, r: int,
                color=None, width: int = 1):
    color = color or C.WHITE
    pg.draw.circle(surface, color, (int(pos.x), int(pos.y)), r, width=width)


def text(surface: pg.Surface, font: pg.font.Font, s: str, x: int, y: int,
         color=None, center: bool = False):
    color = color or C.WHITE
    surf = font.render(s, True, color)
    rect = surf.get_rect()
    if center:
        rect.centerx = x
        rect.top = y
    else:
        rect.topleft = (x, y)
    surface.blit(surf, rect)


def draw_ship_shape(surface: pg.Surface, pos: Vec, angle: float,
                    radius: int, color, invuln: float = 0.0, cls: int = 0):
    """Desenha o polígono da nave com visual diferente por classe."""
    dirv = angle_to_vec(angle)
    left  = angle_to_vec(angle + 140)
    right = angle_to_vec(angle - 140)
    p1 = pos + dirv * radius
    p2 = pos + left  * radius * 0.9
    p3 = pos + right * radius * 0.9

    if cls == 0:  # Classe A – triângulo normal
        pts = [p1, p2, p3]
    elif cls == 1:  # Classe B – triângulo com recuo central (mais agressivo)
        mid  = pos + dirv * (-radius * 0.3)
        pts  = [p1, p2, mid, p3]
    else:           # Classe C – triângulo aberto / disperso visual
        back = angle_to_vec(angle + 180)
        tail = pos + back * radius * 0.4
        pts  = [p1, p2, tail, p3]

    draw_poly(surface, pts, color)

    if invuln > 0 and int(invuln * 10) % 2 == 0:
        draw_circle(surface, pos, radius + 6, color, width=1)


def health_bar(surface: pg.Surface, cx: float, y: float,
               hp: int, max_hp: int, color):
    """Barra de HP pequena acima da nave."""
    w, h = 30, 4
    x = int(cx - w / 2)
    pg.draw.rect(surface, C.DIM, (x, y, w, h))
    filled = int(w * hp / max_hp)
    if filled > 0:
        pg.draw.rect(surface, color, (x, y, filled, h))
