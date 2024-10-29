from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Literal

import pygame
from pygame import Surface, Vector2, Color
from screen import Screen, FRAMERATE

from utils import random_unit_vector


# colors:
WHITE = Color("white")
MAGENTA = Color("magenta")
GREEN = Color("green")
GRAY = Color("gray")

ACCELERATION_ROTATION_PER_SCROLL = 20
FRICTION_PER_SECOND = 0.05  # vel amplitude is decreased by 5% per second

FRICTION_COEFF = (1 - FRICTION_PER_SECOND) ** (1 / FRAMERATE)

PLAYER_SIZE = 12
PLAYER_ACC_AMPLITUDE = 500.0


def get_mouse_pos() -> Vector2:
    return Vector2(pygame.mouse.get_pos())


class Entity(ABC):
    def __init__(
        self,
        pos: Vector2,
        vel: Vector2,
        size: int,
        acc: Vector2 | None = None,
    ):
        self.pos = pos
        self.vel = vel
        self.size = size
        self.acc = Vector2(0, 0) if acc is None else acc

    @abstractmethod
    def update(self, time_delta: float):
        self.pos += self.vel * time_delta
        self.vel += self.acc * time_delta
        self.vel *= FRICTION_COEFF


@dataclass
class Engine:
    strength: int
    _on: bool = False
    _speedup: bool = False

    def get(self) -> int:
        if not self._on:
            return 0
        return self.strength if self._speedup else 1

    def on(self) -> None:
        self._on = True

    def off(self) -> None:
        self._on = False

    def set_speedup(self, speedup: bool) -> None:
        self._speedup = speedup

    def __bool__(self) -> bool:
        return self._on


class Player(Entity):
    def __init__(self, pos: Vector2, vel: Vector2, acc: Vector2):
        super().__init__(pos, vel, PLAYER_SIZE, acc)
        self.engine = Engine(strength=5)

    def update(self, time_delta: float):
        self.pos += self.vel * time_delta
        self.vel += self.engine.get() * self.acc * time_delta
        self.vel *= FRICTION_COEFF

    def rotate_acc(self, angle: float):
        self.acc.rotate_ip(angle)


class Game:
    def __init__(self, surface_rect: pygame.Rect):
        self.surface_rect = surface_rect
        self.center = Vector2(surface_rect.center)
        self.player = Player(
            Vector2(600.0, 200.0),
            Vector2(0.0, 0.0),
            PLAYER_ACC_AMPLITUDE * random_unit_vector(),
        )

    def update(self, time_delta):
        self.player.update(time_delta)

        # toroidal space
        if not self.surface_rect.collidepoint(self.player.pos):
            if self.player.pos.x < 0:
                self.player.pos.x = self.surface_rect.width
            elif self.player.pos.x > self.surface_rect.width:
                self.player.pos.x = 0
            if self.player.pos.y < 0:
                self.player.pos.y = self.surface_rect.height
            elif self.player.pos.y > self.surface_rect.height:
                self.player.pos.y = 0


class GameScreen(Screen):
    def __init__(self, surface: Surface, control_type: Literal['scroll', 'cursor'] = 'cursor'):
        super().__init__(surface)
        self.game = Game(surface.get_rect())
        self.control_type = control_type

    def process_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.control_type == 'scroll' and event.button in {4, 5}:
                self.game.player.rotate_acc(
                    (1 if event.button == 4 else -1) * ACCELERATION_ROTATION_PER_SCROLL
                )
            elif event.button == 1:
                self.game.player.engine.on()
            elif event.button == 3:
                self.game.player.engine.set_speedup(True)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.game.player.engine.off()
            elif event.button == 3:
                self.game.player.engine.set_speedup(False)
        elif self.control_type == 'cursor' and event.type == pygame.MOUSEMOTION:
            acc_magn = self.game.player.acc.magnitude()
            self.game.player.acc = (get_mouse_pos() - self.game.center).normalize() * acc_magn
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.is_running = False

    def update(self, time_delta):
        self.game.update(time_delta)

        # drawing
        pygame.draw.circle(
            self.surface,
            WHITE if not self.game.player.engine else MAGENTA,
            self.game.player.pos,
            10,
        )
        pygame.draw.line(
            self.surface,
            GRAY if not self.game.player.engine else MAGENTA,
            self.game.player.pos,
            self.game.player.pos + self.game.player.acc.normalize() * 30,
            width=self.game.player.engine.get() * 2 + 1,
        )
        pygame.draw.line(
            self.surface,
            GREEN,
            self.game.player.pos,
            self.game.player.pos + self.game.player.vel * 0.1,
            width=2,
        )

        # cursor controls
        if self.control_type == 'cursor':
            pygame.draw.circle(self.surface, GREEN, self.game.center, 40, 2)
            pygame.draw.circle(
                self.surface,
                GREEN,
                self.game.center + self.game.player.acc.normalize() * 40,
                5,
            )


def main():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    game_screen = GameScreen(screen, control_type='cursor')
    game_screen.run()
    pygame.quit()


if __name__ == "__main__":
    main()
