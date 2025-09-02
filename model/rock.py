from __future__ import annotations

from typing import TYPE_CHECKING

from model.agent import Agent
from model.environment import Environment

if TYPE_CHECKING:
    from model.location import Location


class Rock(Agent):

    def __init__(self, location: Location) -> None:
        super().__init__(location)

    def act(self, environment: Environment) -> None:
        pass
