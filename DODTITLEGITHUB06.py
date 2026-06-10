import pyxel
import random
import math
import os
import subprocess  # ★ 外部プロセス（taskkillなど）を制御するために追加

# --- 定数 ---
WINDOW_W = 160
WINDOW_H = 120

PLAYER_SPEED = 1.7
PLAYER_R = 5
ZOMBIE_R = 4

SANCTUARY_W = 16
MAX_STAGE_PLAY = 5
ZOMBIE_COUNT_BASE = 6
TRANSFORM_DURATION = 240
FOLLOW_DISTANCE = 12
TRAIL_MAX_LENGTH = 200
FINAL_SCENE_HOLD_TIME = 180
UI_HEIGHT = 20
CREDITS_SPEED = 0.5
GAMEOVER_HOLD_TIME = 120

BASE_TIME_LIMIT = 18.0
BONUS_TIME_AFTER_CLEAR = 5.0
FINAL_STAGE_ZOMBIES = 30
FINAL_STAGE_TIME_LIMIT_MIN = 4.5

# --- 動画の再生時間設定（フレーム数：1秒 = 30フレーム） ---
# 動画の長さに合わせて、ここの数値を微調整してください。
VIDEO_DURATION_CARD = 330  # 他3つの動画の再生時間（約11秒分）

GAMEPAD_DPAD_UP = pyxel.GAMEPAD1_BUTTON_DPAD_UP
GAMEPAD_DPAD_DOWN = pyxel.GAMEPAD1_BUTTON_DPAD_DOWN
GAMEPAD_DPAD_LEFT = pyxel.GAMEPAD1_BUTTON_DPAD_LEFT
GAMEPAD_DPAD_RIGHT = pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT

GAMEPAD_A_ID = pyxel.GAMEPAD1_BUTTON_A
GAMEPAD_START_ID = pyxel.GAMEPAD1_BUTTON_START
GAMEPAD_Y_ID = pyxel.GAMEPAD1_BUTTON_Y

def clamp(v, a, b):
    return max(a, min(b, v))

def dist(ax, ay, bx, by):
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5

def center_text_x(text):
    return (WINDOW_W - len(text) * 4) // 2

CREDITS_CONTENT = [
    (16, "DEMOCRACY OF THE DEAD", 8),
    (8, "---", 7),
    (12, "GAME DESIGN & CONCEPT", 11),
    (12, "Y. K", 7),
    (8, "", 0),
    (12, "PROGRAMMING & GRAPHICS", 11),
    (12, "M. T", 7),
    (8, "", 0),
    (12, "SPECIAL THANKS TO:", 11),
    (12, "Team T.d", 7),
    (12, "All Players", 7),
    (8, "", 0),
    (12, "TEST PLAYERS", 11),
    (12, "Team T.d", 7),
    (12, "M. T", 7),
    (8, "", 0),
    (16, "THANK YOU FOR PLAYING!", 13),
    (8, "---", 7),
    (12, "Presented by MIRAI WORK", 13),
    (8, "---", 7),
    (12, "SEE YOU AGAIN!", 8),
    (WINDOW_H, "", 0)
]

