from dataclasses import dataclass
import math
from typing import Literal

import pygame
import pygame_gui
from pygame import Color, Vector2, freetype

from utils import Slider, Timer

FONT_FILE = None

freetype.init()
FONT = freetype.Font(FONT_FILE, 20)
HUGE_FONT = freetype.Font(FONT_FILE, 150)


def paint(text: str, color: Color) -> str:
    hex_color = "#{:02x}{:02x}{:02x}".format(color.r, color.g, color.b)
    return f"<font color={hex_color}>{text}</font>"


def bold(text: str) -> str:
    return f"<b>{text}</b>"


@dataclass
class FpsInfo:
    target_fps: int

    def __post_init__(self):
        self.fps_history: list[float] = []
        self.min_fps = math.inf
        self.max_fps = -math.inf

    def update(self, time_delta: float):
        self.fps_history.append(1.0 / time_delta)

    def calc_stats(self) -> tuple[float, float, float, float, int]:
        num_ticks = len(self.fps_history)
        avg_fps = sum(self.fps_history) / num_ticks
        self.fps_history.sort()
        SMOOTH_WINDOW_SIZE = 100
        min_fps = sum(self.fps_history[:SMOOTH_WINDOW_SIZE]) / SMOOTH_WINDOW_SIZE
        max_fps = sum(self.fps_history[-SMOOTH_WINDOW_SIZE:]) / SMOOTH_WINDOW_SIZE
        std_fps = (
            sum((fps - avg_fps) ** 2 for fps in self.fps_history)
            / len(self.fps_history)
        ) ** 0.5
        return avg_fps, min_fps, max_fps, std_fps, num_ticks

    def verdict(self) -> str:
        avg_fps, min_fps, _, std_fps, num_ticks = self.calc_stats()
        if num_ticks < 100:
            return ""
        problems = []
        if min_fps < self.target_fps * 0.3:
            problems.append(
                f"[Freezes] minimum framerate falls below 30% the target fps ({min_fps:.2f})"
            )
        if std_fps > self.target_fps * 0.15:
            problems.append(
                f"[Jumps] standard deviation of the framerate is too high ({std_fps:.2f})"
            )
        if avg_fps < self.target_fps * 0.9:
            problems.append(
                f"[Jitters] average framerate is below 90% of the target fps ({avg_fps:.2f} < {self.target_fps}) * 0.9"
            )
        return "\n".join(problems)

    def __str__(self) -> str:
        avg_fps, min_fps, max_fps, std_fps, num_ticks = self.calc_stats()
        return f"FPSINFO({avg_fps:.2f}±{std_fps:.2f} (min-max: {min_fps:.2f}-{max_fps:.2f}; target: {self.target_fps}); {num_ticks} ticks)"


class ColorGradient:
    def __init__(self, start_color: Color, end_color: Color):
        self.start_color = start_color
        self.end_color = end_color

    def __call__(self, percent: float) -> Color:
        return Color(
            int(self.start_color.r + (self.end_color.r - self.start_color.r) * percent),
            int(self.start_color.g + (self.end_color.g - self.start_color.g) * percent),
            int(self.start_color.b + (self.end_color.b - self.start_color.b) * percent),
            int(self.start_color.a + (self.end_color.a - self.start_color.a) * percent),
        )


class Label:
    def __init__(
        self,
        text: str,
        surface: pygame.Surface,
        rect: pygame.Rect | None = None,
        position: Vector2 | None = None,
        color: Color = Color("white"),
        anker: Literal[
            "center", "topleft", "topright", "bottomleft", "bottomright"
        ] = "center",
        font: freetype.Font = FONT,
    ):
        self.font = font
        self.position = position
        self.rect = rect
        if self.rect is None and self.position is None:
            raise ValueError("either rect or position must be given")

        self.text = text
        self.surface = surface
        self.color = color
        if self.rect is None and self.position is not None:
            self.rect = pygame.Rect(0, 0, 100, 40)
            if anker == "center":
                self.rect.center = self.position
            elif anker == "topleft":
                self.rect.topleft = self.position
            elif anker == "topright":
                self.rect.topright = self.position
            elif anker == "bottomleft":
                self.rect.bottomleft = self.position

    def draw(self):
        self.font.render_to(self.surface, self.rect, self.text, self.color)  # type: ignore

    def update(self):
        self.draw()

    def set_text(self, text: str):
        self.text = text

    def set_color(self, color: Color):
        self.color = color


class TextBox:
    def __init__(
        self,
        text_lines: list[str],
        position: Vector2,
        surface: pygame.Surface,
    ):
        self.labels: list[Label]
        self.text_lines = text_lines
        self.position = position
        self.surface = surface
        self.rebuild(self.position)

    def rebuild(self, top_left: Vector2):
        r = pygame.Rect(0, 0, 200, 25)
        r.topleft = top_left
        self.rects = [r]
        for _ in range(len(self.text_lines) - 1):
            r = self.rects[-1].copy()
            r.topleft = r.bottomleft
            r.y += 2.0
            self.rects.append(r)
        assert len(self.rects) == len(self.text_lines)
        self.labels = [
            Label(text, self.surface, rect)
            for text, rect in zip(self.text_lines, self.rects)
        ]
        for i, r in enumerate(self.rects):
            self.labels[i].rect = r

    def total_size(self) -> Vector2:
        return Vector2(self.rects[-1].bottomright) - Vector2(self.rects[0].topleft)

    def set_bottom_right(self, bottom_right: Vector2):
        position = bottom_right - self.total_size()
        self.rebuild(position)

    def set_top_right(self, top_right: Vector2):
        position = top_right - Vector2(self.total_size().x, 0)
        self.rebuild(position)

    def set_bottom_left(self, bottom_left: Vector2):
        position = bottom_left - Vector2(0, self.total_size().y)
        self.rebuild(position)

    def update(self):
        for label in self.labels:
            label.update()

    def set_lines(self, text_lines: list[str]):
        assert len(text_lines) == len(
            self.labels
        ), f"{len(text_lines)=} != {len(self.labels)=}"
        self.text_lines = text_lines
        for label, text in zip(self.labels, self.text_lines):
            label.set_text(text)


class ProgressBar(pygame_gui.elements.UIStatusBar):
    def __init__(
        self, color_gradient_pair: tuple[Color, Color], slider: Slider, **kwargs
    ):
        self.slider = slider
        self.old_text = ""
        self.new_text = ""
        super().__init__(**kwargs)
        self.color_gradient = ColorGradient(*color_gradient_pair)

    def update(self, time_delta: float):
        super().update(time_delta)
        self.update_percent_full()
        self.new_text = str(self.slider)
        if self.old_text != self.new_text:
            self.status_changed = True
        self.old_text = self.new_text

    def status_text(self):
        return self.new_text

    def update_percent_full(self):
        self.percent_full = self.slider.get_percent_full()
        self.bar_filled_colour = self.color_gradient(self.percent_full)


class Notification(Label):
    def __init__(
        self,
        text: str,
        position: Vector2,
        surface: pygame.Surface,
        duration: float = 3.0,
        color: Color = Color("white"),
        **kwargs,
    ):
        super().__init__(
            text=text,
            surface=surface,
            position=position,
            color=color,
            anker="center",
            **kwargs,
        )
        self.lifetime_timer = Timer(max_time=duration)
        self._is_alive = True

    def update(self, time_delta: float):
        self.lifetime_timer.tick(time_delta)
        self.rect.y -= 3.0 * time_delta  # type: ignore
        if not self.lifetime_timer.running():
            self._is_alive = False
        if self._is_alive:
            super().update()
