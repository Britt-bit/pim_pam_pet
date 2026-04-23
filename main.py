"""
SpinAlert - Random Alert + Spin Wheel + Scoreboard App
Built with Kivy for Android
"""

from kivy.app import App
from kivy.properties import NumericProperty
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

import json
import os
import math
import random
import threading
import time
from datetime import datetime, timedelta, time as dt_time

# Try to import plyer for notifications (works on Android)
try:
    from plyer import notification
    HAS_NOTIFICATIONS = True
except Exception:
    HAS_NOTIFICATIONS = False

# ─── Data storage ────────────────────────────────────────────────────────────

DATA_FILE = "spinapp_data.json"

DEFAULT_DATA = {
    "alert_settings": {
        "start_hour": 7,
        "end_hour": 19,
        "count": 5,
        "enabled": False
    },
    "wheel_mode": "letters",   # "letters" or "colors"
    "scores": []               # [{"name": "Alice", "score": 0}, ...]
}

WHEEL_COLORS = [
    ("#E63946", "Red"),
    ("#F4A261", "Orange"),
    ("#2A9D8F", "Teal"),
    ("#E9C46A", "Yellow"),
    ("#264653", "Navy"),
    ("#A8DADC", "Sky"),
    ("#6D6875", "Mauve"),
    ("#B5E48C", "Lime"),
]

WHEEL_LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                # Merge missing keys
                for k, v in DEFAULT_DATA.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            pass
    return dict(DEFAULT_DATA)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ─── Colour palette ──────────────────────────────────────────────────────────

BG       = get_color_from_hex("#0D0D0D")
SURFACE  = get_color_from_hex("#1A1A2E")
ACCENT   = get_color_from_hex("#E94560")
ACCENT2  = get_color_from_hex("#F5A623")
TEXT     = get_color_from_hex("#F0F0F0")
SUBTEXT  = get_color_from_hex("#888888")
BTN_BG   = get_color_from_hex("#16213E")


def hex_to_kivy(h):
    return get_color_from_hex(h)


# ─── Custom widgets ──────────────────────────────────────────────────────────

