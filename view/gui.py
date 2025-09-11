from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, Optional

from controller.config import Config
from model.location import Location

if TYPE_CHECKING:
    from model.environment import Environment
    from controller.simulator import Simulator

DARK_BG = "#0b1220"
PANEL_BG = "#0f172a"
PANEL_ACCENT = "#172554"
TEXT_PRIMARY = "#e2e8f0"
TEXT_MUTED = "#94a3b8"
GRID_LINE = "#334155"
AGENT_OUTLINE = "#0ea5e9"
BRIDGE_COMPLETE = "#10b981"
BRIDGE_DAMAGED = "#f97316"
BRIDGE_BUILDING = "#facc15"
BACKGROUND_EMPTY = DARK_BG


class Gui(tk.Tk):
    def __init__(self, environment: Environment, agent_colours: dict, simulator: Optional['Simulator'] = None):
        super().__init__()
        self.__environment = environment
        self.__agent_colours = {None: BACKGROUND_EMPTY, **agent_colours}
        self.__legend_panel: Optional[tk.Frame] = None
        self.__closed = False
        self.simulator = simulator

        self.stats_labels: dict[str, tk.Label] = {}
        self.pause_button: Optional[tk.Button] = None
        self.reset_button: Optional[tk.Button] = None
        self.speed_scale: Optional[ttk.Scale] = None
        self.speed_value_label: Optional[ttk.Label] = None
        self.grid_container: Optional[ttk.Frame] = None
        self.world_canvas: Optional[tk.Canvas] = None

        self.__init_gui()
        self.__init_layout()

    def render(self) -> None:
        if self.simulator:
            self._update_stats()
        self.update_legends()

        if not self.world_canvas:
            return
        self.world_canvas.delete("all")

        W = self.__environment.get_width()
        H = self.__environment.get_height()
        cw = int(self.world_canvas.winfo_width() or 800)
        ch = int(self.world_canvas.winfo_height() or 800)
        size = min(cw, ch)
        cell = size / max(W, H)
        ox = (cw - size) / 2.0
        oy = (ch - size) / 2.0

        for i in range(W + 1):
            x = ox + i * cell
            self.world_canvas.create_line(x, oy, x, oy + H * cell, fill=GRID_LINE)
        for j in range(H + 1):
            y = oy + j * cell
            self.world_canvas.create_line(ox, y, ox + W * cell, y, fill=GRID_LINE)

        get_bridge = getattr(self.__environment, 'get_bridge', None)
        has_bridge_api = callable(get_bridge)

        for r in range(H):
            for c in range(W):
                loc = Location(c, r)
                bridge = get_bridge(loc) if has_bridge_api else None
                if bridge:
                    if bridge.is_complete():
                        bg = BRIDGE_COMPLETE
                    elif getattr(bridge, "damaged", False):
                        bg = BRIDGE_DAMAGED
                    else:
                        bg = BRIDGE_BUILDING
                else:
                    bg = BACKGROUND_EMPTY
                x0 = ox + c * cell
                y0 = oy + r * cell
                x1 = x0 + cell
                y1 = y0 + cell
                self.world_canvas.create_rectangle(x0, y0, x1, y1, fill=bg, outline=GRID_LINE)

        pad = max(2, int(cell * 0.25))
        for r in range(H):
            for c in range(W):
                agent = self.__environment.get_agent(Location(c, r))
                if not agent:
                    continue
                agent_cls = agent.__class__
                col = self.__agent_colours.get(agent_cls, "#38bdf8")
                x0 = ox + c * cell + pad
                y0 = oy + r * cell + pad
                x1 = ox + (c + 1) * cell - pad
                y1 = oy + (r + 1) * cell - pad
                w = x1 - x0
                h = y1 - y0
                cx = x0 + w / 2.0
                cy = y0 + h / 2.0
                if agent_cls.__name__ == "ReedRichards":
                    self.world_canvas.create_rectangle(x0, y0, x1, y1, fill=col, outline=AGENT_OUTLINE, width=1.0)
                elif agent_cls.__name__ == "SueStorm":
                    points = [(cx, y0), (x1, y1), (x0, y1)]
                    self.world_canvas.create_polygon(points, fill=col, outline=AGENT_OUTLINE)
                elif agent_cls.__name__ == "JohnnyStorm":
                    points = [(cx, y0), (x1, cy), (cx, y1), (x0, cy)]
                    self.world_canvas.create_polygon(points, fill=col, outline=AGENT_OUTLINE)
                elif agent_cls.__name__ == "BenGrimm":
                    points = [
                        (x0 + w * 0.25, y0), (x0 + w * 0.75, y0),
                        (x1, y0 + h * 0.5), (x0 + w * 0.75, y1),
                        (x0 + w * 0.25, y1), (x0, y0 + h * 0.5),
                    ]
                    self.world_canvas.create_polygon(points, fill=col, outline=AGENT_OUTLINE)
                elif agent_cls.__name__ == "SilverSurfer":
                    self.world_canvas.create_oval(x0, y0, x1, y1, fill=col, outline=AGENT_OUTLINE, width=1.0)
                elif agent_cls.__name__ == "GalactusProjection":
                    t = min(w, h) * 0.3
                    half_t = t / 2.0
                    points = [
                        (cx - half_t, y0), (cx + half_t, y0),
                        (cx + half_t, cy - half_t), (x1, cy - half_t),
                        (x1, cy + half_t), (cx + half_t, cy + half_t),
                        (cx + half_t, y1), (cx - half_t, y1),
                        (cx - half_t, cy + half_t), (x0, cy + half_t),
                        (x0, cy - half_t), (cx - half_t, cy - half_t)
                    ]
                    self.world_canvas.create_polygon(points, fill=col, outline=AGENT_OUTLINE)
                else:
                    self.world_canvas.create_oval(x0, y0, x1, y1, fill=col, outline=AGENT_OUTLINE, width=1.0)

        self.update_idletasks()

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.__closed = True
            self.destroy()

    def is_closed(self) -> bool:
        return self.__closed

    def toggle_pause(self) -> None:
        if not self.simulator:
            return
        self.simulator.paused = not self.simulator.paused
        self.pause_button.config(text="Resume" if self.simulator.paused else "Pause")

    def reset_simulation(self) -> None:
        if not self.simulator:
            return
        self.simulator.reset()
        if self.pause_button:
            self.pause_button.config(text="Pause")

    def on_speed_change(self, value: str) -> None:
        if not self.simulator:
            return
        try:
            v = float(value)
            self.simulator.simulation_speed = v
            if self.speed_value_label:
                self.speed_value_label.config(text=f"{v:.1f} steps/s")
        except ValueError:
            pass

    def _update_stats(self) -> None:
        sim = self.simulator
        if not sim:
            return
        self.stats_labels["Step"].config(text=f"Step: {sim.step_count}")
        total = len(sim.bridges)
        complete = sum(1 for b in sim.bridges if b.is_complete())
        damaged = sum(1 for b in sim.bridges if getattr(b, "damaged", False))
        self.stats_labels["Bridges"].config(text=f"Bridges: {complete}/{total} complete, {damaged} damaged")
        heroes_line = ", ".join(f"{h.name}:{h.energy}" for h in sim.heroes) or "none"
        self.stats_labels["Heroes"].config(text=f"Heroes: {heroes_line}")
        if sim.surfer:
            status = "retreating" if getattr(sim.surfer, "retreating", False) else "active"
            self.stats_labels["Surfer"].config(text=f"Surfer: {sim.surfer.energy} ({status})")
        else:
            self.stats_labels["Surfer"].config(text="Surfer: none")
        if sim.galactus:
            gx = sim.galactus.get_location().get_x()
            gy = sim.galactus.get_location().get_y()
            self.stats_labels["Galactus"].config(text=f"Galactus: at ({gx}, {gy})")
        else:
            self.stats_labels["Galactus"].config(text="Galactus: none")
        if sim.mission_failed:
            status_text = "Mission Failed"
            reason = sim.status_reason or "Environment signaled mission failure"
        elif sim.mission_completed:
            status_text = "Mission Completed"
            reason = sim.status_reason or "All objectives satisfied"
        else:
            status_text = "In Progress"
            reason = ""
        self.stats_labels["Status"].config(
            text=f"Status: {status_text}{(' — ' + reason) if reason else ''}"
        )