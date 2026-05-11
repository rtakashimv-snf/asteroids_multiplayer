# ASTEROIDE MULTIPLAYER v3.0
# Entidades do jogo.

import math
from random import uniform
import pygame as pg
import config as C
from utils import (Vec, angle_to_vec, draw_circle, draw_poly,
                   wrap_pos, health_bar)


# ---------------------------------------------------------------------------
# Projéteis
# ---------------------------------------------------------------------------

class Bullet(pg.sprite.Sprite):
    def __init__(self, pos, vel, owner_id, color):
        super().__init__()
        self.pos   = Vec(pos)
        self.vel   = Vec(vel)
        self.ttl   = C.BULLET_TTL
        self.r     = C.BULLET_RADIUS
        self.owner = owner_id
        self.color = color
        self.rect  = pg.Rect(0, 0, self.r*2, self.r*2)

    def update(self, dt):
        self.pos += self.vel * dt
        self.pos  = wrap_pos(self.pos)
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
        self.rect.center = self.pos

    def draw(self, surf):
        draw_circle(surf, self.pos, self.r, self.color)


class ChargedBullet(pg.sprite.Sprite):
    def __init__(self, pos, vel, owner_id, color):
        super().__init__()
        self.pos   = Vec(pos)
        self.vel   = Vec(vel)
        self.ttl   = C.BULLET_TTL * 1.4
        self.r     = C.CHARGED_RADIUS
        self.owner = owner_id
        self.color = color
        self.rect  = pg.Rect(0, 0, self.r*2, self.r*2)

    def update(self, dt):
        self.pos += self.vel * dt
        self.pos  = wrap_pos(self.pos)
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
        self.rect.center = self.pos

    def draw(self, surf):
        draw_circle(surf, self.pos, self.r, self.color)
        draw_circle(surf, self.pos, self.r+3, self.color, width=1)


class UfoBullet(pg.sprite.Sprite):
    def __init__(self, pos, vel):
        super().__init__()
        self.pos  = Vec(pos)
        self.vel  = Vec(vel)
        self.ttl  = C.UFO_BULLET_TTL
        self.r    = C.BULLET_RADIUS
        self.rect = pg.Rect(0, 0, self.r*2, self.r*2)

    def update(self, dt):
        self.pos += self.vel * dt
        self.pos  = wrap_pos(self.pos)
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
        self.rect.center = self.pos

    def draw(self, surf):
        draw_circle(surf, self.pos, self.r, C.GRAY)


# ---------------------------------------------------------------------------
# Asteroide
# ---------------------------------------------------------------------------

class Asteroid(pg.sprite.Sprite):
    def __init__(self, pos, vel, size):
        super().__init__()
        self.pos  = Vec(pos)
        self.vel  = Vec(vel)
        self.size = size
        self.r    = C.AST_SIZES[size]["r"]
        self.poly = self._make_poly()
        self.rect = pg.Rect(0, 0, self.r*2, self.r*2)

    def _make_poly(self):
        steps = 12 if self.size=="L" else 10 if self.size=="M" else 8
        pts = []
        for i in range(steps):
            ang = i*(360/steps)
            jitter = uniform(0.75, 1.2)
            v = Vec(math.cos(math.radians(ang)), math.sin(math.radians(ang)))
            pts.append(v * self.r * jitter)
        return pts

    def update(self, dt):
        self.pos += self.vel * dt
        self.pos  = wrap_pos(self.pos)
        self.rect.center = self.pos

    def draw(self, surf):
        pts = [(self.pos + p) for p in self.poly]
        pg.draw.polygon(surf, C.WHITE, pts, width=1)


# ---------------------------------------------------------------------------
# Nave do jogador
# ---------------------------------------------------------------------------

