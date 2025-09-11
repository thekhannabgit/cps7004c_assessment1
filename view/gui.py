from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, Optional

from controller.config import Config
from model.location import Location

if TYPE_CHECKING:
    from model.environment import Environment
    from controller.simulator import Simulator

DARK_BG          = "#0b1220"  # deep navy for board
PANEL_BG         = "#0f172a"  # slate-900-like
PANEL_ACCENT     = "#172554"  # dark indigo
TEXT_PRIMARY     = "#e2e8f0"  # slate-200
TEXT_MUTED       = "#94a3b8"  # slate-400

GRID_LINE        = "#334155"  # slate-700 visible on dark
AGENT_OUTLINE    = "#0ea5e9"  # sky-500 outline

# Bridge status colours (requested)
BRIDGE_COMPLETE  = "#10b981"  # green-500
BRIDGE_DAMAGED   = "#f97316"  # orange-500
BRIDGE_BUILDING  = "#facc15"  # amber-400
BACKGROUND_EMPTY = DARK_BG     # board background


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

        # centre the square
        ox = (cw - size) / 2.0
        oy = (ch - size) / 2.0

        # grid lines
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

        # for agents draw different shapes per class
        pad = max(2, int(cell * 0.25))  # margin => shapes do not fill entire cell
        for r in range(H):
            for c in range(W):
                agent = self.__environment.get_agent(Location(c, r))
                if not agent:
                    continue
                agent_cls = agent.__class__
                col = self.__agent_colours.get(agent_cls, "#38bdf8")  # fallback colour
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
                    points = [
                        (cx, y0),
                        (x1, y1),
                        (x0, y1),
                    ]
                    self.world_canvas.create_polygon(points, fill=col, outline=AGENT_OUTLINE)
                elif agent_cls.__name__ == "JohnnyStorm":
                    points = [
                        (cx, y0),
                        (x1, cy),
                        (cx, y1),
                        (x0, cy),
                    ]
                    self.world_canvas.create_polygon(points, fill=col, outline=AGENT_OUTLINE)
                elif agent_cls.__name__ == "BenGrimm":
                    points = [
                        (x0 + w * 0.25, y0),
                        (x0 + w * 0.75, y0),
                        (x1, y0 + h * 0.5),
                        (x0 + w * 0.75, y1),
                        (x0 + w * 0.25, y1),
                        (x0, y0 + h * 0.5),
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

    def __init_gui(self):
        self.title(Config.simulation_name)
        self.configure(bg=PANEL_BG)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        try:
            style = ttk.Style(self)
            style.theme_use("clam")
            style.configure("Dark.TFrame", background=PANEL_BG)
            style.configure("Dark.TLabel", background=PANEL_BG, foreground=TEXT_PRIMARY)
            style.configure("Muted.TLabel", background=PANEL_BG, foreground=TEXT_MUTED)
            style.configure("Dark.TButton", padding=(10, 6), font=("", 10, "bold"))
            style.map("Dark.TButton",
                      foreground=[("active", TEXT_PRIMARY)],
                      background=[("active", "#1f2937")])  # slate-800 on hover
        except Exception:
            pass

        # start maximized
        try:
            self.state("zoomed")             # Windows
        except Exception:
            try:
                self.attributes("-zoomed", True)  # X11
            except Exception:
                self.minsize(1000, 780)

        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def __init_layout(self) -> None:
        top = ttk.Frame(self, style="Dark.TFrame", padding=(12, 10))
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)
        top.columnconfigure(1, weight=0)

        stats = ttk.Frame(top, style="Dark.TFrame")
        stats.grid(row=0, column=0, sticky="w", padx=(0, 12))
        title = ttk.Label(stats, text="Mission Telemetry", style="Dark.TLabel", font=("", 12, "bold"))
        title.pack(anchor="w", pady=(0, 6))
        for key in ["Step", "Bridges", "Heroes", "Surfer", "Galactus", "Status"]:
            lbl = ttk.Label(stats, text=f"{key}: ?", style="Dark.TLabel", font=("", 10))
            lbl.pack(anchor="w", pady=1)
            self.stats_labels[key] = lbl

        controls = ttk.Frame(top, style="Dark.TFrame")
        controls.grid(row=0, column=1, sticky="e")
        self.pause_button = ttk.Button(controls, text="Pause", style="Dark.TButton", command=self.toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=4)
        self.reset_button = ttk.Button(controls, text="Reset", style="Dark.TButton", command=self.reset_simulation)
        self.reset_button.pack(side=tk.LEFT, padx=4)

        ttk.Label(controls, text="Speed", style="Dark.TLabel").pack(side=tk.LEFT, padx=(10, 4))
        self.speed_scale = ttk.Scale(
            controls, from_=1.0, to=20.0, orient=tk.HORIZONTAL,
            command=self.on_speed_change, length=220
        )
        self.speed_scale.set(self.simulator.simulation_speed if self.simulator else 5.0)
        self.speed_scale.pack(side=tk.LEFT, padx=(0, 4))
        self.speed_value_label = ttk.Label(controls,
                                           text=f"{self.speed_scale.get():.1f} steps/s",
                                           style="Muted.TLabel")
        self.speed_value_label.pack(side=tk.LEFT)

        legend_frame = ttk.Frame(self, style="Dark.TFrame", padding=(12, 6))
        legend_frame.grid(row=1, column=0, sticky="ew")
        ttk.Label(legend_frame, text="Bridge status:", style="Dark.TLabel", font=("", 10, "bold")).pack(side=tk.LEFT, padx=(0, 8))

        def swatch(parent, colour, text):
            c = tk.Canvas(parent, width=16, height=16, highlightthickness=0, bg=PANEL_BG, bd=0)
            c.create_rectangle(0, 0, 16, 16, fill=colour, outline="#0f172a")
            c.pack(side=tk.LEFT)
            ttk.Label(parent, text=text, style="Muted.TLabel").pack(side=tk.LEFT, padx=(4, 12))

        swatch(legend_frame, BRIDGE_BUILDING, "Yellow = being built")
        swatch(legend_frame, BRIDGE_DAMAGED,  "Orange = damaged")
        swatch(legend_frame, BRIDGE_COMPLETE, "Green = complete")

        self.legend_panel = ttk.Frame(self, style="Dark.TFrame", padding=(12, 0))
        self.legend_panel.grid(row=2, column=0, sticky="ew")

        divider = tk.Frame(self, height=1, bg=PANEL_ACCENT, bd=0)
        divider.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 0))

        self.grid_container = ttk.Frame(self, style="Dark.TFrame")
        self.grid_container.grid(row=4, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.grid_container.rowconfigure(0, weight=1)
        self.grid_container.columnconfigure(0, weight=1)

        self.world_canvas = tk.Canvas(self.grid_container, highlightthickness=0, bg=DARK_BG, bd=0)
        self.world_canvas.grid(row=0, column=0, sticky="nsew")

        def _resize(_e):
            if not self.world_canvas:
                return
            w = self.grid_container.winfo_width()
            h = self.grid_container.winfo_height()
            size = min(w, h)
            self.world_canvas.config(width=size, height=size)
            self.render()

        self.grid_container.bind("<Configure>", _resize)

    def update_legends(self):
        counts = {}
        for r in range(self.__environment.get_height()):
            for c in range(self.__environment.get_width()):
                a = self.__environment.get_agent(Location(c, r))
                if a:
                    cls = a.__class__
                    counts[cls] = counts.get(cls, 0) + 1

        for w in self.legend_panel.winfo_children():
            w.destroy()

        if counts:
            ttk.Label(self.legend_panel, text="Agents:", style="Dark.TLabel", font=("", 10, "bold")).pack(side=tk.LEFT, padx=(0, 8))

        for cls, count in sorted(counts.items(), key=lambda x: x[0].__name__):
            colour = self.__agent_colours.get(cls, "#38bdf8")
            c = tk.Canvas(self.legend_panel, width=16, height=16, highlightthickness=0, bg=PANEL_BG, bd=0)
            c.create_rectangle(0, 0, 16, 16, fill=colour, outline=PANEL_ACCENT)
            c.pack(side=tk.LEFT)
            ttk.Label(self.legend_panel, text=f"{cls.__name__} ({count})", style="Muted.TLabel").pack(side=tk.LEFT, padx=(4, 12))

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
            self.simulator.simulation_speed = v  # steps per second; right=faster
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

        # Status + reason
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
