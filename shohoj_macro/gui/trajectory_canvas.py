"""
Live Trajectory, Bézier Curve & Click Heatmap Visualizer Canvas
Renders the macro mouse travel path, smoothing curves, and target zones in a mini canvas.
"""

import tkinter as tk
import customtkinter as ctk
from shohoj_macro.gui.glass_theme import GlassTheme
from shohoj_macro.core.events import MacroEvent, EventType


class TrajectoryCanvas(ctk.CTkFrame):
    """Visualizer canvas displaying mouse path and target zones."""

    def __init__(self, master, width: int = 280, height: int = 180, **kwargs):
        super().__init__(
            master,
            width=width,
            height=height,
            fg_color=GlassTheme.CARD_BG,
            border_color=GlassTheme.CARD_BORDER,
            border_width=1,
            corner_radius=12,
            **kwargs,
        )
        self.canvas_width = width
        self.canvas_height = height

        self.canvas = tk.Canvas(
            self,
            width=width - 8,
            height=height - 8,
            bg=GlassTheme.BG_DARK,
            highlightthickness=0,
        )
        self.canvas.pack(padx=4, pady=4, fill="both", expand=True)

        # Draw grid background
        self._draw_grid()

    def _draw_grid(self):
        self.canvas.delete("grid")
        w = self.canvas.winfo_reqwidth()
        h = self.canvas.winfo_reqheight()
        grid_color = "#161822"
        for x in range(0, w, 20):
            self.canvas.create_line(x, 0, x, h, fill=grid_color, tags="grid")
        for y in range(0, h, 20):
            self.canvas.create_line(0, y, w, y, fill=grid_color, tags="grid")

    def update_trajectory(self, events: list[MacroEvent], current_step_idx: int = -1):
        """Redraws the trajectory path from the macro events."""
        self.canvas.delete("path")
        self.canvas.delete("zone")
        self.canvas.delete("point")

        if not events:
            return

        # Find bounding box of all mouse coordinates
        coords = []
        for ev in events:
            if ev.event_type in (EventType.MOUSE_MOVE, EventType.MOUSE_CLICK, EventType.MOUSE_DOWN, EventType.MOUSE_DRAG, EventType.HUMAN_WANDER_ZONE):
                coords.append((ev.x, ev.y))
            if ev.event_type == EventType.MOUSE_DRAG:
                coords.append((ev.end_x, ev.end_y))

        if not coords:
            return

        min_x = min(c[0] for c in coords)
        max_x = max(c[0] for c in coords)
        min_y = min(c[1] for c in coords)
        max_y = max(c[1] for c in coords)

        span_x = max(100, max_x - min_x)
        span_y = max(100, max_y - min_y)

        pad = 20
        c_w = max(50, self.canvas_width - pad * 2)
        c_h = max(50, self.canvas_height - pad * 2)

        def transform(x, y):
            tx = pad + ((x - min_x) / span_x) * c_w
            ty = pad + ((y - min_y) / span_y) * c_h
            return tx, ty

        # Draw lines connecting path
        prev_pt = None
        for i, ev in enumerate(events):
            if ev.event_type in (EventType.MOUSE_MOVE, EventType.MOUSE_CLICK, EventType.MOUSE_DRAG):
                cur_pt = transform(ev.x, ev.y)
                if prev_pt:
                    line_color = GlassTheme.ACCENT_CYAN if ev.curve_type != "linear" else "#4A5568"
                    self.canvas.create_line(prev_pt[0], prev_pt[1], cur_pt[0], cur_pt[1], fill=line_color, width=1.5, smooth=True, tags="path")
                prev_pt = cur_pt

                # Draw point or zone
                if ev.event_type == EventType.MOUSE_CLICK:
                    pt_color = GlassTheme.ACCENT_EMERALD if i == current_step_idx else GlassTheme.ACCENT_BLUE
                    r = 4
                    self.canvas.create_oval(cur_pt[0] - r, cur_pt[1] - r, cur_pt[0] + r, cur_pt[1] + r, fill=pt_color, outline="#FFFFFF", width=1, tags="point")

                    if ev.human_target_radius > 0:
                        # Draw tolerance radius
                        scale_r = (ev.human_target_radius / span_x) * c_w
                        self.canvas.create_oval(cur_pt[0] - scale_r, cur_pt[1] - scale_r, cur_pt[0] + scale_r, cur_pt[1] + scale_r, outline=GlassTheme.ACCENT_PURPLE, width=1, dash=(3, 3), tags="zone")

            elif ev.event_type == EventType.HUMAN_WANDER_ZONE:
                cur_pt = transform(ev.x, ev.y)
                scale_r = max(6, (ev.zone_radius / span_x) * c_w)
                self.canvas.create_oval(cur_pt[0] - scale_r, cur_pt[1] - scale_r, cur_pt[0] + scale_r, cur_pt[1] + scale_r, outline=GlassTheme.ACCENT_PURPLE, fill="#2D124D", width=1, tags="zone")