class RoundButton(Button):
    def __init__(self, accent=False, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = ACCENT if accent else BTN_BG
        self.color = TEXT
        self.font_size = dp(14)
        self.bold = True
        self.size_hint_y = None
        self.height = dp(48)


class SectionLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = ACCENT
        self.font_size = dp(13)
        self.bold = True
        self.size_hint_y = None
        self.height = dp(28)
        self.halign = "left"
        self.valign = "middle"
        self.bind(size=lambda *a: setattr(self, 'text_size', self.size))


class ValueLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = TEXT
        self.font_size = dp(15)
        self.size_hint_y = None
        self.height = dp(36)
        self.halign = "left"
        self.valign = "middle"
        self.bind(size=lambda *a: setattr(self, 'text_size', self.size))


# ─── Spin Wheel canvas widget ────────────────────────────────────────────────

class WheelWidget(FloatLayout):
    """Draws the spinning wheel and handles the spin animation."""

    angle = NumericProperty(0)

    def __init__(self, mode="letters", **kwargs):
        super().__init__(**kwargs)
        self.mode = mode
        self.spinning = False
        self.result_label = None
        self.bind(angle=lambda *a: self._redraw())
        self._build()

    def _build(self):
        self.bind(size=self._redraw, pos=self._redraw)

    def _redraw(self, *args):
        self.canvas.clear()
        items = WHEEL_COLORS if self.mode == "colors" else WHEEL_LETTERS[:12]
        n = len(items)
        sweep = 360.0 / n
        cx, cy = self.center
        r = min(self.width, self.height) * 0.44

        with self.canvas:
            for i, item in enumerate(items):
                start_angle = i * sweep + self.angle
                if self.mode == "colors":
                    Color(*hex_to_kivy(item[0]))
                else:
                    palette = ["#E94560", "#F5A623", "#2A9D8F", "#A8DADC",
                               "#6D6875", "#B5E48C", "#264653", "#E9C46A",
                               "#F4A261", "#E63946", "#4361EE", "#4CC9F0"]
                    Color(*hex_to_kivy(palette[i % len(palette)]))

                Ellipse(
                    pos=(cx - r, cy - r),
                    size=(r * 2, r * 2),
                    angle_start=start_angle,
                    angle_end=start_angle + sweep
                )

            # Divider lines
            Color(0, 0, 0, 0.6)
            for i in range(n):
                angle_rad = math.radians(i * sweep + self.angle)
                Line(
                    points=[cx, cy,
                            cx + r * math.cos(angle_rad),
                            cy + r * math.sin(angle_rad)],
                    width=1.5
                )

            # Centre circle
            Color(*SURFACE)
            cr = r * 0.18
            Ellipse(pos=(cx - cr, cy - cr), size=(cr * 2, cr * 2))

            # Pointer triangle at the right (3 o'clock = 0°)
            Color(*ACCENT)
            px = cx + r + dp(6)
            py = cy
            ts = dp(12)
            Line(points=[px, py + ts, px - ts * 1.5, py, px, py - ts, px, py + ts], width=2)

        # Draw text labels
        for widget in list(self.children):
            if hasattr(widget, '_wheel_label'):
                self.remove_widget(widget)

        items_list = WHEEL_COLORS if self.mode == "colors" else WHEEL_LETTERS[:12]
        for i, item in enumerate(items_list):
            mid_angle = math.radians((i + 0.5) * sweep + self.angle)
            lx = cx + r * 0.65 * math.cos(mid_angle)
            ly = cy + r * 0.65 * math.sin(mid_angle)
            text = item[1] if self.mode == "colors" else item
            lbl = Label(
                text=text,
                font_size=dp(11) if self.mode == "colors" else dp(14),
                bold=True,
                color=(1, 1, 1, 1),
                size=(dp(50), dp(20)),
                pos=(lx - dp(25), ly - dp(10))
            )
            lbl._wheel_label = True
            self.add_widget(lbl)

    def spin(self, on_result=None):
        if self.spinning:
            return
        self.spinning = True
        extra = random.uniform(720, 1440)
        target = self.angle + extra
        anim = Animation(angle=target, duration=3.0, t="out_cubic")

        def _done(*a):
            self.spinning = False
            self.angle = self.angle % 360
            # Figure out which slice is at the pointer (0°)
            items = WHEEL_COLORS if self.mode == "colors" else WHEEL_LETTERS[:12]
            n = len(items)
            sweep = 360.0 / n
            # Pointer is at angle 0 (right side). Work out which slice it falls in.
            pointer_angle = (360 - self.angle % 360) % 360
            idx = int(pointer_angle / sweep) % n
            result = items[idx]
            if self.mode == "colors":
                result_text = result[1]
            else:
                result_text = result
            self._redraw()
            if on_result:
                on_result(result_text)

        anim.bind(on_complete=_done)
        anim.start(self)

    def set_mode(self, mode):
        self.mode = mode
        self._redraw()


# ─── Screens ─────────────────────────────────────────────────────────────────

class HomeScreen(Screen):
    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app = app_ref
        layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(16))

        with self.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(size=lambda *a: setattr(self._bg, 'size', self.size))
        self.bind(pos=lambda *a: setattr(self._bg, 'pos', self.pos))

        # Title
        title = Label(
            text="✦ SPIN ALERT",
            font_size=dp(32),
            bold=True,
            color=ACCENT,
            size_hint_y=None,
            height=dp(60)
        )
        layout.add_widget(title)

        sub = Label(
            text="Your daily randomness machine",
            font_size=dp(13),
            color=SUBTEXT,
            size_hint_y=None,
            height=dp(24)
        )
        layout.add_widget(sub)

        layout.add_widget(Label(size_hint_y=None, height=dp(20)))

        btn_alerts = RoundButton(text="🔔  Alert Scheduler", accent=False)
        btn_alerts.bind(on_release=lambda *a: self.go("alerts"))
        layout.add_widget(btn_alerts)

        btn_wheel = RoundButton(text="🎡  Spin the Wheel", accent=True)
        btn_wheel.bind(on_release=lambda *a: self.go("wheel"))
        layout.add_widget(btn_wheel)

        btn_score = RoundButton(text="🏆  Scoreboard", accent=False)
        btn_score.bind(on_release=lambda *a: self.go("scores"))
        layout.add_widget(btn_score)

        layout.add_widget(Label())  # spacer

        self.add_widget(layout)

    def go(self, screen):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = screen


