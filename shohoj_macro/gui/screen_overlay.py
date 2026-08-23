"""
Zone Sniper Screen Overlay: 8x Magnifier Loupe, Crosshairs & Visual Circle Drawer
Allows visual selection of points, tolerance circles with Gaussian scatter preview, and pixel sampling.
"""

import tkinter as tk
import math
import random
from PIL import ImageGrab, ImageTk, Image
from typing import Callable, Optional
from shohoj_macro.utils.color_utils import rgb_to_hex


class ScreenOverlaySniper(tk.Toplevel):
    """Fullscreen transparent sniper overlay."""

    def __init__(
        self,
        master,
        mode: str = "circle",  # "point", "circle", "color", "box"
        on_selection_complete: Callable[[dict], None] = None,
    ):
        super().__init__(master)
        self.mode = mode
        self.on_selection_complete = on_selection_complete

        # Fullscreen frameless window
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.85)

        self.screen_w = self.winfo_screenwidth()
        self.screen_h = self.winfo_screenheight()
        self.geometry(f"{self.screen_w}x{self.screen_h}+0+0")

        self.canvas = tk.Canvas(
            self,
            width=self.screen_w,
            height=self.screen_h,
            bg="#08090C",
            cursor="crosshair",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        # Drag state
        self.start_x = 0
        self.start_y = 0
        self.current_x = 0
        self.current_y = 0
        self.is_dragging = False

        # Key & Mouse bindings
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<ButtonPress-3>", lambda e: self.destroy())  # Right click cancel
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.canvas.bind("<Motion>", self._on_mouse_move)

        # Draw instructions banner
        self.canvas.create_text(
            self.screen_w // 2,
            35,
            text=f"🎯 Zone Sniper ({self.mode.upper()} MODE) • Click & Drag to Select • [Esc / Right-Click to Cancel]",
            fill="#00F0FF",
            font=("Segoe UI", 12, "bold"),
            tags="banner",
        )

    def _on_mouse_move(self, event):
        self.current_x = event.x
        self.current_y = event.y
        if not self.is_dragging:
            self._draw_loupe(event.x, event.y)

    def _draw_loupe(self, x: int, y: int):
        self.canvas.delete("loupe")

        # Capture 20x20 area around cursor for 8x zoom
        try:
            bbox = (max(0, x - 10), max(0, y - 10), min(self.screen_w, x + 10), min(self.screen_h, y + 10))
            img = ImageGrab.grab(bbox=bbox)
            zoomed = img.resize((120, 120), Image.NEAREST)
            self._loupe_img = ImageTk.PhotoImage(zoomed)
            center_rgb = img.getpixel((img.width // 2, img.height // 2))[:3]
            hex_color = rgb_to_hex(center_rgb[0], center_rgb[1], center_rgb[2])
        except Exception:
            self._loupe_img = None
            center_rgb = (255, 255, 255)
            hex_color = "#FFFFFF"

        # Loupe position (offset from cursor)
        lx = x + 25 if x + 180 < self.screen_w else x - 165
        ly = y + 25 if y + 180 < self.screen_h else y - 165

        # Background card
        self.canvas.create_rectangle(lx - 4, ly - 4, lx + 124, ly + 160, fill="#12141D", outline="#2E344D", width=1.5, tags="loupe")

        if self._loupe_img:
            self.canvas.create_image(lx, ly, anchor="nw", image=self._loupe_img, tags="loupe")

        # Crosshair inside loupe
        mid_x = lx + 60
        mid_y = ly + 60
        self.canvas.create_line(mid_x - 10, mid_y, mid_x + 10, mid_y, fill="#FF453A", width=1, tags="loupe")
        self.canvas.create_line(mid_x, mid_y - 10, mid_x, mid_y + 10, fill="#FF453A", width=1, tags="loupe")

        # Coordinate & Color info
        self.canvas.create_text(
            lx + 60,
            ly + 132,
            text=f"({x}, {y})",
            fill="#FFFFFF",
            font=("Segoe UI", 9, "bold"),
            tags="loupe",
        )
        self.canvas.create_text(
            lx + 60,
            ly + 148,
            text=f"{hex_color} RGB{center_rgb}",
            fill=hex_color if hex_color != "#000000" else "#00F0FF",
            font=("Segoe UI", 8),
            tags="loupe",
        )

    def _on_mouse_down(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.is_dragging = True
        self.canvas.delete("loupe")

    def _on_mouse_drag(self, event):
        if not self.is_dragging:
            return
        self.current_x = event.x
        self.current_y = event.y
        self.canvas.delete("shape")
        self.canvas.delete("dots")

        dx = self.current_x - self.start_x
        dy = self.current_y - self.start_y
        radius = int(math.hypot(dx, dy))

        if self.mode == "circle":
            # Draw circle
            self.canvas.create_oval(
                self.start_x - radius,
                self.start_y - radius,
                self.start_x + radius,
                self.start_y + radius,
                outline="#BF5AF2",
                fill="rgba(191, 90, 242, 0.15)",
                width=2,
                tags="shape",
            )
            # Center dot
            self.canvas.create_oval(self.start_x - 3, self.start_y - 3, self.start_x + 3, self.start_y + 3, fill="#00F0FF", tags="shape")
            # Live simulated Gaussian scatter dots
            sigma = radius / 3.0 if radius > 0 else 1
            for _ in range(18):
                gx = random.gauss(0, sigma)
                gy = random.gauss(0, sigma)
                if math.hypot(gx, gy) <= radius:
                    px = self.start_x + gx
                    py = self.start_y + gy
                    self.canvas.create_oval(px - 1.5, py - 1.5, px + 1.5, py + 1.5, fill="#30D158", outline="", tags="dots")

            self.canvas.create_text(
                self.start_x,
                self.start_y - radius - 16,
                text=f"Center: ({self.start_x}, {self.start_y}) • Radius: {radius}px",
                fill="#FFFFFF",
                font=("Segoe UI", 10, "bold"),
                tags="shape",
            )

        elif self.mode == "box":
            self.canvas.create_rectangle(
                self.start_x,
                self.start_y,
                self.current_x,
                self.current_y,
                outline="#00F0FF",
                width=2,
                tags="shape",
            )

    def _on_mouse_up(self, event):
        self.is_dragging = False
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        radius = int(math.hypot(dx, dy))

        # Sample pixel at start
        try:
            im = ImageGrab.grab(bbox=(self.start_x, self.start_y, self.start_x + 1, self.start_y + 1))
            rgb = im.getpixel((0, 0))[:3]
            hex_c = rgb_to_hex(rgb[0], rgb[1], rgb[2])
        except Exception:
            hex_c = "#FFFFFF"

        result = {
            "mode": self.mode,
            "x": self.start_x,
            "y": self.start_y,
            "end_x": event.x,
            "end_y": event.y,
            "radius": radius if radius > 0 else 0,
            "hex_color": hex_c,
        }

        if self.on_selection_complete:
            self.on_selection_complete(result)

        self.destroy()
