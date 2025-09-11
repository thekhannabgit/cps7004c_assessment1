from __future__ import annotations

import heapq
import itertools
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from controller.config import Config
from model.agent import Agent
from model.location import Location
from model.bridge import Bridge

if TYPE_CHECKING:
    from model.earth import Earth
    from model.silver_surfer import SilverSurfer
    from model.galactus import GalactusProjection
    from model.hero import Hero


@dataclass
class PathNode:
    f: float
    g: float
    h: float
    location: Location
    parent: Optional['PathNode']


class Hero(Agent):
    max_energy: int = 100
    move_cost: int = 1
    repair_cost: int = 1
    attack_cost: int = 2
    shield_cost: int = 3

    def __init__(self, name: str, location: Location, hq_location: Location) -> None:
        super().__init__(location)
        self.name: str = name
        self._energy: int = self.max_energy
        self.hq_location: Location = hq_location
        # track if shield active for Sue; number of steps left
        self._shield_duration: int = 0

    @property
    def energy(self) -> int:
        return self._energy

    def consume_energy(self, amount: int) -> None:
        self._energy = max(self._energy - amount, 0)

    def recharge(self) -> None:
        if self._energy < self.max_energy:
            self._energy += 1

    def is_exhausted(self) -> bool:
        return self._energy <= 0

    def _loc_key(self, loc: Location, width: Optional[int] = None, height: Optional[int] = None) -> Tuple[int, int]:
        if width is None or height is None:
            # fallback when environment sizes aren't provided
            return (loc.get_x(), loc.get_y())
        return (loc.get_x() % width, loc.get_y() % height)

    def _heuristic(self, a: Location, b: Location, width: int, height: int) -> int:
        dx = abs(a.get_x() - b.get_x())
        dy = abs(a.get_y() - b.get_y())
        dx = min(dx, width - dx)
        dy = min(dy, height - dy)
        return dx + dy

    def _neighbors4(self, loc: Location, width: int, height: int) -> List[Location]:
        x, y = loc.get_x(), loc.get_y()
        return [
            Location((x + 1) % width, y),
            Location((x - 1) % width, y),
            Location(x, (y + 1) % height),
            Location(x, (y - 1) % height),
        ]

    def _a_star(self, environment: 'Earth', start: Location, goal: Location,
                avoid_agents: bool = True) -> List[Location]:

        if start is None or goal is None:
            return []

        width = environment.get_width()
        height = environment.get_height()

        start_key = self._loc_key(start, width, height)
        goal_key = self._loc_key(goal, width, height)

        # Min-heap of (f, tie, PathNode) to avoid comparing PathNode directly
        open_heap: List[Tuple[float, int, PathNode]] = []
        counter = itertools.count()

        start_node = PathNode(f=0.0, g=0.0, h=self._heuristic(start, goal, width, height),
                              location=start, parent=None)
        heapq.heappush(open_heap, (start_node.f, next(counter), start_node))

        g_score: Dict[Tuple[int, int], float] = {start_key: 0.0}
        visited: set[Tuple[int, int]] = set()

        while open_heap:
            _, __, current = heapq.heappop(open_heap)
            cur_key = self._loc_key(current.location, width, height)
            if cur_key in visited:
                continue
            visited.add(cur_key)

            if cur_key == goal_key:
                # Reconstruct path (exclude the start location)
                path: List[Location] = []
                node = current
                while node.parent is not None:
                    path.append(node.location)
                    node = node.parent
                path.reverse()
                return path

            for nb in self._neighbors4(current.location, width, height):
                nb_key = self._loc_key(nb, width, height)
                if nb_key in visited:
                    continue

                # Treat occupied cells as blocked, unless it's the goal (soft rule)
                if avoid_agents and nb_key != goal_key:
                    occupant = environment.get_agent(nb)
                    if occupant is not None:
                        continue

                tentative_g = g_score[cur_key] + 1
                if tentative_g < g_score.get(nb_key, float('inf')):
                    h_val = self._heuristic(nb, goal, width, height)
                    f_val = tentative_g + h_val
                    g_score[nb_key] = tentative_g
                    node = PathNode(f=f_val, g=tentative_g, h=h_val, location=nb, parent=current)
                    heapq.heappush(open_heap, (f_val, next(counter), node))

        return []

    def move_along_path(self, environment: 'Earth', path: List[Location]) -> None:
        if not path or self.is_exhausted():
            return
        next_loc = path[0]
        # Remove from current position
        environment.set_agent(None, self.get_location())
        # Place at new position
        environment.set_agent(self, next_loc)
        self.set_location(next_loc)
        # consume energy
        self.consume_energy(self.move_cost)

    def repair_bridge(self, environment: 'Earth') -> None:
        bridge = environment.get_bridge(self.get_location())
        if bridge is not None and not bridge.is_destroyed and not bridge.is_complete and not self.is_exhausted():
            if self._energy >= self.repair_cost:
                self.consume_energy(self.repair_cost)
                bridge.repair(self)

    def share_energy(self, teammate: 'Hero', amount: int) -> None:
        amount = min(amount, self._energy)
        capacity = teammate.max_energy - teammate.energy
        transfer = min(amount, capacity)
        if transfer <= 0:
            return
        self._energy -= transfer
        teammate._energy += transfer

    def attack_surfer(self, surfer: 'SilverSurfer') -> None:
        pass

    def shield_location(self, environment: 'Earth', location: Location) -> None:
        pass

    def act(self, environment: 'Earth') -> None:

        if environment.is_hq(self.get_location()):
            self.recharge()

        if self.is_exhausted():
            if not environment.is_hq(self.get_location()):
                path = self._a_star(environment, self.get_location(), self.hq_location)
                if path:
                    self.move_along_path(environment, path)
            return

        bridge = environment.get_bridge(self.get_location())
        if bridge is not None and not bridge.is_complete and not bridge.is_destroyed:
            self.repair_bridge(environment)
            return

        target = self.find_nearest_incomplete_bridge(environment)
        if target is None:
            return

        path = self._a_star(environment, self.get_location(), target)
        if path:
            self.move_along_path(environment, path)


    def find_nearest_incomplete_bridge(self, environment: 'Earth') -> Optional[Location]:
        bridges = [(loc_key, br) for loc_key, br in environment._bridges.items()
                   if not br.is_complete and not br.is_destroyed]
        if not bridges:
            return None
        width, height = environment.get_width(), environment.get_height()
        best_loc = None
        best_dist = float('inf')
        sx, sy = self.get_location().get_x(), self.get_location().get_y()
        for (x, y), _ in bridges:
            dx = abs(sx - x)
            dy = abs(sy - y)
            dx = min(dx, width - dx)
            dy = min(dy, height - dy)
            dist = dx + dy
            if dist < best_dist:
                best_dist = dist
                best_loc = Location(x, y)
        return best_loc