class AlertScreen(Screen):
    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app = app_ref

        with self.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(size=lambda *a: setattr(self._bg, 'size', self.size))
        self.bind(pos=lambda *a: setattr(self._bg, 'pos', self.pos))

        outer = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(12))

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(44))
        back = RoundButton(text="← Back", size_hint_x=0.3)
        back.bind(on_release=lambda *a: self.go_back())
        hdr.add_widget(back)
        hdr.add_widget(Label(text="Alert Scheduler", font_size=dp(18), bold=True, color=TEXT))
        outer.add_widget(hdr)

        # Start hour
        outer.add_widget(SectionLabel(text="START HOUR"))
        self.start_val = ValueLabel(text=f"07:00")
        outer.add_widget(self.start_val)
        self.start_slider = Slider(min=0, max=23, value=7, step=1,
                                   size_hint_y=None, height=dp(40))
        self.start_slider.bind(value=self._update_start)
        outer.add_widget(self.start_slider)

        # End hour
        outer.add_widget(SectionLabel(text="END HOUR"))
        self.end_val = ValueLabel(text=f"19:00")
        outer.add_widget(self.end_val)
        self.end_slider = Slider(min=0, max=23, value=19, step=1,
                                 size_hint_y=None, height=dp(40))
        self.end_slider.bind(value=self._update_end)
        outer.add_widget(self.end_slider)

        # Count
        outer.add_widget(SectionLabel(text="NUMBER OF ALERTS"))
        self.count_val = ValueLabel(text="5 alerts")
        outer.add_widget(self.count_val)
        self.count_slider = Slider(min=1, max=20, value=5, step=1,
                                   size_hint_y=None, height=dp(40))
        self.count_slider.bind(value=self._update_count)
        outer.add_widget(self.count_slider)

        outer.add_widget(Label(size_hint_y=None, height=dp(8)))

        # Toggle
        self.toggle_btn = RoundButton(text="▶  Start Scheduling", accent=True)
        self.toggle_btn.bind(on_release=self._toggle)
        outer.add_widget(self.toggle_btn)

        self.status_label = Label(text="", color=SUBTEXT, font_size=dp(12),
                                  size_hint_y=None, height=dp(30))
        outer.add_widget(self.status_label)

        outer.add_widget(Label())
        self.add_widget(outer)

    def on_enter(self):
        s = self.app.data["alert_settings"]
        self.start_slider.value = s["start_hour"]
        self.end_slider.value = s["end_hour"]
        self.count_slider.value = s["count"]
        self._sync_time_labels()
        self._refresh_toggle()

    def _sync_time_labels(self):
        self.start_val.text = f"{int(self.start_slider.value):02d}:00"
        self.end_val.text = f"{int(self.end_slider.value):02d}:00"

    def _update_start(self, slider, val):
        sh = int(val)
        eh = int(self.end_slider.value)
        if sh >= eh:
            if sh < 23:
                eh = sh + 1
            else:
                sh, eh = 22, 23
                self.start_slider.value = float(sh)
            self.end_slider.value = float(eh)
        sh, eh = int(self.start_slider.value), int(self.end_slider.value)
        self._sync_time_labels()
        self.app.data["alert_settings"]["start_hour"] = sh
        self.app.data["alert_settings"]["end_hour"] = eh
        save_data(self.app.data)

    def _update_end(self, slider, val):
        eh = int(val)
        sh = int(self.start_slider.value)
        if eh <= sh:
            if eh > 0:
                sh = eh - 1
            else:
                sh, eh = 0, 1
                self.end_slider.value = float(eh)
            self.start_slider.value = float(sh)
        sh, eh = int(self.start_slider.value), int(self.end_slider.value)
        self._sync_time_labels()
        self.app.data["alert_settings"]["start_hour"] = sh
        self.app.data["alert_settings"]["end_hour"] = eh
        save_data(self.app.data)

    def _update_count(self, slider, val):
        self.count_val.text = f"{int(val)} alerts"
        self.app.data["alert_settings"]["count"] = int(val)
        save_data(self.app.data)

    def _toggle(self, *args):
        s = self.app.data["alert_settings"]
        s["enabled"] = not s["enabled"]
        save_data(self.app.data)
        if s["enabled"]:
            self.app.start_scheduler()
        else:
            self.app.stop_scheduler()
        self._refresh_toggle()

    def _refresh_toggle(self):
        enabled = self.app.data["alert_settings"]["enabled"]
        if enabled:
            self.toggle_btn.text = "⏹  Stop Scheduling"
            self.toggle_btn.background_color = get_color_from_hex("#555555")
            self.status_label.text = "✓ Alerts are active"
            self.status_label.color = get_color_from_hex("#4CAF50")
        else:
            self.toggle_btn.text = "▶  Start Scheduling"
            self.toggle_btn.background_color = ACCENT
            self.status_label.text = ""

    def go_back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "home"


