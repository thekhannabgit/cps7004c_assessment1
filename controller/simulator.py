import random
from model.location import Location
from model.mars import Mars
from model.bridge import Bridge
from model.hero import ReedRichards, SueStorm, JohnnyStorm, BenGrimm
from model.silver_surfer import SilverSurfer
from model.galactus import GalactusProjection
from view.gui import Gui


class Simulator:

    def __init__(self) -> None:
        self._after_id = None

        self.step_count = 0
        self.mars = Mars()

        self.mission_failed = False
        self.mission_completed = False
        self.status_reason: str = ""

        self.heroes: list = []
        self.surfer: SilverSurfer | None = None
        self.galactus: GalactusProjection | None = None

        self.bridges: list[Bridge] = []

        self._generate_initial_world()

        self.is_running = False
        self.paused = False

        self.simulation_speed = 5.0

        self.agent_colours = {
            ReedRichards:        "#60a5fa",  # blue-400
            SueStorm:            "#22d3ee",  # cyan-400
            JohnnyStorm:         "#fbbf24",  # amber-400
            BenGrimm:            "#f59e0b",  # amber-500
            SilverSurfer:        "#d1d5db",  # gray-300
            GalactusProjection:  "#a78bfa",  # violet-400
            None:                "#0b1220",  # board bg
        }

        self.gui = Gui(self.mars, self.agent_colours, simulator=self)
        self.gui.render()


    def _generate_initial_world(self) -> None:
        width  = self.mars.get_width()
        height = self.mars.get_height()

        centre_x = width // 2
        centre_y = height // 2

        hero_offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        hero_classes = [ReedRichards, SueStorm, JohnnyStorm, BenGrimm]
        for (dx, dy), cls in zip(hero_offsets, hero_classes):
            hx = (centre_x + dx) % width
            hy = (centre_y + dy) % height
            loc = Location(hx, hy)
            hero = cls(loc)
            self.heroes.append(hero)
            self.mars.set_agent(hero, loc)


        self.bridges.clear()
        forbidden = {(centre_x, centre_y)} | { (h.get_location().get_x(), h.get_location().get_y()) for h in self.heroes }
        target_sites = 7  # ↑ from 5
        while len(self.bridges) < target_sites:
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            if (x, y) in forbidden:
                continue
            loc = Location(x, y)
            if self.mars.get_agent(loc) is None:
                br = Bridge(loc)
                self.bridges.append(br)
                self.mars.add_bridge(br)


        self.franklin_location = Location(0, 0)
        self.surfer_spawn_step = 15
        self.galactus_spawn_step = 30


    def run(self) -> None:
        self.is_running = True
        self.paused = False
        self.schedule_next_step()

    def schedule_next_step(self) -> None:

        delay_ms = max(1, int(1000 / max(0.1, self.simulation_speed)))
        if not self.gui.is_closed() and self.is_running:
            self._after_id = self.gui.after(delay_ms, self._tick)

    def _tick(self) -> None:
        if self.gui.is_closed() or not self.is_running:
            return

        if self.paused:
            self.schedule_next_step()
            return

        self.step_count += 1
        self._update()
        self.gui.render()

        if self.mission_failed or self.mission_completed:
            self.is_running = False
            return
        self.schedule_next_step()


    def _update(self) -> None:
        # Spawn Silver Surfer
        if self.surfer is None and self.step_count >= self.surfer_spawn_step:
            while True:
                x = random.randint(0, self.mars.get_width() - 1)
                y = random.randint(0, self.mars.get_height() - 1)
                loc = Location(x, y)
                if self.mars.get_agent(loc) is None:
                    self.surfer = SilverSurfer(loc)
                    self.mars.set_agent(self.surfer, loc)
                    break

        # Spawn Galactus
        if self.galactus is None and self.step_count >= self.galactus_spawn_step:
            loc = Location(self.mars.get_width() - 1, self.mars.get_height() - 1)
            self.galactus = GalactusProjection(loc, self.franklin_location)
            self.mars.set_agent(self.galactus, loc)

        for hero in list(self.heroes):
            hero.act(self.mars)

        width  = self.mars.get_width()
        height = self.mars.get_height()
        for a in self.heroes:
            for b in self.heroes:
                if a is b:
                    continue
                dx = abs(a.get_location().get_x() - b.get_location().get_x())
                dy = abs(a.get_location().get_y() - b.get_location().get_y())
                dx = min(dx, width - dx)
                dy = min(dy, height - dy)
                if dx + dy == 1 and a.energy - b.energy >= 20 and a.energy > 20 and b.energy < b.max_energy:
                    give = min(10, a.energy - b.energy)
                    a.energy -= give
                    b.energy = min(b.max_energy, b.energy + give)

        # Surfer & Galactus act
        if self.surfer:
            self.surfer.act(self.mars)
        if self.galactus:
            self.galactus.act(self.mars)

        #all bridges complete & undamaged
        if not self.mission_failed:
            if self.bridges and all((not br.damaged) and br.is_complete() for br in self.bridges):
                self.mission_completed = True
                self.status_reason = "All bridges complete and undamaged"


        if not self.mission_completed and hasattr(self.mars, "mission_failed") and self.mars.mission_failed:
            if self.galactus and self._is_at(self.galactus.get_location(), self.franklin_location):
                self.status_reason = "Galactus reached Franklin"
            else:
                self.status_reason = "Environment signaled mission failure"
            self.mission_failed = True

    @staticmethod
    def _is_at(a: Location, b: Location) -> bool:
        return a.get_x() == b.get_x() and a.get_y() == b.get_y()

    # ------------------------------------------------------------------ reset

    def reset(self) -> None:

        if getattr(self, "_after_id", None):
            try:
                self.gui.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

        self.mars.clear()
        if hasattr(self.mars, "mission_failed"):
            self.mars.mission_failed = False

        self.step_count = 0
        self.mission_failed = False
        self.mission_completed = False
        self.status_reason = ""

        self.heroes.clear()
        self.bridges.clear()
        self.surfer = None
        self.galactus = None

        random.seed()

        self._generate_initial_world()
        self.is_running = True
        self.paused = False
        self.gui.render()
        self.schedule_next_step()


if __name__ == "__main__":
    sim = Simulator()
    sim.run()
    sim.gui.mainloop()
