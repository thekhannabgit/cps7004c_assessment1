from __future__ import annotations

import random
from collections import deque
from typing import List, Optional, TYPE_CHECKING

from model.agent import Agent
from model.location import Location

if TYPE_CHECKING:
    from model.mars import Mars
    from model.bridge import Bridge


class SilverSurfer(Agent):
    max_energy: int = 100

    def __init__(self, location: Location) -> None:
        super().__init__(location)
        self.energy = self.max_energy
        self.retreating = False
        self.last_target_xy: tuple[int, int] | None = None
        self.target_cooldown: int = 0

    def at_same_cell(self, mars: 'Mars', loc: Location) -> bool:
        return (
            self.get_location().get_x() % mars.get_width() == loc.get_x() % mars.get_width() and
            self.get_location().get_y() % mars.get_height() == loc.get_y() % mars.get_height()
        )

    def distance(self, loc1: Location, loc2: Location, mars: 'Mars') -> int:
        width = mars.get_width()
        height = mars.get_height()
        dx = abs(loc1.get_x() - loc2.get_x())
        dy = abs(loc1.get_y() - loc2.get_y())
        dx = min(dx, width - dx)
        dy = min(dy, height - dy)
        return dx + dy

    def bfs_path(self, start: Location, goal: Location, mars: 'Mars') -> List[Location]:
        width = mars.get_width()
        height = mars.get_height()
        start_coords = (start.get_x(), start.get_y())
        goal_coords = (goal.get_x(), goal.get_y())
        visited = set([start_coords])
        queue: deque[tuple[tuple[int, int], List[tuple[int, int]]]] = deque()
        queue.append((start_coords, []))
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        while queue:
            (cx, cy), path = queue.popleft()
            if (cx, cy) == goal_coords:
                return [Location(coords[0], coords[1]) for coords in path]
            for dx, dy in directions:
                nx = (cx + dx) % width
                ny = (cy + dy) % height
                if (nx, ny) not in visited:
                    occupant = mars.get_agent(Location(nx, ny))
                    if occupant is None or (nx, ny) == goal_coords:
                        visited.add((nx, ny))
                        queue.append(((nx, ny), path + [(nx, ny)]))
        return []

    def find_target_bridge(self, mars: 'Mars') -> Optional['Bridge']:
        bridges = mars.get_all_bridges()
        if not bridges:
            return None
        candidates: list['Bridge'] = []
        for b in bridges:
            if b.is_complete() or getattr(b, "damaged", False):
                continue
            occupant = mars.get_agent(b.location)
            if occupant is not None and not isinstance(occupant, SilverSurfer):
                continue
            if self.target_cooldown > 0 and self.last_target_xy is not None:
                if (b.location.get_x() % mars.get_width(), b.location.get_y() % mars.get_height()) == self.last_target_xy:
                    continue
            candidates.append(b)
        if not candidates:
            return None
        candidates.sort(key=lambda b: self.distance(self.get_location(), b.location, mars))
        return candidates[0]

    def act(self, mars: 'Mars') -> None:
        if self.energy < 20:
            self.retreating = True
            self.energy = min(self.max_energy, self.energy + 5)
            dir = random.choice([(-1,0),(1,0),(0,-1),(0,1)])
            nx = (self.get_location().get_x() + dir[0]) % mars.get_width()
            ny = (self.get_location().get_y() + dir[1]) % mars.get_height()
            if mars.get_agent(Location(nx, ny)) is None:
                mars.set_agent(None, self.get_location())
                new_loc = Location(nx, ny)
                mars.set_agent(self, new_loc)
                self.set_location(new_loc)
            if self.energy >= 40:
                self.retreating = False
            return

        if self.target_cooldown > 0:
            self.target_cooldown -= 1

        target_bridge = self.find_target_bridge(mars)
        if target_bridge is None:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for _ in range(2):
                random.shuffle(directions)
                moved = False
                for dx, dy in directions:
                    nx = (self.get_location().get_x() + dx) % mars.get_width()
                    ny = (self.get_location().get_y() + dy) % mars.get_height()
                    new_loc = Location(nx, ny)
                    occupant = mars.get_agent(new_loc)
                    if occupant is None:
                        mars.set_agent(None, self.get_location())
                        mars.set_agent(self, new_loc)
                        self.set_location(new_loc)
                        self.energy = max(0, self.energy - 1)
                        moved = True
                        break
                if not moved:
                    break
            return

        steps = 2
        for _ in range(steps):
            if self.distance(self.get_location(), target_bridge.location, mars) == 0:
                break
            path = self.bfs_path(self.get_location(), target_bridge.location, mars)
            if not path:
                break
            next_loc = path[0]
            mars.set_agent(None, self.get_location())
            new_loc = Location(next_loc.get_x(), next_loc.get_y())
            mars.set_agent(self, new_loc)
            self.set_location(new_loc)
            self.energy = max(0, self.energy - 1)

        if self.at_same_cell(mars, target_bridge.location):
            if self.energy > 0:
                target_bridge.damage(20)
                self.energy = max(0, self.energy - 5)
                self.last_target_xy = (
                    target_bridge.location.get_x() % mars.get_width(),
                    target_bridge.location.get_y() % mars.get_height(),
                )
                self.target_cooldown = 6