class WheelScreen(Screen):
    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app = app_ref

        with self.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(size=lambda *a: setattr(self._bg, 'size', self.size))
        self.bind(pos=lambda *a: setattr(self._bg, 'pos', self.pos))

        outer = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(44))
        back = RoundButton(text="← Back", size_hint_x=0.3)
        back.bind(on_release=lambda *a: self.go_back())
        hdr.add_widget(back)
        hdr.add_widget(Label(text="Spin the Wheel", font_size=dp(18), bold=True, color=TEXT))
        outer.add_widget(hdr)

        # Mode toggle
        mode_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.btn_letters = RoundButton(text="Letters", accent=True)
        self.btn_colors = RoundButton(text="Colors", accent=False)
        self.btn_letters.bind(on_release=lambda *a: self.set_mode("letters"))
        self.btn_colors.bind(on_release=lambda *a: self.set_mode("colors"))
        mode_row.add_widget(self.btn_letters)
        mode_row.add_widget(self.btn_colors)
        outer.add_widget(mode_row)

        # Wheel
        self.wheel = WheelWidget(mode=self.app.data.get("wheel_mode", "letters"))
        outer.add_widget(self.wheel)

        # Result label
        self.result_label = Label(
            text="Tap SPIN!",
            font_size=dp(26),
            bold=True,
            color=ACCENT2,
            size_hint_y=None,
            height=dp(48)
        )
        outer.add_widget(self.result_label)

        # Spin button
        spin_btn = RoundButton(text="🎡  SPIN", accent=True)
        spin_btn.font_size = dp(18)
        spin_btn.height = dp(56)
        spin_btn.bind(on_release=self._spin)
        outer.add_widget(spin_btn)

        self.add_widget(outer)

    def set_mode(self, mode):
        self.app.data["wheel_mode"] = mode
        save_data(self.app.data)
        self.wheel.set_mode(mode)
        self.result_label.text = "Tap SPIN!"
        self.btn_letters.background_color = ACCENT if mode == "letters" else BTN_BG
        self.btn_colors.background_color = ACCENT if mode == "colors" else BTN_BG

    def _spin(self, *args):
        self.result_label.text = "..."
        self.wheel.spin(on_result=self._on_result)

    def _on_result(self, result):
        self.result_label.text = f"➤  {result}!"

    def go_back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "home"


