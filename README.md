# 🚀 Asteroids Multiplayer

Clone do clássico arcade **Asteroids** com suporte a **até 4 jogadores simultâneos**, desenvolvido em Python com Pygame. Cada jogador escolhe uma classe de nave com habilidade especial única e compete por pontuação em partidas com tempo e vidas configuráveis.

---

## 🎮 Funcionalidades

- **1 a 4 jogadores simultâneos** — suporte a teclado e gamepad (SDL/pygame)
- **Hot-plug de dispositivos** — jogadores entram no lobby pressionando qualquer botão, sem configuração prévia
- **3 classes de nave** com habilidades especiais distintas
- **Sistema de ondas** — asteroides surgem em ondas crescentes de dificuldade
- **UFOs inimigos** — aparecem periodicamente com mira automática nos jogadores
- **Friendly fire ativo** — jogadores podem acertar uns aos outros (com pontuação)
- **Sistema de HP e vidas** — cada nave tem 4 pontos de HP antes de perder uma vida
- **Placar final** com ranking por pontuação
- **Pausa** com menu de retorno ao jogo ou ao menu principal
- **Partida configurável** — tempo (3, 5 ou 7 minutos) e número de vidas (1 a 5)

---

## 🛸 Classes de Nave

| Classe | Visual | Habilidade Especial |
|---|---|---|
| **A – Rajada** | Interceptor (triângulo fino com aletas) | Dispara uma rajada de 5 tiros rápidos em sequência |
| **B – Carregado** | Bombardeiro (diamante + canhão frontal) | Dispara 1 projétil grande e mais poderoso |
| **C – Disperso** | Caçador (hexágono assimétrico com garras) | Dispara 7 tiros em leque com spread de 35° |

O especial é ativado segurando o botão por **1,2 segundos**. Um arco de carregamento ao redor da nave indica o progresso visualmente.

---

## 🕹️ Controles

### Teclado (4 slots disponíveis)

| Ação | P1 (Setas) | P2 (WASD) | P3 (IJKL) | P4 (Numpad) |
|---|---|---|---|---|
| Girar | `←` / `→` | `A` / `D` | `J` / `L` | `4` / `6` |
| Acelerar | `↑` | `W` | `I` | `8` |
| Atirar | `Enter` | `F` | `N` | `0` |
| Especial | `Shift Dir.` | `G` | `M` | `1` |
| Pausar | `Esc` | `Esc` | `Esc` | `Esc` |

### Gamepad (Xbox / genérico SDL)

| Ação | Botão |
|---|---|
| Girar | Analógico esquerdo X / D-pad |
| Acelerar | Analógico esquerdo Y / D-pad cima |
| Atirar | `A` (botão 0) ou `LB` (botão 4) |
| Especial | `B` (botão 1) ou `RB` (botão 5) |
| Pausar | `Start` / `Options` (botão 7 ou 9) |

---

## 🏆 Sistema de Pontuação

| Evento | Pontos |
|---|---|
| Asteroide grande (L) | 20 pts |
| Asteroide médio (M) | 50 pts |
| Asteroide pequeno (S) | 100 pts |
| UFO grande | 200 pts |
| UFO pequeno | 1.000 pts |
| Acertar outro jogador | 150 pts |

---

## 📁 Estrutura do Projeto

```
asteroids_multiplayer/
├── src/
│   ├── main.py       # Ponto de entrada — instancia e roda o Game
│   ├── game.py       # Loop principal e cenas (menu, lobby, jogo, pausa, placar)
│   ├── systems.py    # World: simulação da partida (física, colisões, ondas, UFOs)
│   ├── sprites.py    # Entidades: Ship, Asteroid, UFO, Bullet, ChargedBullet, UfoBullet
│   ├── input.py      # Camada de input unificada: teclado e gamepad via SDL
│   ├── config.py     # Todas as constantes do jogo (dimensões, física, balanceamento)
│   └── utils.py      # Utilitários: Vec, wrap_pos, funções de desenho, health_bar
├── .gitignore
├── LICENSE           # MIT
└── README.md
```

---

## ⚙️ Requisitos

- Python 3.10+
- Pygame 2.x

---

## ▶️ Como Executar

```bash
# 1. Clone o repositório
git clone https://github.com/rtakashimv-snf/asteroids_multiplayer.git
cd asteroids_multiplayer

# 2. Instale a dependência
pip install pygame

# 3. Execute
python src/main.py
```

---

## 🔧 Configuração

Todas as constantes do jogo estão em `src/config.py` e podem ser ajustadas livremente:

```python
WIDTH, HEIGHT = 1280, 800   # Resolução da janela
FPS           = 60          # Taxa de quadros

SHIP_MAX_HP       = 4       # HP por vida
SHIP_FIRE_RATE    = 0.18    # Cooldown entre tiros (segundos)
SPECIAL_HOLD_TIME = 1.2     # Tempo de carga do especial

AST_VEL_MIN = 35.0          # Velocidade mínima dos asteroides
AST_VEL_MAX = 100.0         # Velocidade máxima dos asteroides

UFO_SPAWN_EVERY = 20.0      # Intervalo entre aparições de UFOs (segundos)
RANDOM_SEED     = None      # Semente para reprodutibilidade (None = aleatório)
```

---

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

---

## 👤 Autor

Desenvolvido por Rubens Takashi, Matheus Takashi e Vinicius Castro
