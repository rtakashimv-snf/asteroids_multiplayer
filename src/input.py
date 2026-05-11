# ASTEROIDE MULTIPLAYER v3.0
# Camada de input unificada: teclado e gamepad genérico SDL.
#
# Filosofia desta versão:
#   - Não há número fixo de jogadores na criação.
#   - InputManager monitora TODOS os dispositivos (teclados e pads).
#   - Ao detectar um "fire event" de um dispositivo ainda não registrado,
#     ele é devolvido para a cena de lobby registrá-lo como novo jogador.
#   - Cada jogador recebe uma InputSource (KeyboardSource ou GamepadSource)
#     identificada pelo seu dispositivo.

from __future__ import annotations
import pygame as pg

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
AXIS_LEFT_X = 0
AXIS_LEFT_Y = 1
AXIS_DEAD   = 0.22

# Slots de teclado disponíveis (até 4 jogadores no teclado)
_KB_MAPS = [
    {"left": pg.K_LEFT,  "right": pg.K_RIGHT, "up": pg.K_UP,
     "fire": pg.K_RETURN, "special": pg.K_RSHIFT},
    {"left": pg.K_a,     "right": pg.K_d,     "up": pg.K_w,
     "fire": pg.K_f,      "special": pg.K_g},
    {"left": pg.K_j,     "right": pg.K_l,     "up": pg.K_i,
     "fire": pg.K_n,      "special": pg.K_m},
    {"left": pg.K_KP4,   "right": pg.K_KP6,   "up": pg.K_KP8,
     "fire": pg.K_KP0,    "special": pg.K_KP1},
]

# Teclas que disparam "entrar no jogo" vindas do teclado P1 (slot 0)
_KB_JOIN_KEYS = {pg.K_RETURN, pg.K_RSHIFT, pg.K_SPACE,
                 pg.K_f, pg.K_g, pg.K_n, pg.K_m,
                 pg.K_KP0, pg.K_KP1}


# ---------------------------------------------------------------------------
# Estado normalizado
# ---------------------------------------------------------------------------
class InputState:
    __slots__ = ("turn", "thrust", "fire", "special", "pause", "back")

    def __init__(self):
        self.turn    : float = 0.0
        self.thrust  : bool  = False
        self.fire    : bool  = False
        self.special : bool  = False
        self.pause   : bool  = False   # Start / Escape
        self.back    : bool  = False   # Especial segurado no menu


# ---------------------------------------------------------------------------
# Fontes de input
# ---------------------------------------------------------------------------
class KeyboardSource:
    def __init__(self, slot: int):
        self.slot    = slot
        self._km     = _KB_MAPS[slot]
        self.device_id = f"kb:{slot}"   # identificador único

    def read(self, keys) -> InputState:
        km = self._km
        st = InputState()
        if keys[km["left"]]:  st.turn -= 1.0
        if keys[km["right"]]: st.turn += 1.0
        st.thrust  = bool(keys[km["up"]])
        st.fire    = bool(keys[km["fire"]])
        st.special = bool(keys[km["special"]])
        st.pause   = bool(keys[pg.K_ESCAPE])
        st.back    = st.special
        return st

    def is_fire_event(self, e: pg.event.Event) -> bool:
        return e.type == pg.KEYDOWN and e.key == self._km["fire"]

    def is_special_event(self, e: pg.event.Event) -> bool:
        return e.type == pg.KEYDOWN and e.key == self._km["special"]

    def is_pause_event(self, e: pg.event.Event) -> bool:
        return e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE

    def label(self) -> str:
        labels = ["Teclado (Setas/Enter)", "Teclado (WASD/F)",
                  "Teclado (IJKL/N)", "Teclado (Numpad)"]
        return labels[self.slot]


class GamepadSource:
    def __init__(self, joy: pg.joystick.Joystick):
        self._joy         = joy
        self._joy.init()
        self._naxes       = joy.get_numaxes()
        self._nbtns       = joy.get_numbuttons()
        self._nhats       = joy.get_numhats()
        self.device_id    = f"pad:{joy.get_instance_id()}"

    @property
    def instance_id(self) -> int:
        return self._joy.get_instance_id()

    def _btn(self, i: int) -> bool:
        return bool(i < self._nbtns and self._joy.get_button(i))

    def _axis(self, i: int) -> float:
        return self._joy.get_axis(i) if 0 <= i < self._naxes else 0.0

    def read(self, _keys=None) -> InputState:
        st = InputState()

        # Virar: eixo analógico X ou hat
        ax = self._axis(AXIS_LEFT_X)
        if abs(ax) > AXIS_DEAD:
            st.turn = max(-1.0, min(1.0, ax))
        if self._nhats > 0 and abs(st.turn) < AXIS_DEAD:
            hx, _ = self._joy.get_hat(0)
            st.turn = float(hx)

        # Thrust: eixo Y negativo ou hat cima
        ay = self._axis(AXIS_LEFT_Y)
        if ay < -AXIS_DEAD:
            st.thrust = True
        if not st.thrust and self._nhats > 0:
            _, hy = self._joy.get_hat(0)
            st.thrust = hy > 0

        # Fogo: botão 0 (A/Cruz) ou botão 4 (LB)
        st.fire    = self._btn(0) or self._btn(4)
        # Especial: botão 1 (B/Círculo) ou botão 5 (RB)
        st.special = self._btn(1) or self._btn(5)
        # Pause: botão 7 (Start/Options) ou botão 9
        st.pause   = self._btn(7) or self._btn(9)
        st.back    = st.special
        return st

    def is_fire_event(self, e: pg.event.Event) -> bool:
        if e.type != pg.JOYBUTTONDOWN:
            return False
        if e.joy != self.instance_id:
            return False
        return e.button in (0, 4)

    def is_special_event(self, e: pg.event.Event) -> bool:
        if e.type != pg.JOYBUTTONDOWN:
            return False
        if e.joy != self.instance_id:
            return False
        return e.button in (1, 5)

    def is_pause_event(self, e: pg.event.Event) -> bool:
        if e.type != pg.JOYBUTTONDOWN:
            return False
        if e.joy != self.instance_id:
            return False
        # Botão 6=Select/Share, 7=Start/Options, 9=Options em alguns layouts
        return e.button in (6, 7, 9)

    def label(self) -> str:
        return self._joy.get_name()[:30]