class ScoreScreen(Screen):
    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app = app_ref

        with self.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(size=lambda *a: setattr(self._bg, 'size', self.size))
        self.bind(pos=lambda *a: setattr(self._bg, 'pos', self.pos))

        self.outer = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(44))
        back = RoundButton(text="← Back", size_hint_x=0.3)
        back.bind(on_release=lambda *a: self.go_back())
        hdr.add_widget(back)
        hdr.add_widget(Label(text="Scoreboard", font_size=dp(18), bold=True, color=TEXT))
        self.outer.add_widget(hdr)

        # Add player row
        add_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.name_input = TextInput(
            hint_text="Player name...",
            multiline=False,
            font_size=dp(14),
            background_color=BTN_BG,
            foreground_color=TEXT,
            hint_text_color=SUBTEXT,
            cursor_color=ACCENT
        )
        add_btn = RoundButton(text="+ Add", accent=True, size_hint_x=0.35)
        add_btn.bind(on_release=self._add_player)
        add_row.add_widget(self.name_input)
        add_row.add_widget(add_btn)
        self.outer.add_widget(add_row)

        # Scrollable score list
        self.scroll = ScrollView()
        self.score_grid = GridLayout(
            cols=1,
            spacing=dp(6),
            size_hint_y=None,
            padding=[0, dp(4)]
        )
        self.score_grid.bind(minimum_height=self.score_grid.setter("height"))
        self.scroll.add_widget(self.score_grid)
        self.outer.add_widget(self.scroll)

        self.add_widget(self.outer)

    def on_enter(self):
        self._refresh_list()

    def _refresh_list(self):
        self.score_grid.clear_widgets()
        scores = self.app.data.get("scores", [])
        # Sort by score descending
        sorted_scores = sorted(enumerate(scores), key=lambda x: x[1]["score"], reverse=True)

        for rank, (idx, player) in enumerate(sorted_scores):
            row = self._make_row(idx, player, rank + 1)
            self.score_grid.add_widget(row)

    def _make_row(self, idx, player, rank):
        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=[dp(10), 0],
            spacing=dp(8)
        )
        with row.canvas.before:
            Color(*BTN_BG)
            row._rect = RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(8)])
        row.bind(size=lambda w, s: setattr(w._rect, 'size', s))
        row.bind(pos=lambda w, p: setattr(w._rect, 'pos', p))

        medal = ["🥇", "🥈", "🥉"]
        rank_lbl = Label(
            text=medal[rank - 1] if rank <= 3 else str(rank),
            font_size=dp(16),
            size_hint_x=None,
            width=dp(36),
            color=TEXT
        )
        row.add_widget(rank_lbl)

        name_lbl = Label(
            text=player["name"],
            font_size=dp(15),
            color=TEXT,
            halign="left",
            valign="middle"
        )
        name_lbl.bind(size=lambda w, s: setattr(w, 'text_size', s))
        row.add_widget(name_lbl)

        score_lbl = Label(
            text=str(player["score"]),
            font_size=dp(20),
            bold=True,
            color=ACCENT2,
            size_hint_x=None,
            width=dp(60)
        )
        row.add_widget(score_lbl)

        # +/- buttons
        minus_btn = Button(
            text="−",
            font_size=dp(20),
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            background_normal="",
            background_color=get_color_from_hex("#333355"),
            color=TEXT
        )
        minus_btn.bind(on_release=lambda *a, i=idx: self._change_score(i, -1))

        plus_btn = Button(
            text="+",
            font_size=dp(20),
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            background_normal="",
            background_color=ACCENT,
            color=TEXT
        )
        plus_btn.bind(on_release=lambda *a, i=idx: self._change_score(i, 1))

        del_btn = Button(
            text="✕",
            font_size=dp(14),
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            background_normal="",
            background_color=get_color_from_hex("#550000"),
            color=TEXT
        )
        del_btn.bind(on_release=lambda *a, i=idx: self._delete_player(i))

        row.add_widget(minus_btn)
        row.add_widget(plus_btn)
        row.add_widget(del_btn)

        return row

    def _add_player(self, *args):
        name = self.name_input.text.strip()
        if not name:
            return
        self.app.data["scores"].append({"name": name, "score": 0})
        save_data(self.app.data)
        self.name_input.text = ""
        self._refresh_list()

    def _change_score(self, idx, delta):
        self.app.data["scores"][idx]["score"] += delta
        save_data(self.app.data)
        self._refresh_list()

    def _delete_player(self, idx):
        self.app.data["scores"].pop(idx)
        save_data(self.app.data)
        self._refresh_list()

    def go_back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "home"


