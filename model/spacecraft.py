from __future__ import annotations

from typing import List, TYPE_CHECKING

from model.agent import Agent
from model.rover import Rover

if TYPE_CHECKING:
    from model.location import Location
    from model.mars import Mars


class Spacecraft(Agent):

    def __init__(self, location: Location):
        super().__init__(location)

    def act(self, mars: Mars) -> None:
        pass
