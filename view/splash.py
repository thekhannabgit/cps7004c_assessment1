from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk

def show_splash(image_path: str | None = None, duration_ms: int = 2000) -> None:
    root = tk.Tk()
    root.overrideredirect(True)
    bg_colour = "#0b1220"
    root.configure(bg=bg_colour)

    width = 520
    height = 320
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    pos_x = int((screen_w - width) / 2)
    pos_y = int((screen_h - height) / 2)
    root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    frame = ttk.Frame(root)
    frame.pack(expand=True, fill="both")
    title = ttk.Label(frame, text="Fantastic Four — Earth Defence",
                      font=("", 16, "bold"), foreground="#e2e8f0", background=bg_colour)
    title.pack(pady=(20, 10))

    canvas_w = width - 40
    canvas_h = height - 100
    canvas = tk.Canvas(frame, width=canvas_w, height=canvas_h,
                       highlightthickness=0, bg=bg_colour)
    canvas.pack()

    loaded = False
    if image_path and os.path.exists(image_path):
        try:
            img = tk.PhotoImage(file=image_path)
            canvas.create_image(canvas_w // 2, canvas_h // 2, image=img)
            canvas.image = img
            loaded = True
        except Exception:
            loaded = False

    if not loaded:
        pad = 10
        canvas.create_rectangle(0, 0, canvas_w, canvas_h, outline="#172554", fill="#0f172a")
        canvas.create_text(canvas_w // 2, canvas_h // 2,
                           text="Preparing simulation...", fill="#94a3b8",
                           font=("", 12))

    root.after(duration_ms, root.destroy)
    root.mainloop()