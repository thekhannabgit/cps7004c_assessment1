from __future__ import annotations

import random
from typing import TYPE_CHECKING

from model.agent import Agent

if TYPE_CHECKING:
    from model.location import Location
    from model.mars import Mars


class Rover(Agent):
    """
    Represents a rover agent in the simulation.

    Attributes:
        __space_craft_location: The location of the spacecraft the rover is assigned to.
    """

    def __init__(self, location: Location, space_craft_location: Location):
        """
        Initialize the Rover object with its location and assigned spacecraft location.

        Args:
            location (Location): The initial location of the rover.
            space_craft_location (Location): The location of the spacecraft the rover is assigned to.
        """
        super().__init__(location)
        self.__space_craft_location = space_craft_location

    def act(self, mars: Mars) -> None:
        pass
