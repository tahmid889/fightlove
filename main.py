import os
import random
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.animation import Animation
from kivy.core.audio import SoundLoader
from kivy.metrics import dp

BASE = os.path.dirname(os.path.abspath(__file__))

# ---------------- LEVELS ----------------
# hp = Tahmid er jibon, speed = tar gati, dmg = Habiba ke kotota lage, cd = attack er gap (second)
LEVELS = [
    dict(name="Level 1 - Jatrabari Road", hp=60, speed=70, dmg=6, cd=1.6,
         sky=(0.55, 0.80, 0.95), building=(0.55, 0.55, 0.60)),
    dict(name="Level 2 - Gulistan Evening", hp=100, speed=110, dmg=8, cd=1.2,
         sky=(0.95, 0.60, 0.35), building=(0.40, 0.30, 0.35)),
    dict(name="Level 3 - Midnight Dhaka", hp=150, speed=150, dmg=10, cd=0.9,
         sky=(0.08, 0.08, 0.20), building=(0.18, 0.18, 0.28)),
]


def load_sound(name):
    """sounds/ folder e file thakle load hobe, na thakle kono error hobe na."""
    path = os.path.join(BASE, "sounds", name)
    if os.path.exists(path):
        return SoundLoader.load(path)
    return None


class Fighter:
    def __init__(self, x, color, facing, max_hp):
        self.x = x
        self.color = color
        self.facing = facing      # 1 = dan dike, -1 = bam dike
        self.max_hp = max_hp
        self.hp = max_hp
        self.flash = 0.0          # hit korle sada hoye jabe
        self.attack_t = 0.0       # punch animation timer
        self.cooldown = 0.0
        self.rick_cd = 0.0        # rickshaw dhakka er gap


