from __future__ import annotations

import random
from collections import deque
from typing import List, Optional, TYPE_CHECKING

from model.agent import Agent
from model.location import Location

if TYPE_CHECKING:
    from model.location import Location
    from model.mars import Mars
    from model.bridge import Bridge


class Hero(Agent):

    max_energy: int = 100
    repair_rate: int = 10
    attack_range: int = 1
    name: str = "Hero"

    def __init__(self, location: Location) -> None:
        super().__init__(location)
        self.energy = self.max_energy
        self.is_recharging = False

    def hq_location(self, mars: 'Mars') -> Location:

        return Location(mars.get_width() // 2, mars.get_height() // 2)

    def at_location(self, mars: 'Mars', a: Location, b: Location) -> bool:

        return (
            a.get_x() % mars.get_width() == b.get_x() % mars.get_width() and
            a.get_y() % mars.get_height() == b.get_y() % mars.get_height()
        )

    def __repr__(self) -> str:
        return f"{self.name}(energy={self.energy})"

    def distance(self, loc1: Location, loc2: Location, mars: 'Mars') -> int:

        width = mars.get_width()
        height = mars.get_height()
        dx = abs(loc1.get_x() - loc2.get_x())
        dy = abs(loc1.get_y() - loc2.get_y())
        dx = min(dx, width - dx)
        dy = min(dy, height - dy)
        return dx + dy

    def find_nearest_bridge(self, mars: 'Mars') -> Optional['Bridge']:

        bridges = mars.get_all_bridges()
        if not bridges:
            return None
        candidate_bridges = [b for b in bridges if not b.is_complete() or b.damaged]
        if not candidate_bridges:
            return None
        current_location = self.get_location()
        candidate_bridges.sort(key=lambda b: self.distance(current_location, b.location, mars))
        return candidate_bridges[0]

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

    def move_towards(self, target: Location, mars: 'Mars') -> None:

        path = self.bfs_path(self.get_location(), target, mars)
        if not path:
            return
        next_location = path[0]
        if self.energy > 0:
            self.energy = max(0, self.energy - 1)
        mars.set_agent(None, self.get_location())
        new_loc = Location(next_location.get_x(), next_location.get_y())
        mars.set_agent(self, new_loc)
        self.set_location(new_loc)

    def act(self, mars: 'Mars') -> None:

        self.check_recharge(mars)

        hq = self.hq_location(mars)

        if self.energy <= 10 and not self.at_location(mars, self.get_location(), hq):
            self.move_towards(hq, mars)
            return

        if self.energy <= 0:
            if not self.at_location(mars, self.get_location(), hq):
                self.move_towards(hq, mars)
            return

        bridge = self.find_nearest_bridge(mars)
        if bridge is None:
            return
        current_loc = self.get_location()
        if self.at_location(mars, current_loc, bridge.location):
            if self.energy > 0:
                amount = self.repair_rate
                bridge.repair(amount)
                self.energy = max(0, self.energy - 2)
        else:
            self.move_towards(bridge.location, mars)

    def check_recharge(self, mars: 'Mars') -> None:

        centre_x = mars.get_width() // 2
        centre_y = mars.get_height() // 2
        loc = self.get_location()
        if loc.get_x() % mars.get_width() == centre_x and loc.get_y() % mars.get_height() == centre_y:
            self.energy = min(self.max_energy, self.energy + 20)


class ReedRichards(Hero):

    name = "Reed"

    def act(self, mars: 'Mars') -> None:

        self.check_recharge(mars)
        hq = self.hq_location(mars)
        if self.energy <= 10 and not self.at_location(mars, self.get_location(), hq):
            self.move_towards(hq, mars)
            return
        if self.energy <= 0:
            if not self.at_location(mars, self.get_location(), hq):
                self.move_towards(hq, mars)
            return

        surfer = None
        for row in range(mars.get_height()):
            for col in range(mars.get_width()):
                agent = mars.get_agent(Location(col, row))
                if agent and agent.__class__.__name__ == 'SilverSurfer':
                    surfer = agent
                    break
            if surfer:
                break

        if surfer:
            bridges = mars.get_all_bridges()
            candidates = [b for b in bridges if not b.is_complete() or getattr(b, "damaged", False)]
            target_bridge: Optional['Bridge']
            if candidates:
                candidates.sort(key=lambda b: self.distance(b.location, surfer.get_location(), mars))
                target_bridge = candidates[0]
            else:
                target_bridge = None
        else:
            target_bridge = self.find_nearest_bridge(mars)

        if target_bridge is None:
            return

        if self.at_location(mars, self.get_location(), target_bridge.location):
            if self.energy > 0:
                target_bridge.repair(self.repair_rate)
                self.energy = max(0, self.energy - 2)
        else:
            self.move_towards(target_bridge.location, mars)


class SueStorm(Hero):
    name = "Sue"

    def act(self, mars: 'Mars') -> None:

        self.check_recharge(mars)

        hq = self.hq_location(mars)
        if self.energy <= 10 and not self.at_location(mars, self.get_location(), hq):
            self.move_towards(hq, mars)
            return
        if self.energy <= 0:
            if not self.at_location(mars, self.get_location(), hq):
                self.move_towards(hq, mars)
            return

        bridge = self.find_nearest_bridge(mars)
        if bridge is None:
            return
        current_loc = self.get_location()
        if self.at_location(mars, current_loc, bridge.location):
            bridge.damaged = False
            bridge.repair(self.repair_rate)
            self.energy = max(0, self.energy - 2)
        else:
            self.move_towards(bridge.location, mars)


class JohnnyStorm(Hero):

    name = "Johnny"
    attack_range = 3

    def act(self, mars: 'Mars') -> None:

        self.check_recharge(mars)

        hq = self.hq_location(mars)
        if self.energy <= 10 and not self.at_location(mars, self.get_location(), hq):
            self.move_towards(hq, mars)
            return
        if self.energy <= 0:
            if not self.at_location(mars, self.get_location(), hq):
                self.move_towards(hq, mars)
            return

        target_surfer = None
        for row in range(mars.get_height()):
            for col in range(mars.get_width()):
                agent = mars.get_agent(Location(col, row))
                if agent and agent.__class__.__name__ == 'SilverSurfer':
                    dist = self.distance(self.get_location(), agent.get_location(), mars)
                    if dist <= self.attack_range:
                        target_surfer = agent
                        break
            if target_surfer:
                break
        if target_surfer:
            if self.energy > 0:
                target_surfer.energy = max(0, target_surfer.energy - 10)
                self.energy = max(0, self.energy - 5)
                return
        super().act(mars)


class BenGrimm(Hero):

    name = "Ben"
    repair_rate = 20

    def act(self, mars: 'Mars') -> None:

        self.check_recharge(mars)

        hq = self.hq_location(mars)
        if self.energy <= 10 and not self.at_location(mars, self.get_location(), hq):
            self.move_towards(hq, mars)
            return
        if self.energy <= 0:
            if not self.at_location(mars, self.get_location(), hq):
                self.move_towards(hq, mars)
            return

        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx = (self.get_location().get_x() + dx) % mars.get_width()
            ny = (self.get_location().get_y() + dy) % mars.get_height()
            agent = mars.get_agent(Location(nx, ny))
            if agent and agent.__class__.__name__ == 'SilverSurfer':
                agent.energy = max(0, agent.energy - 20)
                self.energy = max(0, self.energy - 5)
                return
        super().act(mars)