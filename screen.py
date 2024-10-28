from abc import ABC, abstractmethod

import pygame
import pygame_gui

from front_utils import FpsInfo


FRAMERATE = 60


class Screen(ABC):
    """Abstract class for all screens in the game."""

    def __init__(
        self,
        surface: pygame.Surface,
        bg_color: str = '#202020',
        framerate: int = FRAMERATE,
    ):
        self.surface = surface
        self.framerate = framerate
        self.window_size = self.surface.get_rect().size
        self.background = pygame.Surface(self.window_size)
        self.background.fill(pygame.Color(bg_color))
        self.manager = pygame_gui.UIManager(self.window_size)
        self.is_running = True

        # adding the quit button
        quit_button_rect = pygame.Rect(0, 0, 0, 0)
        quit_button_rect.size = (15, 15)
        quit_button_rect.topright = self.surface.get_rect().topright
        self.quit_button = pygame_gui.elements.UIButton(
            relative_rect=quit_button_rect, text="x", manager=self.manager
        )
        self.clock = pygame.time.Clock()
        self.fps_info = FpsInfo(framerate)

    @abstractmethod
    def process_event(self, event: pygame.event.Event):
        ...

    @abstractmethod
    def update(self, time_delta: float):
        ...

    def post_run(self):
        ...

    def process_ui_event(self, event: pygame.event.Event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.quit_button:
                self.is_running = False
        ...

    def run(self) -> FpsInfo:
        """Main loop. Returns the FPSinfo object."""
        while self.is_running:
            time_delta = self.clock.tick(self.framerate) / 1000.0
            self.fps_info.update(time_delta)
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.is_running = False
                if event.type == pygame.QUIT:
                    self.is_running = False
                self.process_ui_event(event)
                if not self.manager.process_events(event):
                    self.process_event(event)
            self.surface.blit(self.background, (0, 0))
            self.manager.update(time_delta)
            self.update(time_delta)
            self.manager.draw_ui(self.surface)
            pygame.display.update()
        self.post_run()
        return self.fps_info