# ASTEROIDE MULTIPLAYER v3.0
# Gerencia o loop principal e todas as cenas.

import math
import random
import sys
from dataclasses import dataclass

import pygame as pg

import config as C
from systems import World
from input import InputManager
from sprites import Ship
from utils import Vec, text, draw_circle
from utils import angle_to_vec


# ---------------------------------------------------------------------------
# Helpers de desenho
# ---------------------------------------------------------------------------

def _draw_ship_preview(surf, pos, angle, r, cls, color):
    """Desenha nave de preview no lobby."""
    from sprites import draw_ship
    draw_ship(surf, Vec(pos), angle, r, cls, color)


def _btn(surf, font, label, cx, cy, selected, color=None):
    color  = color or C.WHITE
    size   = font.size(label)
    pad    = (24, 8)
    w, h   = size[0]+pad[0]*2, size[1]+pad[1]*2
    rect   = pg.Rect(cx-w//2, cy-h//2, w, h)
    bg     = (40,40,40) if selected else (12,12,12)
    pg.draw.rect(surf, bg, rect, border_radius=5)
    pg.draw.rect(surf, color if selected else C.DIM, rect, width=1+(1 if selected else 0), border_radius=5)
    lbl = font.render(label, True, color if selected else C.GRAY)
    surf.blit(lbl, lbl.get_rect(center=rect.center))
    return rect


# ---------------------------------------------------------------------------
# Cena
# ---------------------------------------------------------------------------

@dataclass
class Scene:
    name: str


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------

class Game:

    _CLASS_NAMES = ["CLASSE A – Rajada", "CLASSE B – Carregado", "CLASSE C – Disperso"]
    _CLASS_DESC  = [
        "Especial: 5 tiros rápidos em sequência",
        "Especial: 1 tiro grande e poderoso",
        "Especial: 7 tiros em leque disperso",
    ]
    _TIME_OPTIONS  = [("3 min", 180.0), ("5 min", 300.0), ("7 min", 420.0)]
    _LIVES_OPTIONS = [("1 vida",1),("2 vidas",2),("3 vidas",3),("4 vidas",4),("5 vidas",5)]

    def __init__(self):
        pg.init()
        if C.RANDOM_SEED is not None:
            random.seed(C.RANDOM_SEED)

        self.screen = pg.display.set_mode((C.WIDTH, C.HEIGHT))
        pg.display.set_caption("Asteroides Multiplayer")
        self.clock  = pg.time.Clock()
        self.font   = pg.font.SysFont("consolas", 18)
        self.med    = pg.font.SysFont("consolas", 26)
        self.big    = pg.font.SysFont("consolas", 28)
        self.small  = pg.font.SysFont("consolas", 15)

        # Configurações da partida (definidas no menu)
        self.num_lives  : int   = 3
        self.time_limit : float = 180.0

        self.world     : World | None        = None
        self.input_mgr : InputManager | None = None
        self.go_fade   : float               = 0.0

        # Estado do menu
        self._menu_time_idx  = 0
        self._menu_lives_idx = 2
        self._menu_focus     = 0   # 0=tempo 1=vidas

        # Estado do lobby / seleção de naves
        self._sel_classes   : list[int]  = []   # classe por pid
        self._sel_confirmed : list[bool] = []
        self._sel_angles    : list[float]= []
        self._all_ready     : bool       = False
        self._start_flash   : float      = 0.0

        # Placar final
        self._final_scores: list[tuple] = []
        # Seleção na tela de pausa (0=Continuar, 1=Menu)
        self._pause_sel: int = 0

        # Cena inicial: detectar dispositivo do P1
        self.scene = Scene("detect_p1")

    # ======================================================================
    # Loop principal
    # ======================================================================

    def run(self):
        while True:
            dt     = self.clock.tick(C.FPS) / 1000.0
            events = pg.event.get()

            for e in events:
                if e.type == pg.QUIT:
                    pg.quit(); sys.exit(0)

            self.screen.fill(C.BLACK)

            if self.scene.name == "detect_p1":
                self._update_detect_p1(events)
                self._draw_detect_p1()

            elif self.scene.name == "menu":
                self._update_menu(events, dt)
                self._draw_menu()

            elif self.scene.name == "lobby":
                self._update_lobby(events, dt)
                self._draw_lobby(dt)

            elif self.scene.name == "play":
                keys   = pg.key.get_pressed()
                states = self.input_mgr.read_all(keys)
                self.world.update(dt, states)
                self.world.draw(self.screen, self.font, self.big)
                self._check_pause(events)
                if self.world.game_over:
                    self._final_scores = self.world.get_scores()
                    self.go_fade = 0.0
                    self.scene   = Scene("scoreboard")

            elif self.scene.name == "paused":
                self._update_pause(events, dt)
                self._draw_pause()

            elif self.scene.name == "scoreboard":
                self.go_fade += dt
                self._draw_scoreboard(events)

            pg.display.flip()

    # ======================================================================
    # DETECT P1 — tela inicial para registrar dispositivo do primeiro jogador
    # ======================================================================

    def _update_detect_p1(self, events):
        # Cria InputManager vazio; aguarda qualquer input do P1
        if self.input_mgr is None:
            self.input_mgr = InputManager()
            self.input_mgr.process_hotplug(events)

        self.input_mgr.process_hotplug(events)
        src = self.input_mgr.poll_join(events)
        if src is not None:
            # P1 registrado → ir ao menu
            self.scene = Scene("menu")

    def _draw_detect_p1(self):
        cx = C.WIDTH  // 2
        cy = C.HEIGHT // 2

        title = self.big.render("ASTEROIDS", True, C.WHITE)
        self.screen.blit(title, title.get_rect(centerx=cx, top=cy-160))

        sub = self.med.render("MULTIPLAYER", True, C.GRAY)
        self.screen.blit(sub, sub.get_rect(centerx=cx, top=cy-100))

        # Animação de pulso
        t     = pg.time.get_ticks() / 1000.0
        alpha = int(180 + 75 * math.sin(t * 3.0))
        color = (alpha, alpha, alpha)

        msg = self.med.render("Jogador 1: pressione qualquer botão", True, color)
        self.screen.blit(msg, msg.get_rect(centerx=cx, top=cy-20))

        hint = self.small.render(
            "Teclado: Enter / Shift   Controle: botão A ou LB", True, C.GRAY)
        self.screen.blit(hint, hint.get_rect(centerx=cx, top=cy+30))

    # ======================================================================
    # MENU PRINCIPAL
    # ======================================================================

    def _update_menu(self, events, dt):
        im = self.input_mgr
        im.process_hotplug(events)

        for e in events:
            if e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE:
                pg.quit(); sys.exit(0)

        # Navegação horizontal: eventos discretos + analógico com repeat
        ev_left  = im.nav_left(0, events)
        ev_right = im.nav_right(0, events)
        ax_left, ax_right = im.tick_nav(0, dt)
        go_left  = ev_left  or ax_left
        go_right = ev_right or ax_right

        if go_left:
            if self._menu_focus == 0:
                self._menu_time_idx  = max(0, self._menu_time_idx-1)
            else:
                self._menu_lives_idx = max(0, self._menu_lives_idx-1)
        if go_right:
            if self._menu_focus == 0:
                self._menu_time_idx  = min(2, self._menu_time_idx+1)
            else:
                self._menu_lives_idx = min(4, self._menu_lives_idx+1)

        # Mudar linha focada: teclado ↑↓ ou hat Y ou analógico Y
        for e in events:
            if e.type == pg.KEYDOWN and e.key in (pg.K_UP, pg.K_DOWN, pg.K_w, pg.K_s):
                self._menu_focus ^= 1
            # Hat do gamepad
            if e.type == pg.JOYHATMOTION and e.value[1] != 0:
                self._menu_focus ^= 1
        # Analógico Y do gamepad (com cooldown próprio)
        if im.is_gamepad(0):
            ay_val, _ = im.tick_nav_y(0, dt)
            if ay_val:
                self._menu_focus ^= 1

        if im.fire_event(0, events):
            _, self.time_limit = self._TIME_OPTIONS[self._menu_time_idx]
            _, self.num_lives  = self._LIVES_OPTIONS[self._menu_lives_idx]
            self._enter_lobby()

    def _draw_menu(self):
        cx = C.WIDTH // 2
        title = self.big.render("ASTEROIDS", True, C.WHITE)
        self.screen.blit(title, title.get_rect(centerx=cx, top=60))

        base_y = 180
        row_h  = 80

        # --- Tempo ---
        focused = self._menu_focus == 0
        lbl = self.font.render("TEMPO DE PARTIDA", True, C.WHITE if focused else C.GRAY)
        self.screen.blit(lbl, lbl.get_rect(centerx=cx, top=base_y))
        for i,(label,_) in enumerate(self._TIME_OPTIONS):
            _btn(self.screen, self.font, label,
                 cx - 120 + i*120, base_y+36,
                 selected=(i==self._menu_time_idx))

        # --- Vidas ---
        focused = self._menu_focus == 1
        lbl = self.font.render("VIDAS POR JOGADOR", True, C.WHITE if focused else C.GRAY)
        self.screen.blit(lbl, lbl.get_rect(centerx=cx, top=base_y+row_h))
        for i,(label,_) in enumerate(self._LIVES_OPTIONS):
            _btn(self.screen, self.font, label,
                 cx - 240 + i*120, base_y+row_h+36,
                 selected=(i==self._menu_lives_idx))

        hint = self.font.render("← → ajustar   ↑ ↓ trocar linha   Fogo: confirmar", True, C.GRAY)
        self.screen.blit(hint, hint.get_rect(centerx=cx, top=base_y+row_h*2+20))

        # Controles resumidos (dispositivo do P1)
        dev = self.small.render(
            f"P1: {self.input_mgr.source_label(0)}", True, C.PLAYER_COLORS[0])
        self.screen.blit(dev, dev.get_rect(centerx=cx, top=base_y+row_h*2+60))

    # ======================================================================
    # LOBBY / SELEÇÃO DE NAVES
    # ======================================================================

    def _enter_lobby(self):
        n = self.input_mgr.num_players
        self._sel_classes   = [0] * n
        self._sel_confirmed = [False] * n
        self._sel_angles    = [0.0] * n
        self._all_ready     = False
        self._start_flash   = 0.0
        self.scene = Scene("lobby")

    def _update_lobby(self, events, dt):
        im = self.input_mgr
        im.process_hotplug(events)

        # Girar pré-visualizações
        for pid in range(im.num_players):
            self._sel_angles[pid] += 60 * dt

        # Tentar adicionar novo jogador (atire para entrar)
        if im.num_players < InputManager.MAX_PLAYERS:
            new_src = im.poll_join(events)
            if new_src is not None:
                self._sel_classes.append(0)
                self._sel_confirmed.append(False)
                self._sel_angles.append(0.0)

        n = im.num_players

        # ESC / back do P1 → voltar ao menu
        if im.special_event(0, events) and not self._sel_confirmed[0]:
            self.scene = Scene("menu")
            return

        # Cada jogador controla sua própria seleção simultaneamente
        for pid in range(n):
            if self._sel_confirmed[pid]:
                # Confirmar já feito; bota de volta com special
                if im.special_event(pid, events):
                    self._sel_confirmed[pid] = False
                    self._all_ready = False
                continue

            # Navegação: eventos discretos (hat, botão, teclado)
            went_left  = im.nav_left(pid, events)
            went_right = im.nav_right(pid, events)
            # Navegação: analógico com repeat (retorna (left, right))
            ax_left, ax_right = im.tick_nav(pid, dt)
            if went_left  or ax_left:
                self._sel_classes[pid] = (self._sel_classes[pid]-1) % 3
            if went_right or ax_right:
                self._sel_classes[pid] = (self._sel_classes[pid]+1) % 3
            if im.fire_event(pid, events):
                self._sel_confirmed[pid] = True

        # Verificar se todos confirmaram
        if n >= 1 and all(self._sel_confirmed[:n]):
            self._all_ready = True
            self._start_flash += dt
            # Qualquer fogo quando todos prontos → iniciar partida
            for pid in range(n):
                if im.fire_event(pid, events):
                    self._start_game()
                    return
        else:
            self._all_ready = False
            self._start_flash = 0.0

    def _start_game(self):
        n = self.input_mgr.num_players
        player_classes = self._sel_classes[:n]
        self.world = World(player_classes, self.num_lives, self.time_limit)
        self.scene = Scene("play")

    def _draw_lobby(self, dt):
        im = self.input_mgr
        n  = im.num_players

        title = self.med.render("SELEÇÃO DE NAVE", True, C.WHITE)
        self.screen.blit(title, title.get_rect(centerx=C.WIDTH//2, top=10))

        slot_w  = C.WIDTH // InputManager.MAX_PLAYERS
        center_y= C.HEIGHT // 2 + 20

        for pid in range(InputManager.MAX_PLAYERS):
            cx = pid * slot_w + slot_w // 2

            if pid >= n:
                # Slot vazio — mostra "Atire para entrar"
                if n < InputManager.MAX_PLAYERS:
                    t = pg.time.get_ticks()/1000.0
                    alpha = int(140 + 80*math.sin(t*2.5 + pid))
                    color = (alpha//3, alpha//3, alpha//3)
                    pg.draw.rect(self.screen, (8,8,8),
                                 (pid*slot_w+2, 50, slot_w-4, C.HEIGHT-60),
                                 border_radius=8)
                    pg.draw.rect(self.screen, (30,30,30),
                                 (pid*slot_w+2, 50, slot_w-4, C.HEIGHT-60),
                                 width=1, border_radius=8)
                    join_lbl = self.small.render("Atire para entrar", True, color)
                    self.screen.blit(join_lbl, join_lbl.get_rect(centerx=cx, centery=center_y))
                continue

            color    = C.PLAYER_COLORS[pid]
            cls      = self._sel_classes[pid]
            confirmed= self._sel_confirmed[pid]

            # Painel de fundo
            if confirmed:
                pg.draw.rect(self.screen, (10,30,10),
                             (pid*slot_w+2, 50, slot_w-4, C.HEIGHT-60), border_radius=8)
                pg.draw.rect(self.screen, (50,160,50),
                             (pid*slot_w+2, 50, slot_w-4, C.HEIGHT-60),
                             width=2, border_radius=8)
            else:
                pg.draw.rect(self.screen, (10,10,20),
                             (pid*slot_w+2, 50, slot_w-4, C.HEIGHT-60), border_radius=8)
                pg.draw.rect(self.screen, color,
                             (pid*slot_w+2, 50, slot_w-4, C.HEIGHT-60),
                             width=2, border_radius=8)

            # Nome do jogador e dispositivo
            plbl = self.font.render(f"P{pid+1}", True, color)
            self.screen.blit(plbl, plbl.get_rect(centerx=cx, top=60))
            dev  = self.small.render(im.source_label(pid), True, C.GRAY)
            self.screen.blit(dev, dev.get_rect(centerx=cx, top=82))

            # Nave girando
            angle = self._sel_angles[pid]
            _draw_ship_preview(self.screen, (cx, center_y-40), angle, 26, cls, color)

            if confirmed:
                ready = self.big.render("PRONTO", True, (80,220,80))
                self.screen.blit(ready, ready.get_rect(centerx=cx, top=center_y+10))
                back_hint = self.small.render("Especial: voltar", True, C.GRAY)
                self.screen.blit(back_hint, back_hint.get_rect(centerx=cx, top=center_y+70))
            else:
                # Pontos de seleção de classe
                for i in range(3):
                    dot_color = color if i==cls else C.DIM
                    filled    = (i==cls)
                    draw_circle(self.screen, Vec(cx-20+i*20, center_y+10), 5,
                                dot_color, width=0 if filled else 1)

                # Nome e descrição da classe
                cname = self.small.render(self._CLASS_NAMES[cls], True, color)
                self.screen.blit(cname, cname.get_rect(centerx=cx, top=center_y+28))

                # Descrição com quebra de linha
                words = self._CLASS_DESC[cls].split()
                line, lines = "", []
                for w in words:
                    test = line + (" " if line else "") + w
                    if self.small.size(test)[0] > slot_w-20:
                        lines.append(line); line = w
                    else:
                        line = test
                if line: lines.append(line)
                for li, ln in enumerate(lines):
                    ls = self.small.render(ln, True, C.GRAY)
                    self.screen.blit(ls, ls.get_rect(centerx=cx, top=center_y+50+li*18))

                hint = self.small.render("← → classe   Fogo: confirmar", True, C.GRAY)
                self.screen.blit(hint, hint.get_rect(centerx=cx, top=C.HEIGHT-42))

        # Mensagem de iniciar quando todos prontos
        if self._all_ready and n >= 1:
            t     = pg.time.get_ticks()/1000.0
            alpha = int(190 + 65*math.sin(t*4))
            color = (alpha, alpha, int(alpha*0.6))
            msg   = self.med.render("Todos prontos! Atire para iniciar!", True, color)
            self.screen.blit(msg, msg.get_rect(centerx=C.WIDTH//2, top=C.HEIGHT-36))

        # Linha de rodapé geral
        if not self._all_ready:
            sep = self.small.render(
                f"Jogadores: {n}/4   Especial do P1: voltar ao menu", True, C.DIM)
            self.screen.blit(sep, sep.get_rect(centerx=C.WIDTH//2, top=C.HEIGHT-20))

    # ======================================================================
    # PAUSA
    # ======================================================================

    def _check_pause(self, events):
        pid = self.input_mgr.any_pause(events)
        if pid >= 0:
            self.world.paused = True
            self._pause_sel   = 0
            self.scene = Scene("paused")

    def _update_pause(self, events, dt):
        im = self.input_mgr

        # Navegação vertical entre as duas opções (0=Continuar, 1=Menu)
        for e in events:
            if e.type == pg.KEYDOWN and e.key in (pg.K_UP, pg.K_DOWN, pg.K_w, pg.K_s):
                self._pause_sel ^= 1
            if e.type == pg.JOYHATMOTION and e.value[1] != 0:
                self._pause_sel ^= 1

        # Analógico Y com repeat
        for pid in range(im.num_players):
            up, down = im.tick_nav_y(pid, dt)
            if up or down:
                self._pause_sel ^= 1
                break

        # Confirmar seleção: fogo de qualquer jogador
        confirmed = False
        for pid in range(im.num_players):
            if im.fire_event(pid, events):
                confirmed = True
                break
        for e in events:
            if e.type == pg.KEYDOWN and e.key == pg.K_RETURN:
                confirmed = True
            if e.type == pg.MOUSEBUTTONDOWN:
                confirmed = True   # mouse tratado no draw

        if confirmed:
            if self._pause_sel == 0:
                self.world.paused = False
                self.scene = Scene("play")
            else:
                self.world.paused = False
                self.scene = Scene("menu")
                self._reset_lobby()

        # Pause novamente → continuar (toggle)
        for pid in range(im.num_players):
            if im.pause_event(pid, events):
                self.world.paused = False
                self.scene = Scene("play")
                return

        # ESC → continuar
        for e in events:
            if e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE:
                self.world.paused = False
                self.scene = Scene("play")

    def _draw_pause(self):
        self.world.draw(self.screen, self.font, self.big)

        overlay = pg.Surface((C.WIDTH, C.HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0,0))

        cx = C.WIDTH//2
        cy = C.HEIGHT//2

        title = self.big.render("PAUSADO", True, C.WHITE)
        self.screen.blit(title, title.get_rect(centerx=cx, top=cy-110))

        sel = self._pause_sel
        resume_rect = _btn(self.screen, self.med, "Continuar",     cx, cy,    sel==0, C.WHITE)
        menu_rect   = _btn(self.screen, self.med, "Menu Principal", cx, cy+70, sel==1, C.WHITE)

        # Mouse hover / click
        mx, my = pg.mouse.get_pos()
        if resume_rect.collidepoint(mx, my):
            self._pause_sel = 0
        elif menu_rect.collidepoint(mx, my):
            self._pause_sel = 1
        if pg.mouse.get_pressed()[0]:
            if resume_rect.collidepoint(mx, my):
                self.world.paused = False; self.scene = Scene("play")
            elif menu_rect.collidepoint(mx, my):
                self.world.paused = False; self.scene = Scene("menu"); self._reset_lobby()

        hint = self.small.render(
            "↑↓ / Analógico: navegar   Fogo / Enter: confirmar   Start: continuar",
            True, C.GRAY)
        self.screen.blit(hint, hint.get_rect(centerx=cx, top=cy+150))

    def _reset_lobby(self):
        """Limpa estado de lobby sem resetar o InputManager."""
        n = self.input_mgr.num_players
        self._sel_classes   = [0] * n
        self._sel_confirmed = [False] * n
        self._sel_angles    = [0.0] * n
        self._all_ready     = False

    # ======================================================================
    # PLACAR FINAL
    # ======================================================================

    def _draw_scoreboard(self, events):
        alpha = min(255, int(255 * self.go_fade / C.GAME_OVER_FADE_DURATION))
        overlay = pg.Surface((C.WIDTH, C.HEIGHT), pg.SRCALPHA)
        overlay.fill((0,0,0, min(210, alpha)))
        self.screen.blit(overlay, (0,0))
        if alpha < 60:
            return

        cx = C.WIDTH // 2

        title = self.big.render("FIM DE PARTIDA", True, C.WHITE)
        self.screen.blit(title, title.get_rect(centerx=cx, top=60))

        base_y = 160
        row_h  = 80
        scores = self._final_scores

        for rank, (pid, score, lives) in enumerate(scores):
            color = C.PLAYER_COLORS[pid]
            cy    = base_y + rank * row_h
            rect  = pg.Rect(cx-300, cy, 600, 64)

            if rank == 0:
                pg.draw.rect(self.screen, (35,35,5),  rect, border_radius=8)
                pg.draw.rect(self.screen, (200,170,20), rect, width=2, border_radius=8)
            else:
                pg.draw.rect(self.screen, (10,10,10), rect, border_radius=8)
                pg.draw.rect(self.screen, C.DIM,      rect, width=1, border_radius=8)

            medals = ["🥇","🥈","🥉","4º"]
            medal  = self.med.render(medals[min(rank,3)], True, color)
            self.screen.blit(medal, medal.get_rect(left=rect.left+12, centery=rect.centery))

            pname = self.med.render(f"P{pid+1}", True, color)
            self.screen.blit(pname, pname.get_rect(left=rect.left+72, centery=rect.centery))

            pts = self.med.render(f"{score:06d} pts", True, C.WHITE)
            self.screen.blit(pts, pts.get_rect(right=rect.right-12, centery=rect.centery))

        if scores:
            wpid  = scores[0][0]
            wmsg  = self.med.render(f"Vencedor: P{wpid+1}!", True, C.PLAYER_COLORS[wpid])
            self.screen.blit(wmsg, wmsg.get_rect(centerx=cx,
                                                  top=base_y+len(scores)*row_h+20))

        hint = self.font.render("Fogo / Enter — Menu Principal", True, C.GRAY)
        self.screen.blit(hint, hint.get_rect(centerx=cx, top=C.HEIGHT-50))

        # Qualquer fogo de qualquer jogador → voltar ao menu
        for pid in range(self.input_mgr.num_players):
            if self.input_mgr.fire_event(pid, events):
                self._go_to_menu(); return
        for e in events:
            if e.type == pg.KEYDOWN and e.key in (pg.K_RETURN, pg.K_ESCAPE, pg.K_SPACE):
                self._go_to_menu(); return

    def _go_to_menu(self):
        self._reset_lobby()
        self.scene = Scene("menu")