def _ship_shape(pos, angle, r, cls):
    """
    Retorna lista de (polígono_principal, [polígonos_extras]) por classe.
    polígono_principal: lista de Vec
    polígonos_extras  : lista de listas de Vec (detalhes adicionais)
    """
    dirv  = angle_to_vec(angle)
    left  = angle_to_vec(angle + 140)
    right = angle_to_vec(angle - 140)
    back  = angle_to_vec(angle + 180)

    if cls == 0:
        # Classe A – INTERCEPTOR: triângulo fino e alongado com aletas traseiras
        p_tip    = pos + dirv          * r * 1.1
        p_left   = pos + angle_to_vec(angle + 148) * r * 0.85
        p_right  = pos + angle_to_vec(angle - 148) * r * 0.85
        # Aletas: dois triângulos pequenos nas costas
        fin_l1   = pos + angle_to_vec(angle + 130) * r * 0.55
        fin_l2   = pos + angle_to_vec(angle + 170) * r * 0.90
        fin_r1   = pos + angle_to_vec(angle - 130) * r * 0.55
        fin_r2   = pos + angle_to_vec(angle - 170) * r * 0.90
        body     = [p_tip, p_left, p_right]
        extras   = [[p_left, fin_l1, fin_l2], [p_right, fin_r1, fin_r2]]
        return body, extras

    elif cls == 1:
        # Classe B – BOMBARDEIRO: corpo largo em forma de diamante + canhão frontal
        p_tip    = pos + dirv          * r * 1.15
        p_left   = pos + angle_to_vec(angle + 105) * r
        p_right  = pos + angle_to_vec(angle - 105) * r
        p_back   = pos + back          * r * 0.55
        # Canhão: linha dupla saindo da ponta
        can_l    = pos + angle_to_vec(angle + 8)  * r * 1.15
        can_r    = pos + angle_to_vec(angle - 8)  * r * 1.15
        can_end  = pos + dirv * r * 1.50
        body     = [p_tip, p_left, p_back, p_right]
        extras   = [[can_l, can_end, can_r]]
        return body, extras

    else:
        # Classe C – CAÇADOR: hexágono assimétrico com asas em delta e garras
        p_tip    = pos + dirv          * r * 1.0
        p_wl     = pos + angle_to_vec(angle + 80)  * r * 1.25   # asa esq
        p_wr     = pos + angle_to_vec(angle - 80)  * r * 1.25   # asa dir
        p_bl     = pos + angle_to_vec(angle + 150) * r * 0.75   # traseira esq
        p_br     = pos + angle_to_vec(angle - 150) * r * 0.75   # traseira dir
        p_back   = pos + back          * r * 0.35
        # Garras nas pontas das asas
        claw_l1  = pos + angle_to_vec(angle + 70)  * r * 1.45
        claw_l2  = pos + angle_to_vec(angle + 92)  * r * 1.45
        claw_r1  = pos + angle_to_vec(angle - 70)  * r * 1.45
        claw_r2  = pos + angle_to_vec(angle - 92)  * r * 1.45
        body     = [p_tip, p_wl, p_bl, p_back, p_br, p_wr]
        extras   = [[p_wl, claw_l1, claw_l2], [p_wr, claw_r1, claw_r2]]
        return body, extras


def draw_ship(surf, pos, angle, r, cls, color,
              invuln=0.0, special_hold=0.0, special_ready=False):
    """Desenha nave completa com todos os detalhes visuais."""
    body, extras = _ship_shape(pos, angle, r, cls)
    draw_poly(surf, body, color)
    for ex in extras:
        draw_poly(surf, ex, color)

    # Invulnerabilidade: anel piscando
    if invuln > 0 and int(invuln * 10) % 2 == 0:
        draw_circle(surf, pos, r + 7, color, width=1)

    # Feedback do especial: arco de carregamento ao redor da nave
    if special_hold > 0:
        from config import SPECIAL_HOLD_TIME
        progress = min(special_hold / SPECIAL_HOLD_TIME, 1.0)
        if special_ready:
            # Pronto: anel cheio pulsando
            t     = pg.time.get_ticks() / 1000.0
            pulse = int(160 + 95 * math.sin(t * 8))
            ring_color = (pulse, pulse, 60)
            draw_circle(surf, pos, r + 10, ring_color, width=2)
        else:
            # Carregando: arco proporcional ao progresso
            arc_color = (
                int(80  + 175 * progress),
                int(200 - 140 * progress),
                60
            )
            rect = pg.Rect(
                int(pos.x) - r - 10,
                int(pos.y) - r - 10,
                (r + 10) * 2,
                (r + 10) * 2
            )
            end_angle = -math.pi/2 + progress * math.tau
            pg.draw.arc(surf, arc_color, rect,
                        -math.pi/2, end_angle, width=3)