# ---------------------------------------------------------------------------
# Gerenciador global de input
# ---------------------------------------------------------------------------
class InputManager:
    """
    Gerencia todos os dispositivos conectados e a lista de jogadores ativos.

    Uso no lobby:
        im = InputManager()
        # por frame:
        new_src = im.poll_join(events)   # retorna InputSource se alguém entrou
        states  = im.read_all(keys)      # list[InputState] por jogador registrado

    Uso no jogo:
        states = im.read_all(keys)
    """

    MAX_PLAYERS = 4

    def __init__(self):
        pg.joystick.init()
        # Todos os pads conectados: instance_id → GamepadSource
        self._pads: dict[int, GamepadSource] = {}
        self._init_pads()

        # Jogadores registrados em ordem de entrada
        self.sources: list[KeyboardSource | GamepadSource] = []
        # device_ids já registrados (evita duplicata)
        self._registered: set[str] = set()
        # Slots de teclado disponíveis
        self._kb_slots_used: set[int] = set()

    def _init_pads(self):
        for i in range(pg.joystick.get_count()):
            joy = pg.joystick.Joystick(i)
            gp  = GamepadSource(joy)
            self._pads[gp.instance_id] = gp

    # ------------------------------------------------------------------
    # Registro de dispositivos (chamado pelo lobby)
    # ------------------------------------------------------------------

    def process_hotplug(self, events: list):
        """Atualiza lista de pads conectados. Chamar todo frame."""
        for e in events:
            if e.type == pg.JOYDEVICEADDED:
                # pygame 2.x: JOYDEVICEADDED só tem device_index
                # o instance_id é obtido após criar o Joystick
                joy = pg.joystick.Joystick(e.device_index)
                gp  = GamepadSource(joy)
                if gp.instance_id not in self._pads:
                    self._pads[gp.instance_id] = gp
            elif e.type == pg.JOYDEVICEREMOVED:
                # JOYDEVICEREMOVED tem instance_id no pygame 2.x
                iid = getattr(e, 'instance_id', None)
                if iid is not None:
                    self._pads.pop(iid, None)

    def poll_join(self, events: list) -> "KeyboardSource | GamepadSource | None":
        """
        Verifica se algum dispositivo não registrado disparou 'fire'.
        Se sim, registra-o e devolve a fonte criada (para o lobby exibir).
        Retorna None se ninguém entrou.
        """
        if len(self.sources) >= self.MAX_PLAYERS:
            return None

        for e in events:
            src = self._source_from_event(e)
            if src is None:
                continue
            if src.device_id in self._registered:
                continue
            # Novo dispositivo disparou fogo → registra
            self._registered.add(src.device_id)
            self.sources.append(src)
            return src
        return None

    def _source_from_event(self, e: pg.event.Event) -> "KeyboardSource | GamepadSource | None":
        """Devolve a fonte correspondente ao evento, se for um 'fire event'."""
        # Teclado
        if e.type == pg.KEYDOWN and e.key in _KB_JOIN_KEYS:
            # Descobrir qual slot de teclado bate com essa tecla
            for slot, km in enumerate(_KB_MAPS):
                if e.key == km["fire"] or e.key == km["special"]:
                    dev_id = f"kb:{slot}"
                    if dev_id not in self._registered:
                        # Verifica slot disponível
                        if slot not in self._kb_slots_used:
                            self._kb_slots_used.add(slot)
                            return KeyboardSource(slot)
            # Tecla genérica não mapeada num slot livre → slot 0 se livre
            dev_id = "kb:0"
            if dev_id not in self._registered and 0 not in self._kb_slots_used:
                self._kb_slots_used.add(0)
                return KeyboardSource(0)
            return None

        # Gamepad
        if e.type == pg.JOYBUTTONDOWN and e.button in (0, 4):
            iid = e.joy
            if iid in self._pads:
                gp = self._pads[iid]
                if gp.device_id not in self._registered:
                    return gp
        return None

    # ------------------------------------------------------------------
    # Leitura de estado por frame
    # ------------------------------------------------------------------

    def read_all(self, keys) -> list[InputState]:
        return [src.read(keys) for src in self.sources]

    def read(self, pid: int, keys) -> InputState:
        if pid < len(self.sources):
            return self.sources[pid].read(keys)
        return InputState()

    # ------------------------------------------------------------------
    # Eventos discretos por jogador (usado em menus/lobby)
    # ------------------------------------------------------------------

    def fire_event(self, pid: int, events: list) -> bool:
        if pid >= len(self.sources):
            return False
        return any(self.sources[pid].is_fire_event(e) for e in events)

    def special_event(self, pid: int, events: list) -> bool:
        if pid >= len(self.sources):
            return False
        return any(self.sources[pid].is_special_event(e) for e in events)

    def pause_event(self, pid: int, events: list) -> bool:
        if pid >= len(self.sources):
            return False
        return any(self.sources[pid].is_pause_event(e) for e in events)

    def any_pause(self, events: list) -> int:
        """Retorna pid que pausou, ou -1."""
        for pid in range(len(self.sources)):
            if self.pause_event(pid, events):
                return pid
        return -1

    # Controle de repetição analógica para navegação de menu
    # _axis_nav_state[pid] = (last_axis_x, repeat_timer)
    _axis_nav_cooldown = 0.30   # segundos entre repeats ao segurar

    def _axis_nav_init(self, pid):
        if not hasattr(self, '_axis_nav_state'):
            self._axis_nav_state = {}

    def _tick_axis(self, pid: int, dt: float, axis: int, key: str):
        """Helper genérico de repeat analógico. Retorna (neg, pos)."""
        if not hasattr(self, '_axis_nav_state'):
            self._axis_nav_state = {}
        full_key = f"{pid}_{key}"
        if full_key not in self._axis_nav_state:
            self._axis_nav_state[full_key] = {'held': False, 'timer': 0.0}
        if pid >= len(self.sources) or isinstance(self.sources[pid], KeyboardSource):
            return False, False
        src   = self.sources[pid]
        av    = src._axis(axis)
        state = self._axis_nav_state[full_key]
        neg, pos = False, False
        if abs(av) > 0.5:
            if not state['held']:
                state['held']  = True
                state['timer'] = self._axis_nav_cooldown
                neg = av < -0.5
                pos = av >  0.5
            else:
                state['timer'] -= dt
                if state['timer'] <= 0:
                    state['timer'] = self._axis_nav_cooldown
                    neg = av < -0.5
                    pos = av >  0.5
        else:
            state['held']  = False
            state['timer'] = 0.0
        return neg, pos

    def tick_nav(self, pid: int, dt: float):
        """Repeat analógico horizontal. Retorna (left, right)."""
        self._axis_nav_init(pid)
        return self._tick_axis(pid, dt, 0, 'x')

    def tick_nav_y(self, pid: int, dt: float):
        """Repeat analógico vertical. Retorna (up, down)."""
        self._axis_nav_init(pid)
        up, down = self._tick_axis(pid, dt, 1, 'y')
        # eixo Y: -1 = cima, +1 = baixo — inverter para up=True quando vai pra cima
        return up, down

    def nav_left(self, pid: int, events: list) -> bool:
        if pid >= len(self.sources):
            return False
        src = self.sources[pid]
        if isinstance(src, KeyboardSource):
            return any(e.type == pg.KEYDOWN and e.key == src._km["left"] for e in events)
        joy = src._joy
        iid = joy.get_instance_id()
        # Hat ou botão LB
        for e in events:
            if e.type == pg.JOYHATMOTION and e.joy == iid and e.value[0] < 0:
                return True
            if e.type == pg.JOYBUTTONDOWN and e.joy == iid and e.button == 4:
                return True
        # Analógico (via tick_nav, chamado externamente)
        if hasattr(self, '_axis_nav_state') and pid in self._axis_nav_state:
            pass   # resultado já foi computado no tick_nav e retornado lá
        return False

    def nav_right(self, pid: int, events: list) -> bool:
        if pid >= len(self.sources):
            return False
        src = self.sources[pid]
        if isinstance(src, KeyboardSource):
            return any(e.type == pg.KEYDOWN and e.key == src._km["right"] for e in events)
        joy = src._joy
        iid = joy.get_instance_id()
        for e in events:
            if e.type == pg.JOYHATMOTION and e.joy == iid and e.value[0] > 0:
                return True
            if e.type == pg.JOYBUTTONDOWN and e.joy == iid and e.button == 5:
                return True
        return False

    def source_label(self, pid: int) -> str:
        if pid < len(self.sources):
            return self.sources[pid].label()
        return "—"

    def is_gamepad(self, pid: int) -> bool:
        return pid < len(self.sources) and isinstance(self.sources[pid], GamepadSource)

    @property
    def num_players(self) -> int:
        return len(self.sources)