class ReedRichards(Hero):

    def __init__(self, location: Location, hq_location: Location) -> None:
        super().__init__("Reed Richards", location, hq_location)

    def find_nearest_incomplete_bridge(self, environment: 'Earth') -> Optional[Location]:
        bridges = [(loc_key, br) for loc_key, br in environment._bridges.items()
                   if not br.is_complete and not br.is_destroyed]
        if not bridges:
            return None
        width, height = environment.get_width(), environment.get_height()
        best_score = -float('inf')
        best_loc = None

        galactus_pos: Optional[Location] = None
        try:
            from model.galactus import GalactusProjection  # local import to avoid cycle
            for row in range(height):
                for col in range(width):
                    agent = environment.get_agent(Location(col, row))
                    if isinstance(agent, GalactusProjection):
                        galactus_pos = agent.get_location()
                        raise StopIteration
        except StopIteration:
            pass

        sx, sy = self.get_location().get_x(), self.get_location().get_y()
        hx, hy = environment.hq_location.get_x(), environment.hq_location.get_y()

        for (x, y), _ in bridges:
            # To hero
            dx = abs(sx - x); dy = abs(sy - y)
            dx = min(dx, width - dx); dy = min(dy, height - dy)
            dist_to_hero = dx + dy

            hdx = abs(hx - x); hdy = abs(hy - y)
            hdx = min(hdx, width - hdx); hdy = min(hdy, height - hdy)
            dist_from_hq = hdx + hdy

            if galactus_pos is not None:
                gdx = abs(galactus_pos.get_x() - x); gdy = abs(galactus_pos.get_y() - y)
                gdx = min(gdx, width - gdx); gdy = min(gdy, height - gdy)
                dist_to_galactus = gdx + gdy
            else:
                dist_to_galactus = 0

            score = dist_from_hq - dist_to_galactus - dist_to_hero
            if score > best_score:
                best_score = score
                best_loc = Location(x, y)
        return best_loc

    def act(self, environment: 'Earth') -> None:
        super().act(environment)


