import random
import math

from pygame import Vector2


def random_unit_vector() -> Vector2:
    alpha = random.random() * 2 * math.pi
    return Vector2(math.cos(alpha), math.sin(alpha))


class Slider:
    def __init__(self, max_value: float, current_value: float | None = None):
        self.max_value = max_value
        self.current_value = current_value if current_value is not None else max_value

    def is_alive(self) -> bool:
        return self.current_value > 0

    def get_value(self) -> float:
        return self.current_value

    def get_percent_full(self) -> float:
        return self.current_value / self.max_value

    def set_percent_full(self, percent: float) -> None:
        self.current_value = self.max_value * percent

    def set_new_max_value(self, new_max_value: float) -> None:
        percent_full = self.get_percent_full()
        self.max_value = new_max_value
        self.set_percent_full(percent_full)

    def change(self, delta: float) -> float:
        """Change the current value by delta. Return by how much it actually changed."""
        cache_current_value = self.current_value
        self.current_value += delta
        self.current_value = min(self.current_value, self.max_value)
        self.current_value = max(self.current_value, 0.0)
        return self.current_value - cache_current_value

    def __repr__(self) -> str:
        return f"Slider({self})"

    def __str__(self) -> str:
        return f"{self.current_value:.0f}/{self.max_value:.0f}"


class Timer:
    """
    Counts time in seconds.
    """

    def __init__(self, max_time: float):
        self.max_time = max_time
        self.current_time = 0.0

    def tick(self, time_delta: float) -> None:
        self.current_time += time_delta

    def turn_off(self) -> None:
        self.current_time = self.max_time + 0.01

    def get_time_left(self) -> float:
        return self.max_time - self.current_time

    def running(self) -> bool:
        return self.current_time < self.max_time

    def get_value(self) -> float:
        return self.current_time

    def reset(self, with_max_time: float | None = None) -> None:
        if with_max_time is not None:
            self.max_time = with_max_time
        self.current_time = 0.0

    def get_percent_full(self) -> float:
        return self.current_time / self.max_time

    def set_percent_full(self, percent: float) -> None:
        self.current_time = self.max_time * percent

    def get_slider(self, reverse=False) -> Slider:
        if reverse:
            return Slider(self.max_time, self.max_time - self.current_time)
        return Slider(self.max_time, self.current_time)

    def __repr__(self) -> str:
        return f"Timer({self.current_time:.1f}/{self.max_time:.1f})"
