import pygame
import math
import sys
import random

try:
    from tennis_mvc_model import GameModel
    from tennis_mvc_view import GameView
    from tennis_mvc_controller import GameController
except (ImportError, AttributeError):
    # Standalone fallback: the game still runs if the MVC helper files were
    # not copied beside this file or an older module has the same name.
    class GameModel:
        def __init__(self, game_context):
            self.game = game_context

        @property
        def screen_state(self):
            return self.game.state

        @property
        def is_running(self):
            return self.game.running

        @property
        def is_paused(self):
            return self.game.paused

        @property
        def is_match_over(self):
            return self.game.match_over

        def restart_match(self):
            self.game.reset_match()

    class GameView:
        def __init__(self, game_context, model):
            self.game = game_context
            self.model = model

        def render_menu_state(self):
            g = self.game
            if g.state in ("menu", "options"):
                g.draw_menu()
            elif g.state in ("select_player", "select_opp"):
                g.draw_select()
            elif g.state == "select_court":
                g.draw_court_select()
            elif g.state == "select_racket":
                g.draw_racket_select()

        def render_paused_game(self):
            g = self.game
            g.draw_court()
            if g.serve_phase == "wait" and not g.match_over:
                g.draw_service_box(g.server, g.serve_deuce)
            g.draw_player(g.p2, 0.7)
            if g.ball_y < 300:
                g.draw_ball()
            g.draw_net()
            if g.ball_y >= 300:
                g.draw_ball()
            g.draw_player(g.p1, 1.1)
            g.draw_scoreboard()
            g.blit_center("PAUSED", g.big_font, g.WHITE, g.WIDTH // 2, 70)
            mouse_pos = g.pygame.mouse.get_pos()
            g.draw_button(g.pause_continue_rect, "CONTINUE", g.pause_continue_rect.collidepoint(mouse_pos))
            g.draw_button(g.pause_quit_rect, "QUIT TO MENU", g.pause_quit_rect.collidepoint(mouse_pos))

    class GameController:
        def __init__(self, game_context, model, view):
            self.game = game_context
            self.model = model
            self.view = view

        def handle_menu(self, events):
            self.game.handle_menu_events(events)

        def handle_game_input(self, events):
            g = self.game
            space_pressed = False
            for event in events:
                if event.type == g.pygame.QUIT:
                    g.running = False
                elif event.type == g.pygame.KEYDOWN:
                    if event.key == g.pygame.K_ESCAPE:
                        g.paused = not g.paused
                    elif event.key == g.pygame.K_r and g.match_over:
                        self.model.restart_match()
                    elif event.key == g.pygame.K_SPACE:
                        space_pressed = True
                elif (event.type == g.pygame.MOUSEBUTTONDOWN
                      and event.button == 1 and g.paused):
                    if g.pause_continue_rect.collidepoint(event.pos):
                        g.paused = False
                    elif g.pause_quit_rect.collidepoint(event.pos):
                        g.paused = False
                        g.state = "menu"
                        g.menu_sel = 0
            return space_pressed

pygame.init()
WIDTH, HEIGHT = 900, 600
fullscreen = False
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MICO TENNIS")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 22, bold=True)
small_font = pygame.font.SysFont("consolas", 18, bold=True)
tiny_font = pygame.font.SysFont("consolas", 14, bold=True)
big_font = pygame.font.SysFont("consolas", 44, bold=True)
title_font = pygame.font.SysFont("consolas", 76, bold=True)


def toggle_fullscreen():
    """Toggle between the normal window and fullscreen mode with F11."""
    global fullscreen, screen
    fullscreen = not fullscreen
    # SCALED keeps the game's 900x600 logical canvas intact and centers it
    # with proportional scaling/letterboxing on larger fullscreen displays.
    flags = (pygame.FULLSCREEN | pygame.SCALED) if fullscreen else 0
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    pygame.display.set_caption("MICO TENNIS")

# ---------------- SETTINGS ----------------
BASE_SPEED = 5.0              # 100% running speed of YOU (WASD)   -> 80% = 4.0
OPP_BASE_SPEED = 6.0          # 100% running speed of the CPU      -> 80% = 4.8
P1_REACH_X = 60               # how close (left/right) the ball must be to be hit
PLAYER_USES_RETURN_RATE = True  # True: your player also misses sometimes (return %)
SET_OPTIONS = [3, 6, 8]       # available set-win targets in OPTIONS
SETS_TO_WIN = 3               # number of sets needed to win the match
SWING_FRAMES = 22             # how long a racket swing lasts (frames)
SERVE_CHANGE = "set"          # "set"   = alternate server after EACH set
                              # "point" = server alternates after EVERY point
                              # "game"  = server changes every game
SERVE_FAULT_CHANCE = 0.08     # chance a serve lands outside the box (0 = never)
SERVE_AUTO_FRAMES = 150       # your serve starts by itself after this many frames
# ------------------------------------------

# ---------------- PLAYERS ----------------
# Every player plays the same: only name, title and colour differ (those are just labels).
ALL_SPEED = 0.85    # 85% running speed for everyone
ALL_RETURN = 0.90   # 90% ball return for everyone

PLAYERS = [
    {
        'name': 'CARLOS ALCARAZ', 'first': 'CARLOS', 'last': 'ALCARAZ',
        'tag': 'The fast and consistent',
        'stats': [('ATP/WTA WINS', '10'), ('GRAND SLAM TITLES', '3')],
        'speed': 0.92, 'ret': 0.80,
        'color': (255, 70, 70), 'glow': (170, 20, 20),        # RED
    },
    {
        'name': 'ROGER FEDERER', 'first': 'ROGER', 'last': 'FEDERER',
        'tag': 'The elegant and legend',
        'stats': [('GRAND SLAM WINS', '23'), ('ATP/WTA WINS', '32'),
                  ('WIMBLEDON TITLES', '15'), ('GRAND SLAM TITLES', '21')],
        'speed': 0.85, 'ret': 0.95,
        'color': (55, 190, 85), 'glow': (25, 115, 50),        # GREEN
    },
    {
        'name': 'JANNIK SINNER', 'first': 'JANNIK', 'last': 'SINNER',
        'tag': 'Italian professional tennis player, TOP 1 world champion',
        'stats': [('ATP/WTA WINS', '12'), ('WIMBLEDON TITLES', '18'),
                  ('GRAND SLAM TITLES', '5')],
        'speed': 0.86, 'ret': 0.90,
        'color': (80, 150, 255), 'glow': (20, 70, 200),       # BLUE
    },
    {
        'name': 'BEN SHELTON', 'first': 'BEN', 'last': 'SHELTON',
        'tag': 'The speedy and American professional player',
        'stats': [('ATP/WTA WINS', '8'), ('WIMBLEDON TITLES', '4'),
                  ('GRAND SLAM TITLES', '7')],
        'speed': 0.92, 'ret': 0.88,
        'color': (255, 150, 30), 'glow': (200, 90, 0),         # ORANGE
    },
]

# ---------------- COURTS ----------------
# ball_speed: multiplies how fast the ball travels
# bounce:     multiplies how high the ball bounces
# grip:       1.0 = you stop instantly, small number = you slide (clay)
COURTS = [
    {
        'name': 'GRASS COURT', 'event': '(WIMBLEDON)', 'kind': 'grass',
        'headline': 'Fastest surface speed',
        'bullets': ['Lower ball bounce', 'Quick reaction needed', 'Favors aggressive play',
                    'Smooth natural texture', 'Used in Wimbledon'],
        'color': (40, 140, 55), 'alt': (52, 168, 68),
        'ball_speed': 1.15, 'bounce': 0.75, 'grip': 0.60,
        'bar_speed': 0.95, 'bar_bounce': 0.55,
    },
    {
        'name': 'HARD COURT', 'event': '(US OPEN)', 'kind': 'hard',
        'headline': 'Medium-fast gameplay',
        'bullets': ['Consistent bounce', 'Balanced playing style', 'Most popular surface',
                    'Durable surface type', 'Used in US Open'],
        # US Open-style blue hard court with a subtle lighter blue alternate shade.
        'color': (32, 105, 185), 'alt': (42, 125, 210),
        'ball_speed': 1.00, 'bounce': 1.00, 'grip': 1.00,
        'bar_speed': 0.75, 'bar_bounce': 0.75,
    },
    {
        'name': 'CLAY COURT', 'event': '(FRENCH OPEN)', 'kind': 'clay',
        'headline': 'Slower ball speed',
        'bullets': ['High bounce control', 'Long rallies common', 'Sliding movement style',
                    'Physically demanding', 'Used in French Open'],
        'color': (200, 95, 45), 'alt': (165, 70, 28),
        'ball_speed': 0.85, 'bounce': 1.30, 'grip': 0.14,
        'bar_speed': 0.55, 'bar_bounce': 1.00,
    },
]

# ---------------- RACKETS ----------------
RACKETS = [
    {
        'name': 'BABOLAT PURE DRIVE',
        'color': (255, 105, 70), 'glow': (190, 45, 25),
        'stats': [('CONTROL', 0.90), ('COMFORT', 0.85), ('SPIN', 0.75),
                  ('POWER', 0.70), ('DURABILITY', 0.60)],
    },
    {
        'name': 'YONEX EZONE',
        'color': (80, 210, 255), 'glow': (20, 120, 190),
        'stats': [('POWER', 0.93), ('COMFORT', 0.85), ('CONTROL', 0.75),
                  ('SPIN', 0.78), ('DURABILITY', 0.65)],
    },
    {
        'name': 'WILSON PRO STAFF',
        'color': (210, 100, 255), 'glow': (120, 35, 180),
        'stats': [('CONTROL', 0.92), ('COMFORT', 0.82), ('SPIN', 0.80),
                  ('POWER', 0.70), ('DURABILITY', 0.65)],
    },
    {
        'name': 'HEAD RADICAL',
        'color': (255, 210, 55), 'glow': (190, 135, 15),
        'stats': [('CONTROL', 0.88), ('COMFORT', 0.83), ('POWER', 0.75),
                  ('SPIN', 0.78), ('DURABILITY', 0.65)],
    },
]

court_choice = 1          # default: hard court
court_kind = COURTS[1]['kind']
court_color = COURTS[1]['color']
court_alt = COURTS[1]['alt']
court_speed = COURTS[1]['ball_speed']
court_bounce = COURTS[1]['bounce']
court_grip = COURTS[1]['grip']

# chosen characters
p1_choice = 0
opp_choice = 1
racket_choice = 0
names = [PLAYERS[0]['last'], PLAYERS[1]['last']]
player_colors = [PLAYERS[0]['color'], PLAYERS[1]['color']]

# stats used in the match (set by start_match)
p1_speed = BASE_SPEED * ALL_SPEED
p1_return = ALL_RETURN
p2_speed = OPP_BASE_SPEED * ALL_SPEED
opp_return = ALL_RETURN

# Colors: dark green cyber tennis theme
BLACK = (3, 10, 4)
NEON_GREEN = (70, 190, 95)        # primary emerald green
GLOW_GREEN = (35, 130, 65)        # muted green accent
DARK_GREEN = (10, 70, 30)         # deep green background accent
WHITE = (232, 245, 232)
PANEL = (6, 28, 14)

# Court colors
COURT_BLUE = (32, 105, 185)
LINE_WHITE = (255, 255, 255)
NET_BLACK = (0, 16, 5)
BALL_YELLOW = (220, 235, 90)

# Outer Court Trapezoid
COURT = [(250, 120), (650, 120), (820, 520), (80, 520)]

# Inner Service Lines
TOP_SERVICE_Y = 220
BOT_SERVICE_Y = 420
TOP_SERVICE_LEFT = (210, TOP_SERVICE_Y)
TOP_SERVICE_RIGHT = (690, TOP_SERVICE_Y)
BOT_SERVICE_LEFT = (120, BOT_SERVICE_Y)
BOT_SERVICE_RIGHT = (780, BOT_SERVICE_Y)

# Net
NET_LEFT = (180, 300)
NET_RIGHT = (720, 300)
NET_HEIGHT = 45

CENTER_X = 450


def court_left_x(y):
    return 250 + (y - 120) * (80 - 250) / 400.0


def court_right_x(y):
    return 650 + (y - 120) * (820 - 650) / 400.0


# fixed random specks for the clay texture
_rng = random.Random(7)
clay_specks = []
for _ in range(260):
    _y = _rng.uniform(126, 514)
    _x = _rng.uniform(court_left_x(_y) + 6, court_right_x(_y) - 6)
    clay_specks.append((int(_x), int(_y)))


def new_player(x, y, color=(50, 255, 100), glow=(0, 180, 60)):
    return {'x': x, 'y': y, 'px': x, 'py': y,      # position + previous position
            'color': color, 'glow': glow,            # shirt/body colors
            'phase': 0.0, 'moving': False,           # running animation
            'lean': 0.0,                             # body lean while running
            'swing': 0, 'side': 1,                   # racket swing timer + side
            'stroke': 'forehand'}                    # current forehand/backhand stroke


# Player Positions
p1_vel = [0.0, 0.0]        # your current velocity (used for sliding on clay)
p1 = new_player(450.0, 510.0, PLAYERS[0]['color'], PLAYERS[0]['glow'])
p2 = new_player(450.0, 130.0, PLAYERS[1]['color'], PLAYERS[1]['glow'])

# ---------------- TENNIS SCORE STATE ----------------
# index 0 = YOU (bottom), index 1 = CPU (top)
points = [0, 0]            # points in the current game
games = [0, 0]             # games in the current set
completed_sets = []        # list of (your_games, cpu_games) for finished sets
sets_won = [0, 0]
server = 0                 # who is serving: 0 = YOU, 1 = CPU
in_tiebreak = False
tb_start_server = 0
match_over = False
match_winner = None
message = ""
pause_timer = 0

# Ball State
ball_x = 450.0
ball_y = 500.0
ball_vx = 2.0
ball_vy = -4.5
ball_arc_y = 0.0
ball_arc_vy = 4.0
bounced_top = False
bounced_bottom = False

# Return decisions for the current ball
p2_will_miss = False
p2_miss_offset = 0.0
p1_will_return = True

# Serve state
serve_phase = None          # None | "wait" (ball tossed, waiting) | "flying" (serve in the air)
serve_timer = 0
serve_frames_left = 0
serve_is_fault = False
second_serve = False
next_second_serve = False
serve_deuce = True          # True = serving from the right (deuce) side
serve_spot = (450.0, 515.0)
serve_mark = None           # [x, y, frames] white mark where the serve landed


def decide_opponent():
    """Called every time the ball is sent toward the opponent."""
    global p2_will_miss, p2_miss_offset
    p2_will_miss = random.random() >= opp_return
    p2_miss_offset = random.choice([-1, 1]) * random.randint(110, 170)


def decide_player():
    """Called every time the ball is sent toward YOU (uses your return %)."""
    global p1_will_return
    if PLAYER_USES_RETURN_RATE:
        p1_will_return = random.random() < p1_return
    else:
        p1_will_return = True


def service_box(srv, deuce):
    """The diagonal service box the serve must land in.
    Returns (y_top, y_bottom, is_left_side_of_screen)."""
    if srv == 0:                      # you serve from the bottom -> box in the top half
        return 220, 300, deuce        # right-side serve -> left box (diagonal)
    return 300, 420, (not deuce)      # CPU serves from the top -> box in the bottom half


def pick_serve_target(srv, deuce, fault):
    y0, y1, left = service_box(srv, deuce)
    if srv == 0:
        ty = random.uniform(235, 285)
        if fault:
            ty = random.uniform(180, 205)      # long: past the service line
    else:
        ty = random.uniform(335, 405)
        if fault:
            ty = random.uniform(435, 458)
    if left:
        tx = random.uniform(court_left_x(ty) + 20, CENTER_X - 20)
    else:
        tx = random.uniform(CENTER_X + 20, court_right_x(ty) - 20)
    return tx, ty


def serve(srv, second=False):
    """Begin a serve: the server walks to the correct side (right on even points,
    left on odd points), tosses the ball and waits."""
    global serve_phase, serve_timer, second_serve, serve_deuce, serve_spot
    global ball_x, ball_y, ball_vx, ball_vy, ball_arc_y, ball_arc_vy
    global bounced_top, bounced_bottom
    second_serve = second
    serve_deuce = ((points[0] + points[1]) % 2 == 0)

    if srv == 0:
        serve_spot = (550.0 if serve_deuce else 350.0, 515.0)
        p1['x'], p1['y'] = serve_spot
        p1_vel[0] = p1_vel[1] = 0.0
        p2['x'] = CENTER_X
        ball_x, ball_y = serve_spot[0], serve_spot[1] - 10
    else:
        serve_spot = (380.0 if serve_deuce else 520.0, 130.0)
        p2['x'], p2['y'] = serve_spot
        ball_x, ball_y = serve_spot[0], serve_spot[1] - 10

    ball_vx = ball_vy = 0.0
    ball_arc_y = 34.0
    ball_arc_vy = 0.0
    bounced_top = bounced_bottom = False
    serve_phase = "wait"
    serve_timer = SERVE_AUTO_FRAMES if srv == 0 else 70


def launch_serve():
    """Hit the serve diagonally into the service box (next to the center line)."""
    global serve_phase, serve_frames_left, serve_is_fault
    global ball_vx, ball_vy, ball_arc_y, ball_arc_vy, bounced_top, bounced_bottom
    srv = server
    serve_is_fault = random.random() < SERVE_FAULT_CHANCE
    tx, ty = pick_serve_target(srv, serve_deuce, serve_is_fault)

    speed = 4.5 * court_speed
    dy = ty - ball_y
    frames = max(30, int(abs(dy) / speed))
    ball_vy = dy / frames
    ball_vx = (tx - ball_x) / frames
    # arc that touches the ground exactly at the target (gravity is 0.18 per frame)
    ball_arc_y = 28.0
    ball_arc_vy = 0.09 * frames - 28.0 / frames
    serve_frames_left = frames

    bounced_top = (srv == 0)       # the serve bounce already counts as the bounce
    bounced_bottom = (srv == 1)
    serve_phase = "flying"
    if srv == 0:
        decide_opponent()
    else:
        decide_player()
    start_swing(p1 if srv == 0 else p2, ball_x)


# ---------------- TENNIS SCORING LOGIC ----------------
def win_game(who):
    global server, in_tiebreak, tb_start_server, match_over, message, match_winner
    other = 1 - who
    games[who] += 1
    points[0] = points[1] = 0
    was_tiebreak = in_tiebreak
    in_tiebreak = False

    g, o = games[who], games[other]
    set_won = (g >= 6 and g - o >= 2) or g == 7

    if set_won:
        completed_sets.append((games[0], games[1]))
        sets_won[who] += 1
        games[0] = games[1] = 0
        message = "SET!"
        # With set-based serving, the server changes only after a set is won.
        # A tiebreak still hands service to the other player for the next set.
        server = (1 - tb_start_server) if was_tiebreak else (1 - server)
        if sets_won[who] >= SETS_TO_WIN:
            match_over = True
            match_winner = who
            message = f"{names[who]} WINS THE MATCH!"
    else:
        message = "GAME!"
        if SERVE_CHANGE == "game":
            server = 1 - server
        if games[0] == 6 and games[1] == 6:
            in_tiebreak = True
            tb_start_server = server


def win_point(who):
    global server
    other = 1 - who
    points[who] += 1
    if in_tiebreak:
        total = points[0] + points[1]
        if SERVE_CHANGE == "point":
            server = tb_start_server ^ (((total + 1) // 2) % 2)
        if points[who] >= 7 and points[who] - points[other] >= 2:
            win_game(who)
    else:
        if points[who] >= 4 and points[who] - points[other] >= 2:
            win_game(who)


def point_scored(who, text=None):
    """who: 0 = you won the point, 1 = CPU won the point."""
    global message, pause_timer, server, next_second_serve
    prev_server = server
    message = text or ("POINT!" if who == 0 else "MISSED!")
    win_point(who)
    if SERVE_CHANGE == "point" and not in_tiebreak and not match_over:
        server = 1 - prev_server          # the other player serves next
    next_second_serve = False
    pause_timer = 70


def point_text(i):
    """Text for the current-game score: 0, 15, 30, 40, AD."""
    o = 1 - i
    if in_tiebreak:
        return str(points[i])
    pi, po = points[i], points[o]
    if pi >= 3 and po >= 3:
        if pi == po:
            return "40"
        return "AD" if pi > po else "40"
    return ["0", "15", "30", "40"][pi]


def reset_match():
    global server, in_tiebreak, tb_start_server, match_over, message, pause_timer, paused, match_winner
    points[0] = points[1] = 0
    games[0] = games[1] = 0
    sets_won[0] = sets_won[1] = 0
    completed_sets.clear()
    server = 0
    in_tiebreak = False
    tb_start_server = 0
    match_over = False
    match_winner = None
    paused = False
    message = ""
    pause_timer = 0
    c1, c2 = PLAYERS[p1_choice], PLAYERS[opp_choice]
    p1_vel[0] = p1_vel[1] = 0.0
    p1.update(new_player(450.0, 510.0, c1['color'], c1['glow']))
    p2.update(new_player(450.0, 130.0, c2['color'], c2['glow']))
    serve(server)


def start_match():
    """Apply the chosen characters' stats + chosen court and start a new match."""
    global p1_speed, p1_return, p2_speed, opp_return, names, player_colors
    global court_kind, court_color, court_alt, court_speed, court_bounce, court_grip
    c1 = PLAYERS[p1_choice]
    c2 = PLAYERS[opp_choice]
    p1_speed = BASE_SPEED * c1['speed']
    p1_return = c1['ret']
    p2_speed = OPP_BASE_SPEED * c2['speed']
    opp_return = c2['ret']
    names = [c1['last'], c2['last']]
    player_colors = [c1['color'], c2['color']]

    ct = COURTS[court_choice]
    court_kind = ct['kind']
    court_color = ct['color']
    court_alt = ct['alt']
    court_speed = ct['ball_speed']
    court_bounce = ct['bounce']
    court_grip = ct['grip']
    reset_match()


# ---------------- PLAYER ANIMATION + DRAWING ----------------
def stroke_for_ball(p, target_x):
    """Choose a stroke from the ball's position relative to the player's body."""
    return 'forehand' if target_x >= p['x'] else 'backhand'


def start_swing(p, target_x, stroke=None):
    """Start a forehand or backhand swing on the side where the ball is."""
    if stroke not in ('forehand', 'backhand'):
        stroke = stroke_for_ball(p, target_x)
    if p['swing'] == 0:
        p['swing'] = SWING_FRAMES
        p['stroke'] = stroke
        p['side'] = 1 if stroke == 'forehand' else -1


def update_anim(p):
    """Update running animation + swing timer. Call once per frame."""
    dx = p['x'] - p['px']
    dy = p['y'] - p['py']
    speed = math.hypot(dx, dy)
    p['moving'] = speed > 0.5
    if p['moving']:
        # A slower, steady cadence gives a believable running rhythm instead
        # of making the legs flicker or appear to skate.
        p['phase'] += 0.16 + speed * 0.025
    target_lean = max(-5.0, min(5.0, dx * 1.2))
    p['lean'] += (target_lean - p['lean']) * 0.3
    p['px'], p['py'] = p['x'], p['y']
    if p['swing'] > 0:
        p['swing'] -= 1


def swing_angle(t):
    """Racket arm angle in degrees (0 = down, 90 = sideways, 180 = up).
    Backswing -> fast swing through the ball -> follow-through."""
    IDLE, BACK, END = 70, 165, -30
    if t < 0.35:
        return IDLE + (BACK - IDLE) * (t / 0.35)
    elif t < 0.65:
        return BACK + (END - BACK) * ((t - 0.35) / 0.30)
    return END + (IDLE - END) * ((t - 0.65) / 0.35)


def draw_player(p, scale=1.0):
    """Neon stick figure that runs with swinging legs and swings a racket."""
    x, y = p['x'], p['y']
    COL, GLOW = p['color'], p['glow']
    leg = 22 * scale
    h = 25 * scale
    arm = 20 * scale
    ph = p['phase']
    moving = p['moving']
    swinging = p['swing'] > 0
    side = p['side']
    t = 1 - p['swing'] / SWING_FRAMES if swinging else 0.0

    bob = abs(math.sin(ph)) * 2.5 * scale if moving else 0
    hip = (x, y - bob)

    # body lean (running + swing)
    lean = p['lean']
    if swinging:
        lean += side * scale * (-4 + 9 * min(1.0, max(0.0, (t - 0.2) / 0.4)))
        if t > 0.8:
            lean *= (1 - (t - 0.8) / 0.2)
    sh = (hip[0] + lean, hip[1] - h)

    # shadow
    pygame.draw.ellipse(screen, (25, 28, 26),
                        (int(x - 14 * scale), int(y + leg - 4 * scale), int(28 * scale), int(8 * scale)))

    # Legs: alternating forward/back stride with a lifted, bent knee.
    if moving:
        leg_cycles = ((ph, -1), (ph + math.pi, 1))
    else:
        leg_cycles = ((0.25, -1), (-0.25, 1))
    for leg_phase, leg_side in leg_cycles:
        stride = math.sin(leg_phase)
        knee_lift = max(0.0, math.cos(leg_phase))
        hip_x = hip[0] + leg_side * 3 * scale
        knee = (hip_x + stride * 8 * scale,
                hip[1] + 11 * scale - knee_lift * 4 * scale)
        foot = (knee[0] + stride * 9 * scale,
                hip[1] + leg * 1.05 - knee_lift * 7 * scale)
        pygame.draw.line(screen, COL, (hip_x, hip[1]), knee, 3)
        pygame.draw.line(screen, COL, knee, foot, 3)
        pygame.draw.line(screen, COL, foot,
                         (foot[0] + 5 * scale * (1 if stride >= 0 else -1), foot[1]), 3)

    # torso
    pygame.draw.line(screen, GLOW, hip, sh, 6)
    pygame.draw.line(screen, COL, hip, sh, 3)

    # head
    pygame.draw.circle(screen, COL, (int(sh[0] + lean * 0.3), int(sh[1] - 8 * scale)), max(3, int(8 * scale)))

    is_backhand = p.get('stroke') == 'backhand' and swinging

    # Off-hand balances the body while running, but joins the racket for a backhand.
    shoulder = (sh[0], sh[1] + 4 * scale)
    if moving and not is_backhand:
        th_off = 60 + math.sin(ph + math.pi) * 35
    elif swinging and not is_backhand:
        th_off = 85 + 30 * math.sin(t * math.pi)
    elif not is_backhand:
        th_off = 40
    if not is_backhand:
        r = math.radians(th_off)
        off_hand = (shoulder[0] - side * math.sin(r) * arm * 0.9,
                    shoulder[1] + math.cos(r) * arm * 0.9)
        pygame.draw.line(screen, COL, shoulder, off_hand, 3)

    # racket arm
    if swinging:
        th = swing_angle(t)
    elif moving:
        th = 100 + math.sin(ph) * 15
    else:
        th = 70

    def racket_points(angle_deg):
        rr = math.radians(angle_deg)
        vx, vy = side * math.sin(rr), math.cos(rr)
        hand = (shoulder[0] + vx * arm, shoulder[1] + vy * arm)
        head = (hand[0] + vx * 17 * scale, hand[1] + vy * 17 * scale)
        return hand, head

    # racket swish trail during the forward swing
    if swinging and 0.35 <= t <= 0.8:
        for k in (3, 2, 1):
            tk = t - 0.035 * k
            if tk >= 0:
                _, trail_head = racket_points(swing_angle(tk))
                shade = 140 - k * 30
                trail_col = tuple(int(c * shade / 200) for c in COL)
                pygame.draw.circle(screen, trail_col,
                                   (int(trail_head[0]), int(trail_head[1])), int(9 * scale), 1)

    hand, head = racket_points(th)
    pygame.draw.line(screen, COL, shoulder, hand, 3)
    if is_backhand:
        # Two hands stay together on the handle throughout the backhand swing.
        support_shoulder = (sh[0] - side * 8 * scale, sh[1] + 3 * scale)
        support_hand = (hand[0] - side * 5 * scale, hand[1] - 5 * scale)
        pygame.draw.line(screen, COL, support_shoulder, support_hand, 3)
        pygame.draw.circle(screen, WHITE,(int(support_hand[0]), int(support_hand[1])),
                           max(2, int(3 * scale)))
    handle_end = (hand[0] + (head[0] - hand[0]) * 0.5, hand[1] + (head[1] - hand[1]) * 0.5)
    pygame.draw.line(screen, WHITE, hand, handle_end, 3)
    pygame.draw.circle(screen, WHITE, (int(head[0]), int(head[1])), max(4, int(9 * scale)), 2)
    pygame.draw.circle(screen, GLOW, (int(head[0]), int(head[1])), max(2, int(5 * scale)), 1)


def draw_court():
    """Court surface (grass / hard / clay) with neon-green theme lines."""
    pygame.draw.polygon(screen, court_color, COURT)

    if court_kind == "grass":
        # mowed stripes
        for k in range(0, 400, 50):
            y0, y1 = 120 + k, 120 + k + 25
            pygame.draw.polygon(screen, court_alt, [
                (court_left_x(y0), y0), (court_right_x(y0), y0),
                (court_right_x(y1), y1), (court_left_x(y1), y1)])
    elif court_kind == "clay":
        for (sx, sy) in clay_specks:
            pygame.draw.circle(screen, court_alt, (sx, sy), 1)

    pygame.draw.polygon(screen, LINE_WHITE, COURT, 4)
    pygame.draw.line(screen, LINE_WHITE, TOP_SERVICE_LEFT, TOP_SERVICE_RIGHT, 3)
    pygame.draw.line(screen, LINE_WHITE, BOT_SERVICE_LEFT, BOT_SERVICE_RIGHT, 3)
    pygame.draw.line(screen, LINE_WHITE, (CENTER_X, TOP_SERVICE_Y), (CENTER_X, BOT_SERVICE_Y), 3)


def draw_service_box(srv, deuce):
    """Soft white highlight of the box the serve will go to."""
    y0, y1, left = service_box(srv, deuce)
    if left:
        pts = [(court_left_x(y0), y0), (CENTER_X, y0), (CENTER_X, y1), (court_left_x(y1), y1)]
    else:
        pts = [(CENTER_X, y0), (court_right_x(y0), y0), (court_right_x(y1), y1), (CENTER_X, y1)]
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(overlay, (255, 255, 255, 55), pts)
    screen.blit(overlay, (0, 0))


def draw_net():
    """Neon-green and black tennis net across the middle of the court."""
    lx, ly = NET_LEFT
    rx, ry = NET_RIGHT

    # dark see-through backing so the net reads clearly over the blue court
    backing = pygame.Surface((rx - lx, NET_HEIGHT), pygame.SRCALPHA)
    backing.fill((0, 0, 0, 110))
    screen.blit(backing, (lx, ly - NET_HEIGHT))

    # vertical strings: alternate black and white
    num_strings = 18
    for i in range(num_strings + 1):
        t = i / num_strings
        nx = int(lx + (rx - lx) * t)
        ny = int(ly + (ry - ly) * t)
        color = NET_BLACK if i % 2 == 0 else LINE_WHITE
        pygame.draw.line(screen, color, (nx, ny), (nx, ny - NET_HEIGHT), 1)

    # horizontal strings: black and white
    for h, color, width in ((10, NET_BLACK, 2), (20, LINE_WHITE, 1),
                            (30, NET_BLACK, 2), (40, LINE_WHITE, 1)):
        pygame.draw.line(screen, color, (lx, ly - h), (rx, ry - h), width)

    # posts: black outline + white center
    for px, py in ((lx, ly), (rx, ry)):
        pygame.draw.line(screen, NET_BLACK, (px, py), (px, py - NET_HEIGHT - 5), 8)
        pygame.draw.line(screen, LINE_WHITE, (px, py), (px, py - NET_HEIGHT - 5), 4)

    # top tape: white band with black edge
    pygame.draw.line(screen, NET_BLACK, (lx, ly - NET_HEIGHT), (rx, ry - NET_HEIGHT), 8)
    pygame.draw.line(screen, LINE_WHITE, (lx, ly - NET_HEIGHT), (rx, ry - NET_HEIGHT), 4)


def draw_ball():
    render_ball_y = int(ball_y - max(0.0, ball_arc_y))
    pygame.draw.ellipse(screen, (20, 25, 40), (int(ball_x) - 6, int(ball_y) - 3, 12, 6))
    pygame.draw.circle(screen, BALL_YELLOW, (int(ball_x), render_ball_y), 8)
    pygame.draw.circle(screen, LINE_WHITE, (int(ball_x), render_ball_y), 8, 1)
    pygame.draw.circle(screen, (200, 225, 155), (int(ball_x), render_ball_y), 3)


def draw_scoreboard():
    """Vertical tennis scoreboard with players above the set-by-set results."""
    x0, y0 = 10, 8
    w = 205
    player_row_h = 25
    set_row_h = 20
    set_rows = len(completed_sets)
    h = 25 + player_row_h * 2 + 8 + max(1, set_rows) * set_row_h + 8

    pygame.draw.rect(screen, PANEL, (x0, y0, w, h), border_radius=5)
    pygame.draw.rect(screen, NEON_GREEN, (x0, y0, w, h), 2, border_radius=5)
    screen.blit(tiny_font.render("SCOREBOARD", True, NEON_GREEN), (x0 + 8, y0 + 5))
    pygame.draw.line(screen, DARK_GREEN, (x0 + 5, y0 + 24),
                     (x0 + w - 5, y0 + 24), 1)

    for i in range(2):
        y = y0 + 28 + i * player_row_h
        if server == i and not match_over:
            pygame.draw.circle(screen, WHITE, (x0 + 10, y + 9), 3)
        screen.blit(tiny_font.render(names[i], True, player_colors[i]), (x0 + 18, y + 2))
        games_text = str(games[i])
        screen.blit(tiny_font.render(games_text, True, NEON_GREEN), (x0 + 140, y + 2))
        if not match_over:
            ptxt = tiny_font.render(point_text(i), True, WHITE)
            screen.blit(ptxt, (x0 + 168, y + 2))

    sets_y = y0 + 28 + player_row_h * 2
    pygame.draw.line(screen, DARK_GREEN, (x0 + 5, sets_y), (x0 + w - 5, sets_y), 1)
    screen.blit(tiny_font.render("SETS", True, GLOW_GREEN), (x0 + 8, sets_y + 4))
    display_sets = list(completed_sets)
    for set_i, (p1_games, p2_games) in enumerate(display_sets):
        yy = sets_y + 22 + set_i * set_row_h
        screen.blit(tiny_font.render(f"SET {set_i + 1}", True, WHITE), (x0 + 8, yy))
        screen.blit(tiny_font.render(f"{p1_games} - {p2_games}", True, WHITE), (x0 + 145, yy))

    label = ""
    if in_tiebreak:
        label = "TIEBREAK"
    elif points[0] >= 3 and points[1] >= 3 and points[0] == points[1]:
        label = "DEUCE"
    if label and not match_over:
        screen.blit(tiny_font.render(label, True, WHITE), (x0 + 8, y0 + h - 16))


def draw_lawn_landscape():
    """Paint a neon-green cyberpunk city at night behind the court."""
    # Deep city-night gradient with a green horizon glow.
    sky_top = (2, 12, 7)
    sky_bottom = (5, 48, 20)
    for y in range(0, 310, 5):
        t = y / 310.0
        col = tuple(int(sky_top[i] * (1 - t) + sky_bottom[i] * t) for i in range(3))
        pygame.draw.rect(screen, col, (0, y, WIDTH, 5))

    # Soft neon haze behind the skyline.
    haze = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.ellipse(haze, (35, 175, 75, 32), (130, 115, 640, 210))
    pygame.draw.ellipse(haze, (65, 190, 90, 22), (250, 170, 400, 150))
    screen.blit(haze, (0, 0))

    # Moon and a sparse cyberpunk star field.
    pygame.draw.circle(screen, (150, 205, 145), (760, 72), 25)
    pygame.draw.circle(screen, (24, 82, 35), (750, 62), 7)
    for sx, sy, radius in ((85, 42, 2), (220, 74, 1), (340, 34, 2),
                           (480, 62, 1), (625, 38, 2), (850, 112, 1)):
        pygame.draw.circle(screen, (85, 190, 105), (sx, sy), radius)

    # Layered skyline silhouettes.
    far_buildings = [
        (0, 145, 82, 165), (92, 120, 150, 190), (160, 152, 225, 190),
        (238, 105, 300, 190), (314, 138, 370, 190), (390, 112, 445, 190),
        (468, 148, 535, 190), (558, 98, 628, 190), (646, 130, 710, 190),
        (730, 108, 805, 190), (822, 142, 900, 190),
    ]
    for left, top, right, bottom in far_buildings:
        pygame.draw.rect(screen, (4, 30, 14), (left, top, right - left, bottom - top))
        pygame.draw.line(screen, (18, 115, 52), (left, top), (right, top), 1)

    near_buildings = [
        (-20, 185, 115, 335), (100, 165, 205, 335), (192, 200, 315, 335),
        (300, 178, 410, 335), (398, 205, 505, 335), (492, 160, 625, 335),
        (610, 192, 720, 335), (700, 172, 825, 335), (805, 205, 930, 335),
    ]
    for index, (left, top, right, bottom) in enumerate(near_buildings):
        pygame.draw.rect(screen, (3, 22, 10), (left, top, right - left, bottom - top))
        pygame.draw.rect(screen, (8, 62, 25), (left, top, right - left, 3))
        # Green-lit windows create the city-light theme.
        for wx in range(left + 14, right - 8, 24):
            for wy in range(top + 18, min(bottom - 20, 320), 25):
                if (wx + wy + index * 17) % 5 != 0:
                    window_color = (55, 175, 85) if (wx + wy) % 3 else (115, 195, 80)
                    pygame.draw.rect(screen, window_color, (wx, wy, 7, 4))

    # Neon skyline edge and distant street lights.
    pygame.draw.line(screen, (75, 190, 95), (0, 335), (WIDTH, 335), 2)
    for x in range(30, WIDTH, 90):
        pygame.draw.line(screen, (30, 190, 75), (x, 335), (x, 410), 2)
        pygame.draw.circle(screen, (115, 200, 90), (x, 338), 4)

    # Dark reflective city street surrounding the court.
    pygame.draw.rect(screen, (2, 25, 10), (0, 335, WIDTH, HEIGHT - 335))
    for x in range(-HEIGHT, WIDTH + HEIGHT, 90):
        pygame.draw.polygon(screen, (4, 68, 24),
                            [(x, HEIGHT), (x + 52, HEIGHT),
                             (x + 150, 335), (x + 110, 335)])
    for x in range(0, WIDTH, 75):
        pygame.draw.line(screen, (20, 125, 52), (x, 510), (x + 70, 510), 2)

    # Neon sign panels behind the players.
    for rect in ((28, 235, 105, 30), (760, 245, 112, 30)):
        pygame.draw.rect(screen, (5, 28, 10), rect, border_radius=4)
        pygame.draw.rect(screen, (60, 180, 85), rect, 2, border_radius=4)

    # Court shadow and low silhouettes ground the trapezoid in the scene.
    shadow = [(x + 8, y + 12) for x, y in COURT]
    pygame.draw.polygon(screen, (0, 14, 5), shadow)
    for x in range(255, 651, 32):
        pygame.draw.circle(screen, (1, 16, 6), (x, 535), 5)
        pygame.draw.rect(screen, (1, 16, 6), (x - 4, 540, 8, 13))


# ---------------- MENUS ----------------
state = "menu"          # menu | options | select_player | select_opp | game
menu_sel = 0
card_sel = 0
frame = 0
running = True
paused = False
pause_continue_rect = pygame.Rect(WIDTH // 2 - 170, 180, 340, 55)
pause_quit_rect = pygame.Rect(WIDTH // 2 - 170, 250, 340, 55)

previews = [new_player(0.0, 0.0, ch['color'], ch['glow']) for ch in PLAYERS]
menu_hero_left = new_player(135.0, 470.0, NEON_GREEN, GLOW_GREEN)
menu_hero_right = new_player(710.0, 450.0, (150, 255, 55), (35, 145, 20))
menu_hero_left['stroke'] = 'forehand'
menu_hero_right['stroke'] = 'backhand'
menu_hero_left['side'] = 1
menu_hero_right['side'] = -1


def blit_center(text, f, color, cx, y):
    surf = f.render(text, True, color)
    screen.blit(surf, (cx - surf.get_width() // 2, y))


def wrap_text(text, f, max_w):
    lines, cur = [], ""
    for word in text.split():
        test = (cur + " " + word).strip()
        if f.size(test)[0] <= max_w:
            cur = test
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_menu_bg():
    screen.fill(BLACK)
    pygame.draw.polygon(screen, DARK_GREEN, COURT, 2)
    pygame.draw.line(screen, DARK_GREEN, NET_LEFT, NET_RIGHT, 2)
    pygame.draw.line(screen, DARK_GREEN, (CENTER_X, TOP_SERVICE_Y), (CENTER_X, BOT_SERVICE_Y), 1)


def menu_labels():
    if state == "menu":
        return ["PLAY", "OPTIONS", "QUIT"]
    serve_label = {"point": "POINT", "game": "GAME", "set": "SET"}[SERVE_CHANGE]
    return [f"MATCH: FIRST TO {SETS_TO_WIN} SETS",
            "SERVE CHANGES: AFTER EACH " + serve_label,
            "BACK"]


def menu_buttons(n):
    return [pygame.Rect(WIDTH // 2 - 190, 240 + i * 78, 380, 58) for i in range(n)]


def draw_button(rect, text, selected):
    if selected:
        pygame.draw.rect(screen, DARK_GREEN, rect, border_radius=10)
        pygame.draw.rect(screen, NEON_GREEN, rect, 3, border_radius=10)
        color = WHITE
    else:
        pygame.draw.rect(screen, PANEL, rect, border_radius=10)
        pygame.draw.rect(screen, GLOW_GREEN, rect, 2, border_radius=10)
        color = NEON_GREEN
    blit_center(text, font, color, rect.centerx, rect.centery - 11)


def draw_menu():
    draw_menu_bg()
    if state == "menu":
        # Decorative tennis players frame the main menu and show the racket gameplay.
        menu_hero_left['phase'] = 0.0
        menu_hero_right['phase'] = 0.0
        menu_hero_left['moving'] = False
        menu_hero_right['moving'] = False
        menu_hero_left['swing'] = 0
        menu_hero_right['swing'] = 0
        menu_hero_left['lean'] = 0.0
        menu_hero_right['lean'] = 0.0
        draw_player(menu_hero_left, 2.15)
    blit_center("MICO TENNIS", title_font, GLOW_GREEN, WIDTH // 2 + 3, 63)
    blit_center("MICO TENNIS", title_font, NEON_GREEN, WIDTH // 2, 60)
    sub = "MAIN MENU" if state == "menu" else "OPTIONS"
    blit_center(sub, font, WHITE, WIDTH // 2, 165)
    labels = menu_labels()
    for i, rect in enumerate(menu_buttons(len(labels))):
        draw_button(rect, labels[i], i == menu_sel)
    hint = "UP / DOWN + ENTER  or  click"
    if state == "options":
        hint = "LEFT / RIGHT or ENTER to change    ESC = back"
    blit_center(hint, tiny_font, GLOW_GREEN, WIDTH // 2, HEIGHT - 40)


def card_rect(i):
    return pygame.Rect(18 + i * 220, 100, 205, 400)


def draw_bar(x, y, w, label, value, color=NEON_GREEN, glow=GLOW_GREEN, show_pct=True):
    text = f"{label} {int(value * 100)}%" if show_pct else label
    screen.blit(tiny_font.render(text, True, WHITE), (x, y))
    pygame.draw.rect(screen, DARK_GREEN, (x, y + 18, w, 10))
    pygame.draw.rect(screen, color, (x, y + 18, int(w * value), 10))
    pygame.draw.rect(screen, glow, (x, y + 18, w, 10), 1)


def draw_select():
    draw_menu_bg()
    title = "CHOOSE YOUR PLAYER" if state == "select_player" else "CHOOSE YOUR OPPONENT"
    blit_center(title, big_font, NEON_GREEN, WIDTH // 2, 14)
    if state == "select_opp":
        blit_center(f"YOU: {PLAYERS[p1_choice]['name']}", small_font, WHITE, WIDTH // 2, 68)
    else:
        blit_center("PLAYER 1", small_font, WHITE, WIDTH // 2, 68)

    for i, ch in enumerate(PLAYERS):
        rect = card_rect(i)
        selected = (i == card_sel)
        pygame.draw.rect(screen, DARK_GREEN if selected else PANEL, rect, border_radius=10)
        pygame.draw.rect(screen, ch['color'] if selected else ch['glow'], rect, 3 if selected else 1,
                         border_radius=10)

        pad = 14
        cx = rect.centerx
        blit_center(ch['first'], small_font, ch['color'], cx, rect.y + 10)
        blit_center(ch['last'], small_font, ch['color'], cx, rect.y + 32)

        # animated preview (runs, then swings) on the highlighted card
        pv = previews[i]
        pv['x'], pv['y'] = float(cx), float(rect.y + 112)
        if selected:
            c = frame % 160
            pv['moving'] = c < 80
            if pv['moving']:
                pv['phase'] += 0.30
            if c == 80:
                start_swing(pv, cx + 50)
            if pv['swing'] > 0:
                pv['swing'] -= 1
        else:
            pv['moving'] = False
            pv['swing'] = 0
        draw_player(pv, 1.0)

        # description
        yy = rect.y + 150
        for line in wrap_text(ch['tag'], tiny_font, rect.w - 2 * pad):
            screen.blit(tiny_font.render(line, True, WHITE), (rect.x + pad, yy))
            yy += 16

        # stats
        yy = rect.y + 212
        for label, val in ch['stats']:
            screen.blit(tiny_font.render(f"{label}: {val}", True, ch['color']), (rect.x + pad, yy))
            yy += 17

        # speed / return bars
        draw_bar(rect.x + pad, rect.y + 300, rect.w - 2 * pad, "RUNNING SPEED", ch['speed'], ch['color'], ch['glow'])
        draw_bar(rect.x + pad, rect.y + 345, rect.w - 2 * pad, "BALL RETURN", ch['ret'], ch['color'], ch['glow'])

    blit_center("LEFT / RIGHT or mouse to choose    ENTER / click = confirm    ESC = back",
                tiny_font, GLOW_GREEN, WIDTH // 2, HEIGHT - 60)


def court_rect(i):
    return pygame.Rect(20 + i * 295, 100, 270, 400)


def draw_court_select():
    draw_menu_bg()
    blit_center("CHOOSE YOUR COURT", big_font, NEON_GREEN, WIDTH // 2, 14)
    blit_center(f"{PLAYERS[p1_choice]['name']}  VS  {PLAYERS[opp_choice]['name']}",
                small_font, WHITE, WIDTH // 2, 68)

    for i, c in enumerate(COURTS):
        rect = court_rect(i)
        selected = (i == card_sel)
        pygame.draw.rect(screen, DARK_GREEN if selected else PANEL, rect, border_radius=10)
        pygame.draw.rect(screen, NEON_GREEN if selected else GLOW_GREEN, rect, 3 if selected else 1,
                         border_radius=10)
        cx = rect.centerx
        blit_center(c['name'], small_font, NEON_GREEN, cx, rect.y + 10)
        blit_center(c['event'], small_font, WHITE, cx, rect.y + 30)

        # mini court preview
        px, pw = rect.x + 30, rect.w - 60
        py, ph = rect.y + 58, 100

        def edge_l(t):
            return px + pw * 0.25 * (1 - t)

        def edge_r(t):
            return px + pw * (0.75 + 0.25 * t)

        pts = [(edge_l(0), py), (edge_r(0), py), (edge_r(1), py + ph), (edge_l(1), py + ph)]
        pygame.draw.polygon(screen, c['color'], pts)
        if c['kind'] == 'grass':
            for k in range(0, 100, 20):
                t0, t1 = k / 100.0, (k + 10) / 100.0
                pygame.draw.polygon(screen, c['alt'], [
                    (edge_l(t0), py + k), (edge_r(t0), py + k),
                    (edge_r(t1), py + k + 10), (edge_l(t1), py + k + 10)])
        elif c['kind'] == 'clay':
            for (sx, sy) in clay_specks[:50]:
                u = (sx - 80) / 740.0
                v = (sy - 120) / 400.0
                pygame.draw.circle(screen, c['alt'], (int(px + u * pw), int(py + v * ph)), 1)
        pygame.draw.polygon(screen, LINE_WHITE, pts, 2)
        for t in (0.25, 0.75):
            pygame.draw.line(screen, LINE_WHITE, (edge_l(t), py + ph * t), (edge_r(t), py + ph * t), 1)
        pygame.draw.line(screen, LINE_WHITE, (px + pw / 2, py + ph * 0.25), (px + pw / 2, py + ph * 0.75), 1)
        pygame.draw.line(screen, NET_BLACK, (edge_l(0.46) - 6, py + ph * 0.46 + 2),
                         (edge_r(0.46) + 6, py + ph * 0.46 + 2), 3)
        pygame.draw.line(screen, LINE_WHITE, (edge_l(0.46) - 6, py + ph * 0.46),
                         (edge_r(0.46) + 6, py + ph * 0.46), 3)

        # headline + bullet points
        blit_center(c['headline'], small_font, WHITE, cx, rect.y + 172)
        yy = rect.y + 208
        for b in c['bullets']:
            screen.blit(tiny_font.render("- " + b, True, NEON_GREEN), (rect.x + 18, yy))
            yy += 18

        # gameplay bars
        draw_bar(rect.x + 16, rect.y + 318, rect.w - 32, "BALL SPEED", c['bar_speed'],
                 NEON_GREEN, GLOW_GREEN, show_pct=False)
        draw_bar(rect.x + 16, rect.y + 355, rect.w - 32, "BALL BOUNCE", c['bar_bounce'],
                 NEON_GREEN, GLOW_GREEN, show_pct=False)

    blit_center("LEFT / RIGHT or mouse to choose    ENTER / click = next    ESC = back",
                tiny_font, GLOW_GREEN, WIDTH // 2, HEIGHT - 60)


def draw_racket_select():
    draw_menu_bg()
    blit_center("CHOOSE YOUR RACKET", big_font, NEON_GREEN, WIDTH // 2, 14)
    blit_center(f"{PLAYERS[p1_choice]['name']}  VS  {PLAYERS[opp_choice]['name']}   |   "
                f"{COURTS[court_choice]['name']}", small_font, WHITE, WIDTH // 2, 68)

    for i, racket in enumerate(RACKETS):
        rect = card_rect(i)
        selected = (i == card_sel)
        pygame.draw.rect(screen, DARK_GREEN if selected else PANEL, rect, border_radius=10)
        pygame.draw.rect(screen, racket['color'] if selected else racket['glow'], rect,
                         3 if selected else 1, border_radius=10)

        cx = rect.centerx
        name_lines = wrap_text(racket['name'], small_font, rect.w - 20)
        for line_i, line in enumerate(name_lines):
            blit_center(line, small_font, racket['color'], cx, rect.y + 12 + line_i * 22)

        # Simple racket silhouette to make the cards visually distinct.
        racket_y = rect.y + 105
        pygame.draw.ellipse(screen, racket['color'],
                            (cx - 25, racket_y - 25, 50, 64), 3)
        pygame.draw.line(screen, racket['color'], (cx, racket_y + 37),
                         (cx, racket_y + 85), 4)
        pygame.draw.line(screen, WHITE, (cx - 18, racket_y - 3),
                         (cx + 18, racket_y + 17), 1)
        pygame.draw.line(screen, WHITE, (cx + 18, racket_y - 3),
                         (cx - 18, racket_y + 17), 1)

        yy = rect.y + 205
        for label, value in racket['stats']:
            draw_bar(rect.x + 14, yy, rect.w - 28, label, value,
                     racket['color'], racket['glow'])
            yy += 37

    blit_center("LEFT / RIGHT or mouse to choose    ENTER / click = confirm    ESC = back",
                tiny_font, GLOW_GREEN, WIDTH // 2, HEIGHT - 60)


def activate_button(i):
    global state, menu_sel, card_sel, SETS_TO_WIN, SERVE_CHANGE, running
    if state == "menu":
        if i == 0:
            state = "select_player"
            card_sel = p1_choice
        elif i == 1:
            state = "options"
            menu_sel = 0
        else:
            running = False
    else:  # options
        if i == 0:
            current = SET_OPTIONS.index(SETS_TO_WIN)
            SETS_TO_WIN = SET_OPTIONS[(current + 1) % len(SET_OPTIONS)]
        elif i == 1:
            SERVE_CHANGE = {"point": "game", "game": "set", "set": "point"}[SERVE_CHANGE]
        else:
            state = "menu"
            menu_sel = 2


def confirm_card():
    global state, card_sel, p1_choice, opp_choice, court_choice, racket_choice
    if state == "select_player":
        p1_choice = card_sel
        state = "select_opp"
        card_sel = opp_choice
    elif state == "select_opp":
        opp_choice = card_sel
        state = "select_court"
        card_sel = court_choice
    elif state == "select_court":
        court_choice = card_sel
        state = "select_racket"
        card_sel = racket_choice
    else:  # select_racket
        racket_choice = card_sel
        start_match()
        state = "game"


def handle_menu_events(events):
    global state, menu_sel, card_sel, running
    for e in events:
        if e.type == pygame.QUIT:
            running = False
            continue

        if state in ("menu", "options"):
            rects = menu_buttons(len(menu_labels()))
            n = len(rects)
            if e.type == pygame.MOUSEMOTION:
                for i, r in enumerate(rects):
                    if r.collidepoint(e.pos):
                        menu_sel = i
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i, r in enumerate(rects):
                    if r.collidepoint(e.pos):
                        menu_sel = i
                        activate_button(i)
                        break
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_UP, pygame.K_w):
                    menu_sel = (menu_sel - 1) % n
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    menu_sel = (menu_sel + 1) % n
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    activate_button(menu_sel)
                elif state == "options" and e.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d):
                    if menu_sel in (0, 1):
                        activate_button(menu_sel)
                elif e.key == pygame.K_ESCAPE and state == "options":
                    state = "menu"
                    menu_sel = 1
        else:  # player / opponent / court / racket selection
            if state == "select_court":
                rect_of, n = court_rect, len(COURTS)
            elif state == "select_racket":
                rect_of, n = card_rect, len(RACKETS)
            else:
                rect_of, n = card_rect, len(PLAYERS)
            if e.type == pygame.MOUSEMOTION:
                for i in range(n):
                    if rect_of(i).collidepoint(e.pos):
                        card_sel = i
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i in range(n):
                    if rect_of(i).collidepoint(e.pos):
                        card_sel = i
                        confirm_card()
                        break
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_LEFT, pygame.K_a):
                    card_sel = (card_sel - 1) % n
                elif e.key in (pygame.K_RIGHT, pygame.K_d):
                    card_sel = (card_sel + 1) % n
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    confirm_card()
                elif e.key == pygame.K_ESCAPE:
                    if state == "select_racket":
                        state = "select_court"
                        card_sel = court_choice
                    elif state == "select_court":
                        state = "select_opp"
                        card_sel = opp_choice
                    elif state == "select_opp":
                        state = "select_player"
                        card_sel = p1_choice
                    else:
                        state = "menu"
                        menu_sel = 0


# ====================== MVC ARCHITECTURE ======================
# MVC components live in mvc_model.py, mvc_view.py, and mvc_controller.py.
mvc_game_context = sys.modules[__name__]
mvc_model = GameModel(mvc_game_context)
mvc_view = GameView(mvc_game_context, mvc_model)
mvc_controller = GameController(mvc_game_context, mvc_model, mvc_view)


# ====================== MAIN LOOP ======================
while running:
    clock.tick(60)
    frame += 1
    events = pygame.event.get()

    # F11 toggles fullscreen from menus, selection screens, pause, or gameplay.
    for event in events:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            toggle_fullscreen()

    # ---------- MENU SCREENS ----------
    if state != "game":
        mvc_controller.handle_menu(events)
        mvc_view.render_menu_state()
        pygame.display.flip()
        continue

    # ---------- GAME ----------
    screen.fill(BLACK)

    space_pressed = mvc_controller.handle_game_input(events)

    if state != "game":
        continue

    if paused:
        # Draw the current frame without advancing movement, ball physics,
        # score pauses, serve timers, or animation timers.
        mvc_view.render_paused_game()
        pygame.display.flip()
        continue

    # ---------------- PLAYER CONTROLS (WASD) ----------------
    keys = pygame.key.get_pressed()
    dir_x = (1 if keys[pygame.K_d] else 0) - (1 if keys[pygame.K_a] else 0)
    dir_y = (1 if keys[pygame.K_s] else 0) - (1 if keys[pygame.K_w] else 0)
    # Left click = backhand on the player's left side; right click = forehand
    # on the player's right side. Hold the correct button while positioned.
    mouse_buttons = pygame.mouse.get_pressed()
    if mouse_buttons[0]:
        player_stroke = 'backhand'
    elif mouse_buttons[2]:
        player_stroke = 'forehand'
    else:
        player_stroke = None
    # court_grip = 1.0 -> stop instantly; small value (clay) -> you slide
    p1_vel[0] += (dir_x * p1_speed - p1_vel[0]) * court_grip
    p1_vel[1] += (dir_y * p1_speed - p1_vel[1]) * court_grip
    p1['x'] += p1_vel[0]
    p1['y'] += p1_vel[1]

    # keep player inside their half of the court
    p1['x'] = max(150.0, min(p1['x'], 750.0))
    p1['y'] = max(430.0, min(p1['y'], 520.0))

    if serve_phase == "wait" and server == 0:
        p1['x'], p1['y'] = serve_spot      # you stand still while serving
        p1_vel[0] = p1_vel[1] = 0.0

    if match_over:
        pass  # game frozen, waiting for R to restart
    elif pause_timer > 0:
        # Short pause after a point, then serve again
        pause_timer -= 1
        if pause_timer == 0:
            message = ""
            serve(server, next_second_serve)
            next_second_serve = False
    elif serve_phase == "wait":
        # ball is tossed; SPACE (or the timer) hits the serve
        serve_timer -= 1
        ball_arc_y = 34 + 5 * math.sin(frame * 0.15)
        if (server == 0 and (space_pressed or serve_timer <= 0)) or (server == 1 and serve_timer <= 0):
            launch_serve()
    else:
        # ---------------- MOVE BALL ----------------
        ball_x += ball_vx
        ball_y += ball_vy
        ball_arc_y += ball_arc_vy
        ball_arc_vy -= 0.18

        if ball_x < 150:
            ball_x = 150
            ball_vx = -ball_vx
        elif ball_x > 750:
            ball_x = 750
            ball_vx = -ball_vx

        # ---------------- SERVE LANDING / FAULTS ----------------
        if serve_phase == "flying":
            serve_frames_left -= 1
            if serve_frames_left <= 0:
                serve_phase = None
                ball_arc_y = 0.0
                serve_mark = [ball_x, ball_y, 50]
                if serve_is_fault:
                    ball_vx = ball_vy = 0.0
                    if second_serve:
                        point_scored(1 - server, "DOUBLE FAULT!")
                    else:
                        message = "FAULT!"
                        pause_timer = 60
                        next_second_serve = True
                else:
                    ball_arc_vy = 3.2 * court_bounce      # small hop after the bounce
                    ball_vx *= 0.5

        # ---------------- OPPONENT (P2) MOVEMENT ----------------
        if ball_vy < 0:
            # Ball heading to the opponent
            if p2_will_miss:
                target_x = ball_x + p2_miss_offset   # chases the wrong spot
                speed = p2_speed * 0.6
            else:
                target_x = ball_x
                speed = p2_speed
                if ball_y <= 230:
                    speed = max(speed, 7.0)          # final dash so it reaches the ball
            target_x = max(150.0, min(target_x, 750.0))

            if p2['x'] < target_x:
                p2['x'] += min(speed, target_x - p2['x'])
            elif p2['x'] > target_x:
                p2['x'] -= min(speed, p2['x'] - target_x)
        else:
            # Ball heading to player: opponent drifts back to center
            p2['x'] += (CENTER_X - p2['x']) * 0.05

        # ---------------- RACKET SWING TRIGGERS ----------------
        # Opponent swings as the ball arrives (whiffs if it is going to miss)
        if ball_vy < 0 and 100 < ball_y <= 180:
            start_swing(p2, ball_x)
        # Player chooses the stroke: E for forehand, Q for backhand.
        if (ball_vy > 0 and player_stroke
                and p1['y'] - 55 <= ball_y <= p1['y'] + 30
                and abs(ball_x - p1['x']) <= P1_REACH_X + 25
                and player_stroke == stroke_for_ball(p1, ball_x)):
            start_swing(p1, ball_x, player_stroke)

        # ---------------- TOP SIDE (P2) LOGIC ----------------
        if ball_vy < 0 and not bounced_top and ball_y <= 220:
            ball_arc_y = 0.0
            ball_arc_vy = 3.2 * court_bounce
            bounced_top = True

        if ball_vy < 0 and ball_y <= 135:
            if not p2_will_miss:
                # Opponent returns the ball
                ball_vy = 4.5 * court_speed
                ball_arc_y = 0.0
                ball_arc_vy = 4.2 * court_bounce
                random_target_x = random.randint(250, 650)
                ball_vx = (random_target_x - ball_x) * court_speed / 70.0
                bounced_top = False
                bounced_bottom = False
                decide_player()       # uses YOUR return %
            elif ball_y <= 90:
                # Opponent missed -> you win the point
                point_scored(0)

        # ---------------- BOTTOM SIDE (P1) LOGIC ----------------
        if pause_timer == 0 and not match_over:
            if ball_vy > 0 and not bounced_bottom and ball_y >= 400:
                ball_arc_y = 0.0
                ball_arc_vy = 3.2 * court_bounce
                bounced_bottom = True

            if ball_vy > 0 and p1['y'] - 15 <= ball_y <= p1['y'] + 40:
                correct_stroke = player_stroke == stroke_for_ball(p1, ball_x)
                if (abs(ball_x - p1['x']) <= P1_REACH_X
                        and correct_stroke and p1_will_return):
                    # Player hits the ball back
                    start_swing(p1, ball_x, player_stroke)
                    ball_vy = -4.5 * court_speed
                    ball_arc_y = 0.0
                    ball_arc_vy = 4.2 * court_bounce
                    random_target_x = random.randint(250, 650)
                    ball_vx = (random_target_x - ball_x) * court_speed / 70.0
                    bounced_bottom = False
                    bounced_top = False
                    decide_opponent()     # uses the opponent's return %

            if ball_vy > 0 and ball_y > p1['y'] + 40:
                # Player missed -> CPU wins the point
                point_scored(1)

    update_anim(p1)
    update_anim(p2)

    # ---------------- RENDER ----------------
    draw_court()

    if serve_phase == "wait" and not match_over:
        draw_service_box(server, serve_deuce)       # shows where the serve will go
    if serve_mark and serve_mark[2] > 0:
        pygame.draw.ellipse(screen, LINE_WHITE,
                            (int(serve_mark[0]) - 11, int(serve_mark[1]) - 5, 22, 10), 2)
        serve_mark[2] -= 1

    draw_player(p2, 0.7)

    if ball_y < 300:
        draw_ball()

    draw_net()

    if ball_y >= 300:
        draw_ball()

    draw_player(p1, 1.1)

    draw_scoreboard()

    help_text = small_font.render("W A S D = move    Left click = backhand    Right click = forehand    ESC = menu",
                                  True, GLOW_GREEN)
    screen.blit(help_text, (20, HEIGHT - 32))

    if message:
        msg = big_font.render(message, True, WHITE)
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 70))
    if serve_phase == "wait" and server == 0 and not match_over and pause_timer == 0:
        blit_center("PRESS SPACE TO SERVE", font, WHITE, WIDTH // 2, 80)
    if match_over and match_winner is not None:
        # Final result panel shown after the deciding set.
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 125))
        screen.blit(overlay, (0, 0))
        panel = pygame.Rect(170, 125, 560, 285)
        pygame.draw.rect(screen, PANEL, panel, border_radius=14)
        pygame.draw.rect(screen, NEON_GREEN, panel, 3, border_radius=14)
        loser = 1 - match_winner
        blit_center("MATCH COMPLETE", big_font, WHITE, WIDTH // 2, 145)
        blit_center(f"WINNER: {names[match_winner]}", font,
                    player_colors[match_winner], WIDTH // 2, 210)
        blit_center(f"LOSER: {names[loser]}", font,
                    player_colors[loser], WIDTH // 2, 250)
        set_scores = "   ".join(f"{a}-{b}" for a, b in completed_sets)
        blit_center(f"SET SCORES: {set_scores}", small_font, WHITE, WIDTH // 2, 295)
        blit_center("Press R to play again    ESC to return to menu", small_font,
                    NEON_GREEN, WIDTH // 2, 355)

    pygame.display.flip()

pygame.quit()
sys.exit()