class SueStorm(Hero):

    shield_duration_default: int = 3  # number of steps shield lasts

    def __init__(self, location: Location, hq_location: Location) -> None:
        super().__init__("Sue Storm", location, hq_location)

    def shield_location(self, environment: 'Earth', location: Location) -> None:
        if environment.shields is None:
            environment.shields = {}
        key = (location.get_x() % environment.get_width(),
               location.get_y() % environment.get_height())
        environment.shields[key] = self.shield_duration_default
        self.consume_energy(self.shield_cost)

    def act(self, environment: 'Earth') -> None:
        if environment.is_hq(self.get_location()):
            self.recharge()

        if self.is_exhausted():
            if not environment.is_hq(self.get_location()):
                path = self._a_star(environment, self.get_location(), self.hq_location)
                if path:
                    self.move_along_path(environment, path)
            return

        bridge = environment.get_bridge(self.get_location())
        key = (self.get_location().get_x() % environment.get_width(),
               self.get_location().get_y() % environment.get_height())
        if bridge and not bridge.is_complete and not bridge.is_destroyed \
           and environment.shields.get(key, 0) == 0 and self.energy >= self.shield_cost:
            self.shield_location(environment, self.get_location())
            return

        if bridge and not bridge.is_complete and not bridge.is_destroyed:
            self.repair_bridge(environment)
            return

        super().act(environment)


class JohnnyStorm(Hero):

    attack_range: int = 2
    attack_power: int = 20

    def __init__(self, location: Location, hq_location: Location) -> None:
        super().__init__("Johnny Storm", location, hq_location)

    def attack_surfer(self, surfer: 'SilverSurfer') -> None:
        if self.energy >= self.attack_cost:
            self.consume_energy(self.attack_cost)
            surfer.take_damage(self.attack_power)

    def find_surfer_in_range(self, environment: 'Earth') -> Optional['SilverSurfer']:
        try:
            from model.silver_surfer import SilverSurfer  # local import
            width = environment.get_width()
            height = environment.get_height()
            sx, sy = self.get_location().get_x(), self.get_location().get_y()
            for row in range(height):
                for col in range(width):
                    agent = environment.get_agent(Location(col, row))
                    if isinstance(agent, SilverSurfer):
                        dx = abs(sx - col); dy = abs(sy - row)
                        dx = min(dx, width - dx); dy = min(dy, height - dy)
                        if dx + dy <= self.attack_range:
                            return agent
            return None
        except Exception:
            return None

    def act(self, environment: 'Earth') -> None:
        if environment.is_hq(self.get_location()):
            self.recharge()

        if self.is_exhausted():
            if not environment.is_hq(self.get_location()):
                path = self._a_star(environment, self.get_location(), self.hq_location)
                if path:
                    self.move_along_path(environment, path)
            return

        surfer = self.find_surfer_in_range(environment)
        if surfer is not None:
            self.attack_surfer(surfer)
            return

        bridge = environment.get_bridge(self.get_location())
        if bridge and not bridge.is_complete and not bridge.is_destroyed:
            self.repair_bridge(environment)
            return

        super().act(environment)


class BenGrimm(Hero):

    def __init__(self, location: Location, hq_location: Location) -> None:
        super().__init__("Ben Grimm", location, hq_location)

    def repair_bridge(self, environment: 'Earth') -> None:
        bridge = environment.get_bridge(self.get_location())
        if bridge is not None and not bridge.is_destroyed and not bridge.is_complete and not self.is_exhausted():
            if self._energy >= self.repair_cost:
                self.consume_energy(self.repair_cost)
                bridge.repair(self)
                bridge.repair(self)

    def act(self, environment: 'Earth') -> None:
        if environment.is_hq(self.get_location()):
            self.recharge()

        if self.is_exhausted():
            if not environment.is_hq(self.get_location()):
                path = self._a_star(environment, self.get_location(), self.hq_location)
                if path:
                    self.move_along_path(environment, path)
            return

        bridge = environment.get_bridge(self.get_location())
        if bridge and not bridge.is_complete and not bridge.is_destroyed:
            self.repair_bridge(environment)
            return

        super().act(environment)