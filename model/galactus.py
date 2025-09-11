from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from model.agent import Agent
from model.location import Location

if TYPE_CHECKING:
    from model.mars import Mars
    from model.bridge import Bridge


class GalactusProjection(Agent):

    def __init__(self, location: Location, franklin_location: Location) -> None:
        super().__init__(location)
        self.franklin_location = franklin_location
        self._step_counter = 0

    def act(self, mars: 'Mars') -> None:
        self._step_counter = (self._step_counter + 1) % 2
        if self._step_counter == 1:
            return
        bridges = mars.get_all_bridges()
        target_loc = self.franklin_location
        if bridges:
            # Compute centroid of bridges needing attention
            incomplete = [b for b in bridges if not b.is_complete() or b.damaged]
            if incomplete:
                xs = [b.location.get_x() for b in incomplete]
                ys = [b.location.get_y() for b in incomplete]
                cx = sum(xs) // len(xs)
                cy = sum(ys) // len(ys)
                target_loc = Location(cx, cy)
        current = self.get_location()
        dx = (target_loc.get_x() - current.get_x())
        dy = (target_loc.get_y() - current.get_y())
        width = mars.get_width()
        height = mars.get_height()
        if abs(dx) > width // 2:
            dx = -1 if dx > 0 else 1
        else:
            dx = 0 if dx == 0 else (1 if dx > 0 else -1)
        if abs(dy) > height // 2:
            dy = -1 if dy > 0 else 1
        else:
            dy = 0 if dy == 0 else (1 if dy > 0 else -1)
        nx = (current.get_x() + dx) % width
        ny = (current.get_y() + dy) % height
        next_loc = Location(nx, ny)
        bridge = mars.get_bridge(next_loc)
        if bridge:
            mars.remove_bridge(next_loc)
        agent = mars.get_agent(next_loc)
        if agent:
            mars.set_agent(None, next_loc)
        if (nx, ny) == (self.franklin_location.get_x(), self.franklin_location.get_y()):
            mars.mission_failed = True  # type: ignore[attr-defined]
        mars.set_agent(None, current)
        mars.set_agent(self, next_loc)
        self.set_location(next_loc)