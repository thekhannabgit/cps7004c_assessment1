from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.location import Location


class Bridge:

    def __init__(self, location: Location, max_health: int = 100) -> None:
        self.location = location
        self.max_health = max_health
        self.health = 0
        self.damaged = False

    def is_complete(self) -> bool:
        return self.health >= self.max_health

    def damage(self, amount: int = 10) -> None:

        self.damaged = True
        self.health = max(0, self.health - amount)

    def repair(self, amount: int = 10) -> None:

        self.health = min(self.max_health, self.health + amount)
        if self.health >= self.max_health:
            self.damaged = False

    def __repr__(self) -> str:
        status = "complete" if self.is_complete() else "damaged" if self.damaged else "incomplete"
        return f"Bridge(loc={self.location}, health={self.health}/{self.max_health}, {status})"