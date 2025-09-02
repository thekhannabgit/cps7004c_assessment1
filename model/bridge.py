from __future__ import annotations

from typing import TYPE_CHECKING

from model.location import Location

if TYPE_CHECKING:
    from model.hero import Hero  # pragma: no cover - circular import hint


class Bridge:

    required_progress: int = 5

    def __init__(self, location: Location) -> None:
        self._location = location
        self._progress: int = 0
        self._destroyed: bool = False

    @property
    def location(self) -> Location:
        return self._location

    @property
    def progress(self) -> int:
        return self._progress

    @property
    def is_destroyed(self) -> bool:
        return self._destroyed

    @property
    def is_complete(self) -> bool:
        return self._progress >= self.required_progress and not self._destroyed

    def repair(self, hero: "Hero") -> None:
        if self._destroyed:
            return

        if self._progress < self.required_progress:
            self._progress += 1
            if self._progress > self.required_progress:
                self._progress = self.required_progress

    def damage(self, amount: int = 1) -> None:

        if self._destroyed:
            return
        self._progress -= amount
        if self._progress < 0:
            self._progress = 0

    def destroy(self) -> None:
        
        self._destroyed = True
        self._progress = 0

    def __repr__(self) -> str:
        return (f"Bridge(location={self._location}, progress="
                f"{self._progress}/{self.required_progress}, "
                f"destroyed={self._destroyed})")
