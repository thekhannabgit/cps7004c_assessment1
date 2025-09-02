from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from controller.config import Config
from model.environment import Environment
from model.location import Location
from model.bridge import Bridge

if TYPE_CHECKING:
    from model.agent import Agent


class Earth(Environment):

    def __init__(self) -> None:
        super().__init__()
        self._grid: List[List[Optional[Agent, None]]] = [
            [None for _ in range(self.get_width())] for _ in range(self.get_height())
        ]
        self._bridges: Dict[Tuple[int, int], Bridge] = {}
        self.hq_location: Optional[Location] = None
        self.franklin_location: Optional[Location] = None


        self.shields: Dict[Tuple[int, int], int] = {}


    def get_agent(self, location: Location) -> Optional[Agent, None]:
        if location is None:
            return None
        x = location.get_x() % self.get_width()
        y = location.get_y() % self.get_height()
        return self._grid[y][x]

    def set_agent(self, agent: Optional[Agent, None], location: Location) -> None:

        if location is None:
            return
        x = location.get_x() % self.get_width()
        y = location.get_y() % self.get_height()
        self._grid[y][x] = agent


    def get_bridge(self, location: Location) -> Optional[Bridge]:
        if location is None:
            return None
        key = (location.get_x() % self.get_width(), location.get_y() % self.get_height())
        return self._bridges.get(key)

    def set_bridge(self, bridge: Optional[Bridge], location: Location) -> None:

        key = (location.get_x() % self.get_width(), location.get_y() % self.get_height())
        if bridge is None:
            if key in self._bridges:
                del self._bridges[key]
        else:
            self._bridges[key] = bridge


    def clear(self) -> None:
        self._grid = [[None for _ in range(self.get_width())] for _ in range(self.get_height())]
        self._bridges.clear()
        self.hq_location = None
        self.franklin_location = None
        self.shields.clear()

    def get_adjacent_locations(self, location: Location) -> List[Location]:

        directions = [(-1, -1), (0, -1), (1, -1),
                      (-1, 0),          (1, 0),
                      (-1, 1),  (0, 1),  (1, 1)]
        result: List[Location] = []
        x = location.get_x()
        y = location.get_y()
        for dx, dy in directions:
            nx = (x + dx) % self.get_width()
            ny = (y + dy) % self.get_height()
            result.append(Location(nx, ny))
        return result

    def get_free_adjacent_locations(self, location: Location) -> List[Location]:

        result: List[Location] = []
        for adj in self.get_adjacent_locations(location):
            if self.get_agent(adj) is None:
                result.append(adj)
        return result

    def is_hq(self, location: Location) -> bool:
        return (self.hq_location is not None and
                location.get_x() % self.get_width() == self.hq_location.get_x() % self.get_width() and
                location.get_y() % self.get_height() == self.hq_location.get_y() % self.get_height())

    def is_franklin(self, location: Location) -> bool:
        return (self.franklin_location is not None and
                location.get_x() % self.get_width() == self.franklin_location.get_x() % self.get_width() and
                location.get_y() % self.get_height() == self.franklin_location.get_y() % self.get_height())


    def get_bridge_clusters(self) -> List[List[Bridge]]:

        clusters: List[List[Bridge]] = []
        visited: set[Tuple[int, int]] = set()
        for key, bridge in self._bridges.items():
            if key in visited or bridge.is_destroyed:
                continue
            cluster: List[Bridge] = []
            queue = [key]
            visited.add(key)
            while queue:
                cx, cy = queue.pop()
                curr_bridge = self._bridges.get((cx, cy))
                if curr_bridge is None or curr_bridge.is_destroyed:
                    continue
                cluster.append(curr_bridge)
                # check neighbours
                for dx, dy in [(-1, -1), (0, -1), (1, -1),
                               (-1, 0),          (1, 0),
                               (-1, 1),  (0, 1),  (1, 1)]:
                    nx = (cx + dx) % self.get_width()
                    ny = (cy + dy) % self.get_height()
                    key2 = (nx, ny)
                    if key2 in visited:
                        continue
                    if key2 in self._bridges and not self._bridges[key2].is_destroyed:
                        queue.append(key2)
                        visited.add(key2)
            clusters.append(cluster)
        return clusters