class Player:
    def __init__(self, x, y, is_main=True, color_override=None):
        self.x, self.y = x, y
        self.dir = 1
        self.walk_frame = 0
        self.color = color_override if color_override is not None else 11
        self.is_main = is_main
        self.is_zombified = False
        self.temp_color = None
        self.dust_particles = []
        self.transform_particles = []
        if is_main:
            self.trail = [(x, y)] * TRAIL_MAX_LENGTH

    def update(self, obstacles, controllable=True):
        for p in self.transform_particles:
            p[0] += p[2]
            p[1] += p[3]
            p[5] -= 1
            p[3] += 0.05
        self.transform_particles = [p for p in self.transform_particles if p[5] > 0]

        if not self.is_main:
            return

        dx, dy = 0, 0
        if controllable and not self.is_zombified:
            sp = PLAYER_SPEED
            if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(GAMEPAD_DPAD_LEFT):
                dx = -sp
            elif pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(GAMEPAD_DPAD_RIGHT):
                dx = sp

            if pyxel.btn(pyxel.KEY_UP) or pyxel.btn(GAMEPAD_DPAD_UP):
                dy = -sp
            elif pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(GAMEPAD_DPAD_DOWN):
                dy = sp

            if dx != 0 and dy != 0:
                diag_factor = 1.0 / math.sqrt(2)
                dx *= diag_factor
                dy *= diag_factor

        moved = (dx != 0 or dy != 0)
        if moved:
            self.walk_frame = (self.walk_frame + 1) % 16
            self.x += dx
            self.y += dy

            if pyxel.frame_count % 3 == 0:
                self.dust_particles.append([self.x + random.randint(-2, 2), self.y + random.randint(2, 4),
                                             random.uniform(-0.5, 0.5), random.uniform(-0.5, 0), 6, 15])

            if dx > 0: self.dir = 1
            elif dx < 0: self.dir = -1

        self.x = clamp(self.x, PLAYER_R, WINDOW_W - 1 - PLAYER_R)
        self.y = clamp(self.y, UI_HEIGHT + PLAYER_R, WINDOW_H - 1 - PLAYER_R)

        if self.is_main and not self.is_zombified:
            self.trail.insert(0, (self.x, self.y))
            self.trail = self.trail[:TRAIL_MAX_LENGTH]

        for p in self.dust_particles:
            p[0] += p[2]
            p[1] += p[3]
            p[5] -= 1
        self.dust_particles = [p for p in self.dust_particles if p[5] > 0]

    def spawn_transform_particle(self, color):
        for _ in range(random.randint(1, 4)):
            self.transform_particles.append(
                [self.x + random.uniform(-5, 5), self.y + random.uniform(-10, 0),
                 random.uniform(-1.5, 1.5), random.uniform(-2.5, -0.8),
                 color, random.randint(15, 40)]
            )

    def draw(self):
        x, y = int(self.x), int(self.y)
        c = self.temp_color if self.temp_color is not None else self.color
        wf = (self.walk_frame // 4)
        foot_offset = [0, 1, -1, 0][wf]

        for p in self.dust_particles:
            pyxel.pset(int(p[0]), int(p[1]), p[4])
        for p in self.transform_particles:
            pyxel.rect(int(p[0]), int(p[1]), 1, 1, p[4])

        pyxel.circ(x, y + 3, 4, 0)
        pyxel.circ(x, y + 3, 3, 1)

        if self.is_zombified:
            z_c = 3
            pyxel.rect(x - 3, y - 3, 6, 6, z_c)
            pyxel.rect(x - 2, y - 2, 4, 4, z_c + 1)
            pyxel.circ(x, y - 5, 2, z_c)
            pyxel.pset(x + self.dir, y - 5, 8)
            pyxel.pset(x - self.dir, y - 5, 8)
            return

        pyxel.rect(x - 3, y - 3, 6, 6, c)
        pyxel.rect(x - 2, y - 2, 4, 4, c - 1)
        pyxel.rect(x - 1, y - 1, 2, 2, c - 2)

        pyxel.rect(x - 3, y + 3 + foot_offset, 6, 2, c)
        pyxel.rect(x - 2, y + 3 + foot_offset, 4, 1, c - 1)

        pyxel.circ(x, y - 6, 3, 6)
        pyxel.circ(x, y - 6, 2, 7)
        pyxel.pset(x - 1, y - 7, 7)

        eye_offset = 0
        if pyxel.frame_count % 120 < 5:
            eye_offset = 1
        pyxel.line(x + self.dir * 1, y - 6 - eye_offset, x + self.dir * 1, y - 6 + eye_offset, 0)

        hair_offset = 0
        if pyxel.frame_count % 16 < 8:
            hair_offset = 1

        hair_color = 5
        if c == 7: hair_color = 12
        elif c == 8: hair_color = 6

        pyxel.pset(x - 2 * self.dir, y - 7 - hair_offset, hair_color)


class Zombie:
    def __init__(self, x, y, speed_factor=1.0, global_speed_multiplier=1.0):
        self.x, self.y = x, y
        self.vx = random.uniform(-0.4, 0.4)
        self.vy = random.uniform(-0.4, 0.4)
        self.dir = 1
        self.state = "wander"
        self.speed_factor = speed_factor * global_speed_multiplier
        self.base_color = random.choice([3, 11, 4])
        self.captured_particles = []

    def update(self, player, obstacles, captured_zombies):
        px, py = player.x, player.y
        d = dist(self.x, self.y, px, py)

        if self.state == "captured":
            try:
                index = captured_zombies.index(self)
            except ValueError:
                index = 0
            target_index = min(len(player.trail) - 1, (index + 1) * FOLLOW_DISTANCE)
            target_pos = player.trail[target_index]
            tx, ty = target_pos

            td = dist(self.x, self.y, tx, ty)
            sp = 1.0 * self.speed_factor

            if td > 1.0:
                self.vx = (tx - self.x) / td * sp
                self.vy = (ty - self.y) / td * sp
            else:
                self.vx, self.vy = 0, 0

            self.x += self.vx
            self.y += self.vy

            if abs(self.vx) > 0.1:
                self.dir = 1 if self.vx > 0 else -1

            for p in self.captured_particles:
                p[0] += p[2]
                p[1] += p[3]
                p[5] -= 1
            self.captured_particles = [p for p in self.captured_particles if p[5] > 0]

            self.x = clamp(self.x, ZOMBIE_R, WINDOW_W - 1 - ZOMBIE_R)
            self.y = clamp(self.y, UI_HEIGHT + ZOMBIE_R, WINDOW_H - 1 - ZOMBIE_R)
            return

        if d < PLAYER_R + ZOMBIE_R and self.state != "captured" and not player.is_zombified:
            self.state = "captured"
            self.vx, self.vy = 0, 0
            pyxel.play(3, 8)
            for _ in range(random.randint(5, 10)):
                self.captured_particles.append([self.x, self.y, random.uniform(-1, 1), random.uniform(-1, -0.5), random.choice([7, 8, 3]), 30])
            return

        if not player.is_zombified:
            if d < 45:
                self.state = "follow"
                if d != 0:
                    self.vx += (px - self.x) / d * 0.1
                    self.vy += (py - self.y) / d * 0.1
            else:
                self.state = "wander"
                if random.random() < 0.02:
                    self.vx = random.uniform(-0.5, 0.5)
                    self.vy = random.uniform(-0.5, 0.5)

        v_len = dist(0, 0, self.vx, self.vy)
        max_v = 1.0 * self.speed_factor
        if v_len > max_v and v_len != 0:
            self.vx *= max_v / v_len
            self.vy *= max_v / v_len

        nx = self.x + self.vx
        ny = self.y + self.vy

        sanctuary_boundary = WINDOW_W - SANCTUARY_W
        if nx > sanctuary_boundary - ZOMBIE_R:
            if self.x <= sanctuary_boundary - ZOMBIE_R:
                self.vx = 0
            nx = self.x

        self.x, self.y = nx, ny
        self.dir = 1 if self.vx > 0 else (-1 if self.vx < 0 else self.dir)

        self.x = clamp(self.x, ZOMBIE_R, WINDOW_W - 1 - ZOMBIE_R)
        self.y = clamp(self.y, UI_HEIGHT + ZOMBIE_R, WINDOW_H - 1 - ZOMBIE_R)

    def draw(self):
        x, y = int(self.x), int(self.y)
        for p in self.captured_particles:
            pyxel.pset(int(p[0]), int(p[1]), p[4])

        pyxel.circ(x, y + 3, 4, 0)
        pyxel.circ(x, y + 3, 3, 1)

        c = 7 if self.state == "captured" else self.base_color
        pyxel.rect(x - 3, y - 3, 6, 6, c)
        pyxel.rect(x - 2, y - 2, 4, 4, c + 1)
        pyxel.pset(x + random.randint(-2, 2), y + random.randint(-2, 2), 8)

        pyxel.circ(x, y - 5, 2, c)
        pyxel.pset(x + self.dir, y - 5, 8)
        if pyxel.frame_count % 30 < 15:
            pyxel.pset(x - self.dir, y - 5, 8)


class Fade:
    def __init__(self):
        self.alpha = 0.0
        self.target = 0.0
        self.speed = 0.06
        self.active = False

    def to(self, target, speed=None):
        self.target = clamp(target, 0.0, 1.0)
        if speed is not None: self.speed = speed
        self.active = True

    def update(self):
        if not self.active: return
        if self.alpha < self.target:
            self.alpha = clamp(self.alpha + self.speed, 0.0, 1.0)
        elif self.alpha > self.target:
            self.alpha = clamp(self.alpha - self.speed, 0.0, 1.0)
        if abs(self.alpha - self.target) < 0.01:
            self.alpha = self.target
            self.active = False

    def draw(self):
        if self.alpha <= 0.01: return
        layers = int(self.alpha * 8) + 1
        for _ in range(layers):
            pyxel.rect(0, 0, WINDOW_W, WINDOW_H, 0)


class Shake:
    def __init__(self):
        self.timer = 0
        self.intensity = 0

    def start(self, frames=12, intensity=2):
        self.timer = frames
        self.intensity = intensity

    def update(self):
        if self.timer > 0: self.timer -= 1

    def get_offset(self):
        if self.timer <= 0: return 0, 0
        return (random.randint(-self.intensity, self.intensity),
                random.randint(-self.intensity, self.intensity))


class GameApp:
    def __init__(self):
        pyxel.init(WINDOW_W, WINDOW_H, title="DEMOCRACY OF THE DEAD")
        pyxel.mouse(False)
        
        try:
            pyxel.images[0].load(0, 0, "dodtitle.png")
        except Exception:
            pass
        try:
            pyxel.images[1].load(0, 0, "tarotbak1.png")
        except Exception:
            pass

        self.card_movies = [
            "rea1gumono",
            "rea2seigi",
            "rea3kenjya"
        ]
       
        self.card_clicked = False
        self.video_timer = 0  # 再生時間をカウントするタイマー
        self.video_process = None  # ★ 再生中の外部プレイヤーのプロセスを記憶する変数
        
        # --- SOUND DATA SETUP ---
        pyxel.sounds[0].set("c2e2g2c3 d3c3e2g2 c2d2e2g2 f2e2d2c2", "t", "5", "n", 30)
        pyxel.sounds[1].set("a2c3d3e3 f3e3d3c3 a2c3d3e3 c3r", "t", "5", "n", 30)
        pyxel.sounds[2].set("c1r r r g0r r r a0r r r f0r r r", "t", "7", "n", 30)
        pyxel.sounds[3].set("f0r r r r r r r", "n", "7", "n", 30)
        pyxel.sounds[4].set("", "p", "7", "n", 30)
        pyxel.sounds[5].set("a1g1f1e1 d1c1b0a0 a1g1f1e1 d1c1g0c1", "p", "6", "n", 45)
        pyxel.sounds[6].set("c2c2d2e2 e2d2c2d2 c2c2c2g1 g1g1g1r", "t", "6", "n", 30)
        pyxel.sounds[7].set("c3r", "p", "7", "n", 6)
        pyxel.sounds[8].set("c4g4", "t", "6", "s", 10)
        pyxel.sounds[9].set("c3e3g3c4", "s", "7", "n", 15)
        pyxel.sounds[10].set("c0c0c0", "n", "7", "f", 12)
        pyxel.sounds[11].set("c3", "p", "7", "n", 4)
        pyxel.sounds[12].set("c3r", "n", "7", "s", 8)
        pyxel.sounds[13].set("c1r r r g0r r r", "t", "3", "n", 45)

        pyxel.musics[0].set([0, 1], [2], [3])
        pyxel.musics[1].set([5], [13], [])
        pyxel.musics[2].set([6], [], [])

        self.fade = Fade()
        self.shake = Shake()

        self.state = "TITLE"
        self.stage = -1
        self.stage_start_frame = 0
        self.stage_time_limit = 0.0
        self.time_remaining_next_stage = BASE_TIME_LIMIT
        self.last_stage_remaining_time = 0.0
        self.start_time_total = 0.0
        self.zombie_speed_multiplier = 1.0

        self.player = None
        self.players = []
        self.zombies = []
        self.obstacles = []
        self.dummy_players = []
        self.captured_zombies = []

        self.marching = False
        self.fade_outting = False
        self.next_state_called = False

        self.time_up_zombified = False
        self.time_up_frame = 0
        self.time_up_warning_played = False

        self.total_clear_time = 0.0
        self.ending_timer = 0
        self.credits_y = WINDOW_H
        self.credits_duration = sum(height for height, _, _ in CREDITS_CONTENT)

        self.show_final_score = False

        self.play_music_safe("TITLE")
        try:
            import js
            js.pyxel_app = self
        except:
            pass
        pyxel.run(self.update, self.draw)
        
    def movie_finished(self):
        self.return_to_title_fallback()
   
    
    def start_march(self):
        self.marching = True
        for p in self.players:
            p.walk_frame = 0

    def update_march(self):
        if not self.marching: return
        tx = WINDOW_W - SANCTUARY_W + 2
        march_speed = PLAYER_SPEED * 1.5
        for e in [self.player] + self.captured_zombies:
            if e.x < tx:
                e.x += min(march_speed, tx - e.x)
                if isinstance(e, Player):
                    e.walk_frame = (e.walk_frame + 1) % 16
                e.dir = 1
            if isinstance(e, Player) and e.is_main:
                e.trail = [(e.x, e.y)] * TRAIL_MAX_LENGTH

    def play_music_safe(self, mode):
        pyxel.stop()
        if mode == "TITLE": pyxel.playm(2, loop=True)
        elif mode == "PLAYING": pyxel.playm(0, loop=True)
        elif mode == "ENDING_CREDITS": pyxel.playm(1, loop=True)

    def spawn_stage(self):
        self.stage += 1
        if self.stage > MAX_STAGE_PLAY + 1:
            self.stage = 1

        if self.stage == 0:
            self.stage = 1
            self.stage_time_limit = self.time_remaining_next_stage
        elif self.stage <= MAX_STAGE_PLAY:
            self.stage_time_limit = self.time_remaining_next_stage
        elif self.stage == MAX_STAGE_PLAY + 1:
            self.stage_time_limit = max(FINAL_STAGE_TIME_LIMIT_MIN, self.time_remaining_next_stage)

        self.time_up_zombified = False
        self.time_up_frame = 0
        self.time_up_warning_played = False

        self.obstacles = []
        spawn_x, spawn_y = WINDOW_W // 4, WINDOW_H // 2
        self.players = []
        self.player = Player(spawn_x, spawn_y, is_main=True)
        self.players.append(self.player)

        if self.stage == MAX_STAGE_PLAY + 1:
            sanctuary_pos_x = WINDOW_W - SANCTUARY_W + 8
            self.dummy_players = [
                Player(sanctuary_pos_x, WINDOW_H // 2 - 20, is_main=False, color_override=11),
                Player(sanctuary_pos_x + 5, WINDOW_H // 2, is_main=False, color_override=7),
                Player(sanctuary_pos_x, WINDOW_H // 2 + 20, is_main=False, color_override=8)
            ]
            self.players.extend(self.dummy_players)
            zombie_count = FINAL_STAGE_ZOMBIES
        else:
            self.dummy_players = []
            zombie_count = ZOMBIE_COUNT_BASE + (self.stage - 1) * 2

        self.zombies = []
        self.captured_zombies = []

        for _ in range(zombie_count):
            zx = random.randint(0, WINDOW_W - SANCTUARY_W - 6)
            zy = random.randint(UI_HEIGHT, WINDOW_H - 1)
            sf = random.choice([0.8, 1.0, 1.3])
            self.zombies.append(Zombie(zx, zy, speed_factor=sf, global_speed_multiplier=self.zombie_speed_multiplier))

        if self.start_time_total == 0.0:
            self.start_time_total = pyxel.frame_count / 60.0

        self.stage_start_frame = pyxel.frame_count
        self.state = "PLAYING"
        self.marching = False
        self.fade.to(0.0, speed=0.08)
        self.play_music_safe("PLAYING")

    def start_ending(self):
        self.total_clear_time = (pyxel.frame_count / 60.0) - self.start_time_total
        self.last_stage_remaining_time = self.time_remaining_next_stage
        self.time_remaining_next_stage += BONUS_TIME_AFTER_CLEAR
        self.state = "ENDING"
        self.ending_timer = 0
        self.fade.to(1.0, speed=0.01)
        self.show_final_score = False

    def return_to_title_fallback(self):
        self.stage = -1
        self.time_remaining_next_stage = BASE_TIME_LIMIT
        self.start_time_total = 0.0
        self.sentakutap_played = False
        self.card_clicked = False
        self.video_timer = 0
        self.state = "TITLE"
        self.fade.alpha = 0
        self.fade.target = 0
        self.play_music_safe("TITLE")

    def update(self):
        self.fade.update()
        self.shake.update()

        if self.state == "SENTAKUTAP":

            if self.video_timer == 0:

                self.selected_movie = random.choices(
                    ["rea1gumono", "rea2seigi", "rea3kenjya"],
                    weights=[80, 15, 5]
                )[0]

                try:
                    import js
                    js.showEndingMovie(self.selected_movie)

                except Exception as e:
                    print(e)
                    self.return_to_title_fallback()

                self.video_timer = 1

            self.video_timer += 1

            if self.video_timer > 900:
                self.return_to_title_fallback()

            return

        # 通常のゲームオブジェクト更新
        for p in self.players:
            can_control = self.state == "PLAYING" and not self.time_up_zombified
            p.update(self.obstacles, controllable=can_control)

        for z in self.zombies:
            z.update(self.player, self.obstacles, self.captured_zombies)

        is_enter_pressed = pyxel.btnp(pyxel.KEY_RETURN) or \
                           pyxel.btnp(GAMEPAD_A_ID) or \
                           pyxel.btnp(GAMEPAD_START_ID)

        if self.state == "TITLE":
            if is_enter_pressed:
                pyxel.play(3, 11)
                self.fade.to(1.0, speed=0.06)
                self.next_state_called = True

            if self.next_state_called and not self.fade.active and self.fade.alpha >= 0.99:
                self.next_state_called = False
                self.state = "TUTORIAL"
                self.fade.to(0.0, speed=0.06)

        elif self.state == "TUTORIAL":
            if is_enter_pressed:
                pyxel.play(3, 11)
                self.fade.to(1.0, speed=0.06)
                self.next_state_called = True

            if self.next_state_called and not self.fade.active and self.fade.alpha >= 0.99:
                self.next_state_called = False
                self.stage = 0
                self.time_remaining_next_stage = BASE_TIME_LIMIT
                self.start_time_total = 0.0
                self.spawn_stage()

        elif self.state == "PLAYING":
            newly_captured = [z for z in self.zombies if z.state == "captured" and z not in self.captured_zombies]
            for z in newly_captured:
                self.captured_zombies.append(z)
                self.shake.start(frames=4, intensity=1)

            elapsed = (pyxel.frame_count - self.stage_start_frame) / 60.0
            time_left = max(0.0, self.stage_time_limit - elapsed)

            if time_left < 10.0 and not self.time_up_warning_played and time_left > 0:
                pyxel.play(3, 7, loop=True)
                self.time_up_warning_played = True

            if time_left <= 0.0 and not self.time_up_zombified:
                self.time_up_zombified = True
                self.player.is_zombified = True
                self.time_up_frame = pyxel.frame_count
                pyxel.stop()
                pyxel.play(3, 10)
                self.play_music_safe("STOP")

            if self.time_up_zombified:
                if pyxel.frame_count - self.time_up_frame > GAMEOVER_HOLD_TIME:
                    self.fade.to(1.0, speed=0.06)
                    self.next_state_called = True

            if self.next_state_called and self.fade.alpha >= 0.99:
                self.next_state_called = False
                self.return_to_title_fallback()

            if len(self.captured_zombies) == len(self.zombies) and len(self.zombies) > 0:
                self.time_remaining_next_stage = time_left
                self.state = "GO_TO_SANCT"
                self.start_march()
                self.play_music_safe("STOP")
                pyxel.play(3, 9)

        elif self.state == "GO_TO_SANCT":
            self.update_march()
            sanctuary_x_min = WINDOW_W - SANCTUARY_W
            all_in_sanctuary = all(p.x >= sanctuary_x_min for p in self.players if p.is_main) and \
                               all(z.x >= sanctuary_x_min for z in self.captured_zombies)

            if all_in_sanctuary and not self.fade_outting:
                self.marching = False
                self.fade.to(1.0, speed=0.01)
                self.fade_outting = True

            if self.fade_outting and not self.fade.active and self.fade.alpha >= 0.99:
                self.fade_outting = False
                if self.stage == MAX_STAGE_PLAY + 1:
                    self.start_ending()
                else:
                    self.spawn_stage()

        elif self.state == "ENDING":
            if self.ending_timer == 0:
                self.fade.to(0.0, speed=0.08)
                self.play_music_safe("ENDING_CREDITS")

            self.ending_timer += 1
            for p in self.dummy_players:
                p.update(self.obstacles, controllable=False)

            if self.ending_timer < TRANSFORM_DURATION:
                if self.ending_timer % 30 == 0: pyxel.play(3, 12)
                if self.ending_timer % 5 < 3: self.shake.start(frames=3, intensity=3)

                is_flashing = (self.ending_timer % 4 < 2)
                for p in self.dummy_players:
                    p.temp_color = random.choice([8, 13, 3]) if is_flashing else p.color

                if self.ending_timer % 10 == 0:
                    for p in self.dummy_players:
                        if random.random() < 0.8: p.spawn_transform_particle(random.choice([8, 3]))

            if self.ending_timer == TRANSFORM_DURATION:
                self.shake.start(frames=20, intensity=5)
                pyxel.play(3, 10)
                for p in self.dummy_players:
                    p.is_zombified = True
                    p.temp_color = None
                    for _ in range(20): p.spawn_transform_particle(random.choice([8, 3, 1]))

            if self.ending_timer > TRANSFORM_DURATION + 90:
                self.state = "CREDITS_ROLL"
                self.credits_y = WINDOW_H
                self.fade.to(0.0, speed=0.015)

        elif self.state == "CREDITS_ROLL":
            self.credits_y -= CREDITS_SPEED
            if self.credits_y < -(self.credits_duration) + 10:
                self.show_final_score = True

            if self.credits_y < -(self.credits_duration) - 90:
                self.fade.to(1.0, speed=0.015)

            if self.fade.alpha >= 0.99:
                pyxel.stop()
                self.sentakutap_played = False
                self.card_clicked = False
                self.video_timer = 0
                self.state = "SENTAKUTAP"

    def draw(self):
        ox, oy = self.shake.get_offset()
        pyxel.cls(1) 
        if self.state == "SENTAKUTAP":
             pyxel.cls(0)
             pyxel.text(center_text_x("PLAYING MOVIE..."), 55, "PLAYING MOVIE...", 8)
             self.fade.draw()
             return
        if self.state == "TITLE":
            self.draw_title()
        elif self.state == "TUTORIAL":
            self.draw_tutorial()
        elif self.state in ("PLAYING", "GO_TO_SANCT"):
            pyxel.clip(0, UI_HEIGHT, WINDOW_W, WINDOW_H - UI_HEIGHT)
            pyxel.camera(ox, oy)
            self.draw_playing()
            pyxel.camera(0, 0)
            pyxel.clip()
            self.draw_ui()

            if self.time_up_zombified:
                s1 = "TIME UP!"
                s2 = "GAME OVER"
                pyxel.text(center_text_x(s1), WINDOW_H // 2 - 8, s1, 8)
                pyxel.text(center_text_x(s2), WINDOW_H // 2 + 8, s2, 7)

        elif self.state == "ENDING":
            pyxel.camera(0, 0)
            self.draw_ending_scene()
        elif self.state == "CREDITS_ROLL":
            pyxel.cls(0)
            pyxel.camera(0, 0)
            self.draw_credits_roll()

        self.fade.draw()

    def draw_title(self):
        pyxel.cls(0)
        img_w, img_h = 75, 100
        img_x = (WINDOW_W - img_w) // 2
        img_y = (WINDOW_H - img_h) // 2 - 4
        try:
            pyxel.blt(img_x, img_y, 0, 0, 0, img_w, img_h)
        except Exception:
            pyxel.text(center_text_x("DEMOCRACY OF THE DEAD"), WINDOW_H // 2 - 10, "DEMOCRACY OF THE DEAD", 8)

        bt = "- PRESS ENTER / GAMEPAD A/START -"
        if pyxel.frame_count % 30 < 15:
            pyxel.text(center_text_x(bt), WINDOW_H - 24, bt, 7)

        c1 = "(C) Y.K/MIRAI WORK"
        c2 = "Game Assembly by (C) M.T"
        pyxel.text(center_text_x(c1), WINDOW_H - 16, c1, 13)
        pyxel.text(center_text_x(c2), WINDOW_H - 10, c2, 13)

    def draw_tutorial(self):
        pyxel.cls(0)
        t_title = "TUTORIAL"
        pyxel.text(center_text_x(t_title), 10, t_title, 8)
        pyxel.line(40, 18, 120, 18, 7)

        instructions = [
            ("1. MOVE:", "ARROW KEYS / DIRECTIONAL PAD"),
            ("2. CAPTURE:", "TOUCH ZOMBIES TO JOIN THEM"),
            ("3. GOAL:", "BRING ALL TO THE RIGHT SIDE"),
        ]
        for i, (head, body) in enumerate(instructions):
            y = 30 + i * 25
            pyxel.text(20, y, head, 11)
            pyxel.text(20, y + 8, body, 7)

        begin_text = "- PRESS ENTER / GAMEPAD A/START TO BEGIN -"
        if pyxel.frame_count % 30 < 15:
            pyxel.text(center_text_x(begin_text), WINDOW_H - 15, begin_text, 13)

    def draw_playing(self):
        sanctuary_x = WINDOW_W - SANCTUARY_W
        for y in range(UI_HEIGHT + 10, WINDOW_H, 12):
            pyxel.line(0, y, WINDOW_W - SANCTUARY_W, y, 9)

        pyxel.rect(sanctuary_x, 0, SANCTUARY_W, WINDOW_H, 10)
        pyxel.rectb(sanctuary_x, 0, SANCTUARY_W, WINDOW_H, 12)

        entities = list(self.players) + list(self.zombies)
        entities.sort(key=lambda e: e.y)
        for e in entities:
            e.draw()

        if self.state == "GO_TO_SANCT":
            s = "GO TO SANCTUARY!"
            pyxel.text(center_text_x(s), WINDOW_H - 14, s, 2)

    def draw_ui(self):
        pyxel.rect(0, 0, WINDOW_W, UI_HEIGHT, 0)
        stage_text = f"Stage: {self.stage}/{MAX_STAGE_PLAY}"
        if self.stage == MAX_STAGE_PLAY + 1:
            stage_text = "Stage: FINAL"

        pyxel.text(4, 4, stage_text, 7)
        captured_count = len(self.captured_zombies)
        pyxel.text(4, 12, f"Captured: {captured_count}/{len(self.zombies)}", 7)

        elapsed = (pyxel.frame_count - self.stage_start_frame) / 60.0
        time_left = max(0.0, self.stage_time_limit - elapsed)
        time_text = f"Time: {time_left:.1f}s"
        t_x = WINDOW_W - len(time_text) * 4 - 4
        color = 8 if time_left < 10 or self.time_up_zombified else 7
        pyxel.text(t_x, 8, time_text, color)

    def draw_ending_scene(self):
        ox, oy = self.shake.get_offset()
        pyxel.cls(0)
        pyxel.rect(WINDOW_W - SANCTUARY_W + ox, 0 + oy, SANCTUARY_W, WINDOW_H, 10)

        if self.ending_timer < TRANSFORM_DURATION and self.ending_timer % 3 == 0:
            pyxel.rect(WINDOW_W - SANCTUARY_W + ox, 0 + oy, SANCTUARY_W, WINDOW_H, random.choice([8, 0, 3]))

        for p in self.players:
            pyxel.camera(ox, oy)
            p.draw()
        pyxel.camera(0, 0)

        if self.ending_timer < TRANSFORM_DURATION:
            s = "THE SANCTUARY IS COMPROMISING..."
            pyxel.text(center_text_x(s) + ox, 10 + oy, s, 8)
            s2 = "IT HURTS... IT HURTS..."
            pyxel.text(center_text_x(s2) + ox, 20 + oy, s2, 7)
        else:
            s = "THE SANCTUARY WAS COMPROMISED."
            pyxel.text(center_text_x(s) + ox, 10 + oy, s, 8)
            clear1 = "CLEAR!"
            clear2 = "CONGRATULATIONS!!"

            # 光る色
            clear_color1 = 10 if pyxel.frame_count % 20 < 10 else 7
            clear_color2 = 7 if pyxel.frame_count % 20 < 10 else 10

            # CLEAR!
            cx1 = center_text_x(clear1)
            cy1 = WINDOW_H // 2 - 8

            pyxel.text(cx1 - 1, cy1, clear1, 0)
            pyxel.text(cx1 + 1, cy1, clear1, 0)
            pyxel.text(cx1, cy1 - 1, clear1, 0)
            pyxel.text(cx1, cy1 + 1, clear1, 0)
            pyxel.text(cx1, cy1, clear1, clear_color1)

            # CONGRATULATIONS!!
            cx2 = center_text_x(clear2)
            cy2 = WINDOW_H // 2 + 8

            pyxel.text(cx2 - 1, cy2, clear2, 0)
            pyxel.text(cx2 + 1, cy2, clear2, 0)
            pyxel.text(cx2, cy2 - 1, clear2, 0)
            pyxel.text(cx2, cy2 + 1, clear2, 0)
            pyxel.text(cx2, cy2, clear2, clear_color2)

    def draw_credits_roll(self):
        curr_y = self.credits_y

        for height, text, color in CREDITS_CONTENT:
            if curr_y > -height and curr_y < WINDOW_H:
                pyxel.text(center_text_x(text), int(curr_y), text, color)
            curr_y += height

        if self.show_final_score:
            pyxel.blt(0, 0, 1, 0, 0, WINDOW_W, WINDOW_H)
            # 点滅色
            blink1 = 10 if pyxel.frame_count % 30 < 15 else 8
            blink2 = 7 if pyxel.frame_count % 30 < 15 else 13

            bonus = "BONUS!"
            tarot = "TAROT CARD APPEARS!!"

            # BONUS!
            bx = center_text_x(bonus)
            by = WINDOW_H // 2 - 20

            pyxel.text(bx - 1, by, bonus, 0)
            pyxel.text(bx + 1, by, bonus, 0)
            pyxel.text(bx, by - 1, bonus, 0)
            pyxel.text(bx, by + 1, bonus, 0)
            pyxel.text(bx, by, bonus, blink1)
            # キラキラ
            for _ in range(8):
                px = bx + random.randint(-30, 30)
                py = by + random.randint(-10, 10)
                pyxel.pset(px, py, random.choice([7, 10, 13]))

            # TAROT CARD APPEARS!!
            tx = center_text_x(tarot)
            ty = WINDOW_H // 2 - 8

            pyxel.text(tx - 1, ty, tarot, 0)
            pyxel.text(tx + 1, ty, tarot, 0)
            pyxel.text(tx, ty - 1, tarot, 0)
            pyxel.text(tx, ty + 1, tarot, 0)
            pyxel.text(tx, ty, tarot, blink2)

            # プレイ時間
            s_time = f"TOTAL TIME: {self.total_clear_time:.2f}s"

            pyxel.text(
                center_text_x(s_time),
                WINDOW_H // 2 + 20,
                s_time,
                10
            )

app = GameApp()

try:
    import js
    js.window.pyxel_app = app
except Exception as e:
    print(e)
