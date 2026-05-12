# ASTEROIDE MULTIPLAYER v3.0
# World: simulação da partida.

import math
from random import uniform
import pygame as pg
import config as C
from sprites import Asteroid, Ship, UFO, Bullet, ChargedBullet, UfoBullet
from utils import Vec, rand_edge_pos, rand_unit_vec


class World:
    _SPAWN_POS = [
        (C.WIDTH*0.25, C.HEIGHT*0.35),
        (C.WIDTH*0.75, C.HEIGHT*0.65),
        (C.WIDTH*0.75, C.HEIGHT*0.35),
        (C.WIDTH*0.25, C.HEIGHT*0.65),
    ]

    def __init__(self, player_classes, num_lives, time_limit):
        self.num_players = len(player_classes)
        self.time_limit  = time_limit
        self.elapsed     = 0.0
        self.game_over   = False
        self.paused      = False

        self.ships: list[Ship] = []
        for pid, cls in enumerate(player_classes):
            pos  = self._SPAWN_POS[pid]
            ship = Ship(Vec(pos), pid, C.PLAYER_COLORS[pid], cls)
            self.ships.append(ship)

        self.lives: list[int] = [num_lives] * self.num_players

        self.bullets     = pg.sprite.Group()
        self.ufo_bullets = pg.sprite.Group()
        self.asteroids   = pg.sprite.Group()
        self.ufos        = pg.sprite.Group()
        self.all_sprites = pg.sprite.Group(*self.ships)

        self.wave          = 0
        self.wave_cool     = C.WAVE_DELAY
        self.ufo_timer     = C.UFO_SPAWN_EVERY
        self.safe          = C.SAFE_SPAWN_TIME
        self.respawn_timers: list[float] = [0.0] * self.num_players

    # ------------------------------------------------------------------
    def start_wave(self):
        self.wave += 1
        count  = 2 + self.wave + self.num_players
        living = [s for s in self.ships if s.alive_flag]
        for _ in range(count):
            pos   = rand_edge_pos()
            tries = 0
            while any((pos-s.pos).length()<180 for s in living) and tries<20:
                pos = rand_edge_pos()
                tries += 1
            ang   = uniform(0, math.tau)
            speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX)
            self._spawn_ast(pos, Vec(math.cos(ang),math.sin(ang))*speed, "L")

    def _spawn_ast(self, pos, vel, size):
        a = Asteroid(pos, vel, size)
        self.asteroids.add(a)
        self.all_sprites.add(a)

    def _split_ast(self, ast, scorer_id):
        pts   = C.AST_SIZES[ast.size]["score"]
        split = C.AST_SIZES[ast.size]["split"]
        pos   = Vec(ast.pos)
        ast.kill()
        if 0 <= scorer_id < self.num_players:
            self.ships[scorer_id].score += pts
        for s in split:
            self._spawn_ast(pos, rand_unit_vec()*uniform(C.AST_VEL_MIN,C.AST_VEL_MAX)*1.2, s)

    # ------------------------------------------------------------------
    def _spawn_ufo(self):
        if self.ufos: return
        small = uniform(0,1)<0.5
        y = uniform(0, C.HEIGHT)
        x = 0 if uniform(0,1)<0.5 else C.WIDTH
        ufo = UFO(Vec(x,y), small)
        ufo.dir.xy = (1,0) if x==0 else (-1,0)
        self.ufos.add(ufo)
        self.all_sprites.add(ufo)

    def _ufo_fire(self):
        living = [s for s in self.ships if s.alive_flag and s.invuln<=0]
        if not living: return
        for ufo in self.ufos:
            target = min(living, key=lambda s:(s.pos-ufo.pos).length())
            b = ufo.fire_at(target.pos)
            if b:
                self.ufo_bullets.add(b)
                self.all_sprites.add(b)

    # ------------------------------------------------------------------
    def _add_bullets(self, blist):
        for b in blist:
            self.bullets.add(b)
            self.all_sprites.add(b)

    def try_fire(self, pid):
        ship = self.ships[pid]
        if not ship.alive_flag: return
        self._add_bullets(ship.fire())

    def try_special(self, pid):
        ship = self.ships[pid]
        if not ship.alive_flag or not ship.special_ready: return
        self._add_bullets(ship.fire_special())

    # ------------------------------------------------------------------
    def _ship_hit(self, ship, damage=1):
        if ship.invuln > 0: return
        ship.hp -= damage
        if ship.hp <= 0:
            ship.hp = C.SHIP_MAX_HP
            self.lives[ship.player_id] -= 1
            ship.alive_flag = False
            ship.kill()
            if self.lives[ship.player_id] <= 0:
                self._check_game_over()
            else:
                self.respawn_timers[ship.player_id] = C.SAFE_SPAWN_TIME
        else:
            ship.invuln = 1.2

    def _respawn(self, pid):
        ship = self.ships[pid]
        ship.pos.xy   = self._SPAWN_POS[pid]
        ship.vel.xy   = (0,0)
        ship.angle    = -90.0
        ship.invuln   = C.SAFE_SPAWN_TIME
        ship.alive_flag = True
        self.all_sprites.add(ship)

    def _check_game_over(self):
        alive = [pid for pid in range(self.num_players) if self.lives[pid]>0]
        if len(alive) <= 1:
            self.game_over = True

    # ------------------------------------------------------------------
    def update(self, dt, input_states):
        if self.paused or self.game_over:
            return

        self.elapsed += dt
        if self.elapsed >= self.time_limit:
            self.game_over = True
            return

        # Reaparecer
        for pid in range(self.num_players):
            if self.respawn_timers[pid] > 0:
                self.respawn_timers[pid] -= dt
                if self.respawn_timers[pid] <= 0 and self.lives[pid] > 0:
                    self._respawn(pid)

        # Controle
        for ship in self.ships:
            pid = ship.player_id
            if ship.alive_flag and pid < len(input_states):
                st = input_states[pid]
                ship.control(st, dt)
                if st.fire:
                    self.try_fire(pid)
                if st.special and ship.special_ready:
                    self.try_special(pid)

        self.all_sprites.update(dt)

        # Burst
        for ship in self.ships:
            if ship.alive_flag and ship.cls == 0:
                b = ship.pop_burst_bullet()
                if b:
                    self._add_bullets([b])

        # UFO
        if self.ufos:
            self._ufo_fire()
        else:
            self.ufo_timer -= dt
        if not self.ufos and self.ufo_timer <= 0:
            self._spawn_ufo()
            self.ufo_timer = C.UFO_SPAWN_EVERY

        self._collisions()

        if not self.asteroids and self.wave_cool <= 0:
            self.start_wave()
            self.wave_cool = C.WAVE_DELAY
        elif not self.asteroids:
            self.wave_cool -= dt

    # ------------------------------------------------------------------
    def _collisions(self):
        # Balas jogadores → asteroides
        hits = pg.sprite.groupcollide(
            self.asteroids, self.bullets, False, True,
            collided=lambda a,b: (a.pos-b.pos).length()<a.r)
        for ast, blts in hits.items():
            self._split_ast(ast, blts[0].owner if blts else -1)

        # Balas UFO → asteroides
        hits2 = pg.sprite.groupcollide(
            self.asteroids, self.ufo_bullets, False, True,
            collided=lambda a,b: (a.pos-b.pos).length()<a.r)
        for ast, _ in hits2.items():
            self._split_ast(ast, -1)

        # Balas jogadores → UFOs
        for ufo in list(self.ufos):
            for b in list(self.bullets):
                if (ufo.pos-b.pos).length() < (ufo.r+b.r):
                    pts = C.UFO_SMALL["score"] if ufo.small else C.UFO_BIG["score"]
                    self.ships[b.owner].score += pts
                    ufo.kill(); b.kill()
                    break

        # Balas jogadores → outras naves (friendly fire ON)
        for b in list(self.bullets):
            for ship in self.ships:
                if ship.player_id == b.owner: continue
                if not ship.alive_flag: continue
                if (ship.pos-b.pos).length() < (ship.r + b.r):
                    b.kill()
                    if isinstance(b, ChargedBullet):
                        self._ship_hit(ship, C.CHARGED_DAMAGE)
                    else:
                        self._ship_hit(ship)
                    # Pontos por acertar outro jogador
                    self.ships[b.owner].score += 150
                    break

        # Naves → asteroides / UFOs / balas UFO
        for ship in self.ships:
            if not ship.alive_flag or ship.invuln > 0: continue
            for ast in self.asteroids:
                if (ast.pos-ship.pos).length() < (ast.r+ship.r):
                    self._ship_hit(ship); break
            for ufo in self.ufos:
                if (ufo.pos-ship.pos).length() < (ufo.r+ship.r):
                    self._ship_hit(ship); break
            for blt in list(self.ufo_bullets):
                if (blt.pos-ship.pos).length() < (blt.r+ship.r):
                    blt.kill(); self._ship_hit(ship); break

        # Empurrão entre naves (sem dano)
        for i in range(len(self.ships)):
            for j in range(i+1, len(self.ships)):
                si, sj = self.ships[i], self.ships[j]
                if not (si.alive_flag and sj.alive_flag): continue
                dist = (si.pos-sj.pos).length()
                if 0 < dist < si.r+sj.r:
                    push = (si.pos-sj.pos).normalize() * 2
                    si.vel += push; sj.vel -= push

    # ------------------------------------------------------------------
    def draw(self, surf, font, big):
        for spr in self.all_sprites:
            spr.draw(surf)

        # HUD superior
        pg.draw.line(surf, C.DIM, (0,56), (C.WIDTH,56), width=1)
        slot_w = C.WIDTH // self.num_players
        cls_names = ["RAJADA","CARREGADO","DISPERSO"]
        for pid in range(self.num_players):
            ship  = self.ships[pid]
            color = C.PLAYER_COLORS[pid]
            x     = pid * slot_w + 8
            lives_str = "♥ " * max(0, self.lives[pid])
            lbl = font.render(
                f"P{pid+1} [{cls_names[ship.cls]}]  {ship.score:05d}  {lives_str}",
                True, color)
            surf.blit(lbl, (x, 8))

        # Cronômetro
        rem  = max(0.0, self.time_limit - self.elapsed)
        mins = int(rem)//60
        secs = int(rem)%60
        tt   = big.render(f"{mins}:{secs:02d}", True, C.WHITE)
        surf.blit(tt, tt.get_rect(centerx=C.WIDTH//2, top=26))

        # Indicadores de reaparecer
        for pid in range(self.num_players):
            if self.respawn_timers[pid] > 0:
                pos = self._SPAWN_POS[pid]
                msg = font.render(f"P{pid+1} reaparecendo...", True, C.PLAYER_COLORS[pid])
                surf.blit(msg, msg.get_rect(center=(int(pos[0]),int(pos[1]))))

    def get_scores(self):
        return sorted(
            [(pid, self.ships[pid].score, self.lives[pid])
             for pid in range(self.num_players)],
            key=lambda t: t[1], reverse=True)