class Game(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.level = 0
        self.state = "menu"       # menu / play / win / lose / end
        self.offset = 0.0
        self.touches = {}
        self.dir = 0

        # Sound (optional) - sounds/ folder e ei nam e file dile bajbe
        self.s_punch = load_sound("punch.wav")
        self.s_hit = load_sound("hit.wav")
        self.s_win = load_sound("win.wav")
        self.s_lose = load_sound("lose.wav")
        self.music = load_sound("music.mp3")
        if self.music:
            self.music.loop = True
            self.music.play()

        self.msg = Label(text="", font_size=dp(26), halign="center",
                         color=(1, 1, 1, 1), size_hint=(None, None))
        self.title = Label(text="", font_size=dp(18), size_hint=(None, None),
                           color=(1, 1, 1, 1))
        self.name_h = Label(text="Habiba", font_size=dp(14), size_hint=(None, None),
                            color=(1, 1, 1, 1))
        self.name_t = Label(text="Tahmid", font_size=dp(14), size_hint=(None, None),
                            color=(1, 0.8, 0.8, 1))
        for w in (self.msg, self.title, self.name_h, self.name_t):
            self.add_widget(w)

        self.bind(size=self.on_resize)
        self.show_message("DHAKA FIGHT\nHabiba vs Tahmid\n\nTap to start")
        Clock.schedule_interval(self.update, 1 / 60.0)

    # ---------- helpers ----------
    def play(self, snd):
        if snd:
            snd.stop()
            snd.play()

    def on_resize(self, *a):
        self.ground = self.height * 0.25
        self.msg.size = (self.width, dp(150))
        self.msg.text_size = (self.width, None)
        self.msg.pos = (0, self.height * 0.5)

    def show_message(self, text):
        self.msg.text = text
        self.msg.opacity = 0
        Animation(opacity=1, duration=0.4).start(self.msg)   # fade in animation

    def hide_message(self):
        Animation(opacity=0, duration=0.3).start(self.msg)

    def start_level(self):
        L = LEVELS[self.level]
        self.ground = self.height * 0.25
        self.habiba = Fighter(self.width * 0.2, (0.9, 0.2, 0.6), 1, 100)
        self.tahmid = Fighter(self.width * 0.8, (0.2, 0.2, 0.2), -1, L["hp"])
        self.title.text = L["name"]
        self.title.size = (self.width, dp(30))
        self.title.pos = (0, self.height - dp(40))
        self.special_cd = 0.0
        self.rick_x = None
        self.rick_dir = 1
        self.rick_timer = 6.0
        self.state = "play"
        self.hide_message()

    # ---------- touch controls ----------
    def zone(self, x, y):
        if y > self.height * 0.3:
            return None
        if x < self.width * 0.2:
            return "left"
        if x < self.width * 0.4:
            return "right"
        if x > self.width * 0.8:
            return "special"
        if x > self.width * 0.6:
            return "attack"
        return None

    def on_touch_down(self, touch):
        if self.state in ("menu", "win", "lose", "end"):
            if self.state == "menu" or self.state == "lose":
                self.start_level()
            elif self.state == "win":
                self.level += 1
                self.start_level()
            elif self.state == "end":
                self.level = 0
                self.start_level()
            return True
        z = self.zone(touch.x, touch.y)
        if z:
            self.touches[touch.uid] = z
            if z == "attack":
                self.do_punch()
            elif z == "special":
                self.do_special()
        return True

    def on_touch_up(self, touch):
        self.touches.pop(touch.uid, None)
        return True

    # ---------- combat ----------
    def do_punch(self):
        h, t = self.habiba, self.tahmid
        if h.cooldown > 0:
            return
        h.cooldown = 0.35
        h.attack_t = 0.2
        self.play(self.s_punch)
        if abs(h.x - t.x) < dp(80):
            t.hp -= 10
            t.flash = 0.15
            t.x += h.facing * dp(25)      # dhakka khabe
            self.play(self.s_hit)

    def do_special(self):
        """Habiba er power kick: beshi range, beshi damage, 3 second cooldown."""
        h, t = self.habiba, self.tahmid
        if self.special_cd > 0:
            return
        self.special_cd = 3.0
        h.attack_t = 0.35
        self.play(self.s_punch)
        if abs(h.x - t.x) < dp(130):
            t.hp -= 25
            t.flash = 0.25
            t.x += h.facing * dp(70)
            self.play(self.s_hit)

    def update_rickshaw(self, dt):
        """Rickshaw rasta diye jay, dujon ke i dhakka dite pare (5 damage)."""
        self.rick_timer -= dt
        if self.rick_x is None and self.rick_timer <= 0:
            self.rick_dir = random.choice([1, -1])
            self.rick_x = -dp(80) if self.rick_dir == 1 else self.width + dp(80)
        if self.rick_x is not None:
            self.rick_x += self.rick_dir * dp(260) * dt
            for f in (self.habiba, self.tahmid):
                f.rick_cd = max(0, f.rick_cd - dt)
                if abs(f.x - self.rick_x) < dp(45) and f.rick_cd <= 0:
                    f.hp -= 5
                    f.flash = 0.2
                    f.rick_cd = 1.0
                    self.play(self.s_hit)
            if self.rick_x < -dp(120) or self.rick_x > self.width + dp(120):
                self.rick_x = None
                self.rick_timer = random.uniform(5, 9)

    def tahmid_ai(self, dt, L):
        h, t = self.habiba, self.tahmid
        dist = h.x - t.x
        t.facing = 1 if dist > 0 else -1
        if abs(dist) > dp(70):
            t.x += t.facing * dp(L["speed"]) * dt
        elif t.cooldown <= 0:
            t.cooldown = L["cd"]
            t.attack_t = 0.2
            h.hp -= L["dmg"]
            h.flash = 0.15
            h.x += t.facing * dp(25)
            self.play(self.s_hit)

    # ---------- main loop ----------
    def update(self, dt):
        self.offset += dp(120) * dt
        if self.state == "play":
            L = LEVELS[self.level]
            h, t = self.habiba, self.tahmid
            self.dir = 0
            for z in self.touches.values():
                if z == "left":
                    self.dir = -1
                elif z == "right":
                    self.dir = 1
            h.x += self.dir * dp(220) * dt
            if self.dir:
                h.facing = self.dir
            h.x = max(dp(30), min(self.width - dp(30), h.x))
            t.x = max(dp(30), min(self.width - dp(30), t.x))

            for f in (h, t):
                f.flash = max(0, f.flash - dt)
                f.attack_t = max(0, f.attack_t - dt)
                f.cooldown = max(0, f.cooldown - dt)

            self.special_cd = max(0, self.special_cd - dt)
            self.tahmid_ai(dt, L)
            self.update_rickshaw(dt)

            if t.hp <= 0:
                self.play(self.s_win)
                if self.level >= len(LEVELS) - 1:
                    self.state = "end"
                    self.show_message("YOU WIN!\nHabiba sob level jitlo!\n\nTap to play again")
                else:
                    self.state = "win"
                    self.show_message("Level complete!\n\nTap for next level")
            elif h.hp <= 0:
                self.play(self.s_lose)
                self.state = "lose"
                self.show_message("Habiba here gelo...\n\nTap to retry")
        self.draw()

    # ---------- drawing ----------
    def draw_fighter(self, f):
        y = self.ground
        w, h = dp(40), dp(90)
        self.canvas.add(Color(1, 1, 1) if f.flash > 0 else Color(*f.color))
        self.canvas.add(Rectangle(pos=(f.x - w / 2, y), size=(w, h * 0.65)))
        self.canvas.add(Ellipse(pos=(f.x - w * 0.4, y + h * 0.65), size=(w * 0.8, w * 0.8)))
        if f.attack_t > 0:   # punch er haat
            ax = f.x + w / 2 if f.facing > 0 else f.x - w / 2 - dp(35)
            self.canvas.add(Color(1, 0.85, 0.7))
            self.canvas.add(Rectangle(pos=(ax, y + h * 0.4), size=(dp(35), dp(12))))

    def draw_bar(self, x, y, frac, color):
        w, h = dp(120), dp(12)
        self.canvas.add(Color(0.2, 0.2, 0.2))
        self.canvas.add(Rectangle(pos=(x, y), size=(w, h)))
        self.canvas.add(Color(*color))
        self.canvas.add(Rectangle(pos=(x, y), size=(w * max(0, frac), h)))

    def draw(self):
        self.canvas.clear()
        L = LEVELS[min(self.level, len(LEVELS) - 1)]
        W, H = self.width, self.height
        ground = H * 0.25

        # akash
        self.canvas.add(Color(*L["sky"]))
        self.canvas.add(Rectangle(pos=(0, 0), size=(W, H)))

        # dhakar building (dhire dhire scroll kore)
        heights = [0.30, 0.45, 0.35, 0.55]
        bw = dp(80)
        period = bw * len(heights)
        shift = (self.offset * 0.3) % period
        self.canvas.add(Color(*L["building"]))
        for i in range(int(W / bw) + len(heights) + 2):
            bx = i * bw - shift
            self.canvas.add(Rectangle(pos=(bx, ground),
                                      size=(bw - dp(6), H * heights[i % len(heights)])))

        # rasta
        self.canvas.add(Color(0.25, 0.25, 0.27))
        self.canvas.add(Rectangle(pos=(0, 0), size=(W, ground)))
        # rastar sada dag (animation)
        dash, gap = dp(50), dp(40)
        sh = self.offset % (dash + gap)
        self.canvas.add(Color(1, 1, 1))
        x = -sh
        while x < W:
            self.canvas.add(Rectangle(pos=(x, ground * 0.45), size=(dash, dp(6))))
            x += dash + gap

        if self.state in ("play", "win", "lose", "end") and hasattr(self, "habiba"):
            if self.rick_x is not None:
                ry = ground * 0.12
                self.canvas.add(Color(0.95, 0.75, 0.1))
                self.canvas.add(Rectangle(pos=(self.rick_x - dp(35), ry + dp(14)),
                                          size=(dp(70), dp(30))))
                self.canvas.add(Color(0.8, 0.1, 0.1))
                self.canvas.add(Rectangle(pos=(self.rick_x - dp(35), ry + dp(44)),
                                          size=(dp(70), dp(10))))
                self.canvas.add(Color(0.05, 0.05, 0.05))
                self.canvas.add(Ellipse(pos=(self.rick_x - dp(30), ry), size=(dp(22), dp(22))))
                self.canvas.add(Ellipse(pos=(self.rick_x + dp(8), ry), size=(dp(22), dp(22))))
            self.draw_fighter(self.habiba)
            self.draw_fighter(self.tahmid)
            self.draw_bar(dp(10), H - dp(70), self.habiba.hp / self.habiba.max_hp, (0.2, 0.9, 0.3))
            self.draw_bar(W - dp(130), H - dp(70), self.tahmid.hp / self.tahmid.max_hp, (0.9, 0.2, 0.2))
            self.name_h.pos = (self.habiba.x - dp(30), ground + dp(130))
            self.name_t.pos = (self.tahmid.x - dp(30), ground + dp(130))
            self.name_h.size = self.name_t.size = (dp(60), dp(20))

            # control button
            if self.state == "play":
                sp_alpha = 0.4 if self.special_cd <= 0 else 0.1
                for label_x, col in ((0, (1, 1, 1, 0.25)), (W * 0.2, (1, 1, 1, 0.25)),
                                     (W * 0.6, (1, 0.3, 0.3, 0.35)),
                                     (W * 0.8, (1, 0.8, 0.1, sp_alpha))):
                    self.canvas.add(Color(*col))
                    self.canvas.add(Rectangle(pos=(label_x + dp(5), dp(5)),
                                              size=(W * 0.2 - dp(10), H * 0.3 - dp(10))))
        else:
            self.name_h.pos = self.name_t.pos = (-500, -500)


def error_screen(text):
    """Crash hole app bondho na hoye error ta screen e dekhabe (phone e debug er jonno)."""
    from kivy.uix.scrollview import ScrollView
    lbl = Label(text="ERROR (screenshot niye pathao):\n\n" + text,
                font_size=dp(12), size_hint_y=None, halign="left", valign="top",
                color=(1, 0.4, 0.4, 1))
    lbl.bind(width=lambda w, v: setattr(w, "text_size", (v, None)))
    lbl.bind(texture_size=lambda w, v: setattr(w, "height", v[1]))
    sv = ScrollView()
    sv.add_widget(lbl)
    return sv


class DhakaFightApp(App):
    def build(self):
        try:
            Window.clearcolor = (0, 0, 0, 1)
            return Game()
        except Exception:
            import traceback
            return error_screen(traceback.format_exc())

    def on_pause(self):
        return True      # phone e home chaple app jate bondho na hoy

    def on_resume(self):
        pass


try:
    from kivy.base import ExceptionHandler, ExceptionManager

    class CrashShow(ExceptionHandler):
        shown = False

        def handle_exception(self, inst):
            import traceback
            if CrashShow.shown:          # ekbar i dekhabe, bar bar na
                return ExceptionManager.PASS
            CrashShow.shown = True
            try:
                for child in list(Window.children):
                    Window.remove_widget(child)
                Window.add_widget(error_screen(traceback.format_exc()))
            except Exception:
                pass
            return ExceptionManager.PASS

    ExceptionManager.add_handler(CrashShow())
except Exception:
    pass


if __name__ == "__main__":
    DhakaFightApp().run()