# ─── Main App ─────────────────────────────────────────────────────────────────

class SpinAlertApp(App):
    def build(self):
        self.data = load_data()
        self._scheduler_thread = None
        self._scheduler_running = False

        Window.clearcolor = BG

        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home", app_ref=self))
        sm.add_widget(AlertScreen(name="alerts", app_ref=self))
        sm.add_widget(WheelScreen(name="wheel", app_ref=self))
        sm.add_widget(ScoreScreen(name="scores", app_ref=self))

        # Resume scheduler if it was enabled
        if self.data["alert_settings"].get("enabled"):
            self.start_scheduler()

        return sm

    # ── Notification scheduler ──────────────────────────────────────────────

    def start_scheduler(self):
        if self._scheduler_running:
            return
        self._scheduler_running = True
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop, daemon=True
        )
        self._scheduler_thread.start()

    def stop_scheduler(self):
        self._scheduler_running = False

    def _scheduler_loop(self):
        """Background: N random alerts between start_h and end_h, using time left in window today."""
        while self._scheduler_running:
            s = self.data["alert_settings"]
            start_h = s["start_hour"]
            end_h = s["end_hour"]
            count = max(1, int(s["count"]))

            if end_h <= start_h:
                end_h = min(23, start_h + 1)

            now = datetime.now()
            day_start = now.replace(hour=start_h, minute=0, second=0, microsecond=0)
            day_end = now.replace(hour=end_h, minute=0, second=0, microsecond=0)

            if now < day_start:
                self._interruptible_sleep(
                    max(0, (day_start - datetime.now()).total_seconds())
                )
                continue

            if now >= day_end:
                next_morning = datetime.combine(
                    now.date() + timedelta(days=1), dt_time(start_h, 0, 0)
                )
                self._interruptible_sleep(
                    max(0, (next_morning - datetime.now()).total_seconds())
                )
                continue

            t0 = now
            span = (day_end - t0).total_seconds()
            if span <= 0:
                self._interruptible_sleep(60)
                continue

            times = sorted(
                t0 + timedelta(seconds=random.random() * span) for _ in range(count)
            )

            for t in times:
                if not self._scheduler_running:
                    return
                wait = (t - datetime.now()).total_seconds()
                if wait > 0:
                    self._interruptible_sleep(wait)
                if not self._scheduler_running:
                    return
                self._send_notification()

            fn = datetime.now()
            next_morning = datetime.combine(
                fn.date() + timedelta(days=1), dt_time(start_h, 0, 0)
            )
            self._interruptible_sleep(
                max(0, (next_morning - datetime.now()).total_seconds())
            )

    def _interruptible_sleep(self, seconds):
        """Sleep in small chunks so we can respond to stop quickly."""
        end = time.time() + seconds
        while self._scheduler_running and time.time() < end:
            time.sleep(min(5, end - time.time()))

    def _send_notification(self):
        if HAS_NOTIFICATIONS:
            try:
                notification.notify(
                    title="⏰ SpinAlert!",
                    message="Time to open the app and spin the wheel!",
                    app_name="SpinAlert",
                    timeout=10
                )
            except Exception as e:
                print(f"Notification error: {e}")
        else:
            print("[SpinAlert] Notification triggered (plyer not available on this platform)")

        def go_to_wheel(dt):
            if self.root:
                self.root.current = "wheel"

        Clock.schedule_once(go_to_wheel, 0)

    def on_stop(self):
        self.stop_scheduler()


if __name__ == "__main__":
    SpinAlertApp().run()