class Ship(pg.sprite.Sprite):
    """
    Nave de um jogador.
    cls: 0=Rajada, 1=Carregado, 2=Disperso
    """
    def __init__(self, pos, player_id, color, cls=0):
        super().__init__()
        self.pos        = Vec(pos)
        self.vel        = Vec(0, 0)
        self.angle      = -90.0
        self.cool       = 0.0
        self.invuln     = 0.0
        self.r          = C.SHIP_RADIUS
        self.rect       = pg.Rect(0, 0, self.r*2, self.r*2)

        self.player_id  = player_id
        self.color      = color
        self.cls        = cls

        self.hp         = C.SHIP_MAX_HP
        self.alive_flag = True

        self.special_hold  = 0.0
        self.special_ready = False
        self.burst_queue   = 0
        self.burst_timer   = 0.0

        self.score = 0

    def control(self, state, dt):
        self.angle += state.turn * C.SHIP_TURN_SPEED * dt
        if state.thrust:
            self.vel += angle_to_vec(self.angle) * C.SHIP_THRUST * dt
        self.vel *= C.SHIP_FRICTION

        if state.special:
            self.special_hold += dt
            if self.special_hold >= C.SPECIAL_HOLD_TIME:
                self.special_ready = True
        else:
            self.special_hold  = 0.0
            self.special_ready = False

    def fire(self):
        if self.cool > 0:
            return []
        dirv = angle_to_vec(self.angle)
        pos  = self.pos + dirv * (self.r + 6)
        vel  = self.vel + dirv * C.SHIP_BULLET_SPEED
        self.cool = C.SHIP_FIRE_RATE
        return [Bullet(pos, vel, self.player_id, self.color)]

    def fire_special(self):
        bullets = []
        dirv = angle_to_vec(self.angle)
        pos  = self.pos + dirv * (self.r + 6)
        if self.cls == 0:   # Rajada — iniciada via burst_queue
            self.burst_queue = C.BURST_BULLETS
            self.burst_timer = 0.0
        elif self.cls == 1: # Carregado
            vel = self.vel + dirv * C.CHARGED_SPEED
            bullets.append(ChargedBullet(pos, vel, self.player_id, self.color))
        elif self.cls == 2: # Disperso
            for i in range(C.SCATTER_COUNT):
                spread = C.SCATTER_SPREAD
                off    = -spread + i*(2*spread/(C.SCATTER_COUNT-1))
                d      = angle_to_vec(self.angle + off)
                v      = self.vel + d * C.SHIP_BULLET_SPEED
                bullets.append(Bullet(self.pos + d*(self.r+6), v,
                                      self.player_id, self.color))
        self.special_ready = False
        self.special_hold  = 0.0
        return bullets

    def pop_burst_bullet(self):
        if self.burst_queue > 0 and self.burst_timer <= 0:
            dirv = angle_to_vec(self.angle)
            pos  = self.pos + dirv * (self.r + 6)
            vel  = self.vel + dirv * C.SHIP_BULLET_SPEED
            self.burst_queue -= 1
            self.burst_timer  = C.BURST_INTERVAL
            return Bullet(pos, vel, self.player_id, self.color)
        return None

    def update(self, dt):
        if self.cool > 0:       self.cool   -= dt
        if self.invuln > 0:     self.invuln -= dt
        if self.burst_timer > 0: self.burst_timer -= dt
        self.pos += self.vel * dt
        self.pos  = wrap_pos(self.pos)
        self.rect.center = self.pos

    def draw(self, surf):
        draw_ship(surf, self.pos, self.angle, self.r, self.cls,
                  self.color, self.invuln, self.special_hold, self.special_ready)
        # Barra de HP
        health_bar(surf, self.pos.x, self.pos.y - self.r - 18,
                   self.hp, C.SHIP_MAX_HP, self.color)


# ---------------------------------------------------------------------------
# UFO
# ---------------------------------------------------------------------------

class UFO(pg.sprite.Sprite):
    def __init__(self, pos, small):
        super().__init__()
        self.pos   = Vec(pos)
        self.small = small
        profile    = C.UFO_SMALL if small else C.UFO_BIG
        self.r     = profile["r"]
        self.aim   = profile["aim"]
        self.speed = C.UFO_SPEED
        self.cool  = C.UFO_FIRE_EVERY
        self.rect  = pg.Rect(0, 0, self.r*2, self.r*2)
        self.dir   = Vec(1,0) if uniform(0,1)<0.5 else Vec(-1,0)

    def update(self, dt):
        self.pos += self.dir * self.speed * dt
        self.cool -= dt
        if self.pos.x < -self.r*2 or self.pos.x > C.WIDTH + self.r*2:
            self.kill()
        self.rect.center = self.pos

    def fire_at(self, target_pos):
        if self.cool > 0:
            return None
        aim = (Vec(target_pos) - self.pos)
        if aim.length_squared() == 0:
            aim = self.dir.normalize()
        else:
            aim = aim.normalize()
        shot = aim.rotate(uniform(-(1-self.aim)*60, (1-self.aim)*60))
        self.cool = C.UFO_FIRE_EVERY
        return UfoBullet(self.pos + shot*(self.r+6), shot*C.UFO_BULLET_SPEED)

    def draw(self, surf):
        w, h = self.r*2, self.r
        rect = pg.Rect(0,0,w,h)
        rect.center = self.pos
        pg.draw.ellipse(surf, C.GRAY, rect, width=1)
        cup = pg.Rect(0,0,int(w*0.5),int(h*0.7))
        cup.center = (int(self.pos.x), int(self.pos.y - h*0.3))
        pg.draw.ellipse(surf, C.GRAY, cup, width=1)
