"""
Interactive Freeze-Frame Screen Snipper Tool (Zero-AI Image Anchor Creator)
Allows users to drag a bounding box around any screen element to crop and embed template snippets.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Callable, Optional
import cv2
import numpy as np
from PIL import Image, ImageTk
from shohoj_macro.utils.win32_capture import capture_screen_bgr, get_virtual_screen_geometry
from shohoj_macro.core.cv_engine import CVTemplateMatcher
from shohoj_macro.gui.glass_theme import GlassTheme


class ScreenSnipperModal(tk.Toplevel):
    """Full-screen freeze capture overlay for snipping image templates."""

    def __init__(self, master, on_snip_completed: Callable[[str, str, float, int, int], None]):
        super().__init__(master)
        self.on_snip_completed = on_snip_completed

        # Capture desktop snapshot
        self.screen_bgr, self.v_left, self.v_top = capture_screen_bgr()
        self.v_left, self.v_top, self.v_w, self.v_h = get_virtual_screen_geometry()

        # Window setup: frameless, topmost, fullscreen
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.geometry(f"{self.v_w}x{self.v_h}+{self.v_left}+{self.v_top}")
        self.config(cursor="cross")

        self.start_x = None
        self.start_y = None
        self.current_rect = None

        # Build Canvas with Dimmed Screenshot
        self._build_canvas()

        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_canvas(self):
        self.canvas = tk.Canvas(self, cursor="cross", bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Convert BGR to RGB and dim slightly (opacity 75%)
        screen_rgb = cv2.cvtColor(self.screen_bgr, cv2.COLOR_BGR2RGB)
        dimmed = (screen_rgb.astype(np.float32) * 0.70).astype(np.uint8)

        self.bg_image_pil = Image.fromarray(dimmed)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image_pil)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        # Instruction HUD in center top
        self.canvas.create_rectangle(
            (self.v_w // 2) - 220, 20, (self.v_w // 2) + 220, 60,
            fill="#101320", outline="#00F0FF", width=1.5
        )
        self.canvas.create_text(
            self.v_w // 2, 40,
            text="📸 Drag a rectangle around target button/element • Press Esc to cancel",
            fill="#FFFFFF", font=("Segoe UI", 11, "bold")
        )

    def _on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="#00F0FF", width=2, fill=""
        )

    def _on_drag(self, event):
        if self.start_x is not None and self.start_y is not None:
            self.canvas.coords(self.current_rect, self.start_x, self.start_y, event.x, event.y)

    def _on_release(self, event):
        if self.start_x is None or self.start_y is None:
            return

        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)

        w = x2 - x1
        h = y2 - y1

        if w < 6 or h < 6:
            self.destroy()
            return

        # Crop from original un-dimmed screen_bgr
        cropped_bgr = self.screen_bgr[y1:y2, x1:x2].copy()
        base64_str = CVTemplateMatcher.encode_image_to_base64(cropped_bgr)
        center_x = self.v_left + x1 + (w // 2)
        center_y = self.v_top + y1 + (h // 2)

        self.withdraw()
        # Open Configure & Save Modal
        SnippetConfigModal(self.master, cropped_bgr, base64_str, center_x, center_y, self.on_snip_completed)
        self.destroy()


class SnippetConfigModal(ctk.CTkToplevel):
    """Modal dialog to preview snipped template and configure anchor settings."""

    def __init__(
        self,
        master,
        cropped_bgr: np.ndarray,
        base64_str: str,
        center_x: int,
        center_y: int,
        on_save: Callable[[str, str, float, int, int], None],
    ):
        super().__init__(master)
        self.cropped_bgr = cropped_bgr
        self.base64_str = base64_str
        self.center_x = center_x
        self.center_y = center_y
        self.on_save = on_save

        self.title("📸 Configure Visual Anchor")
        self.geometry("380x360")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self._build_ui()

    def _build_ui(self):
        pad_frame = ctk.CTkFrame(self, fg_color="transparent")
        pad_frame.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            pad_frame,
            text="🎯 Visual Anchor Template",
            font=ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=14, weight="bold"),
            text_color=GlassTheme.ACCENT_CYAN,
        ).pack(anchor="w", pady=(0, 10))

        # Preview Frame
        preview_card = ctk.CTkFrame(pad_frame, fg_color="#10121A", height=100, corner_radius=8)
        preview_card.pack(fill="x", pady=(0, 12))

        # Convert to PIL for Tkinter preview
        h, w = self.cropped_bgr.shape[:2]
        scale = min(1.0, 80.0 / max(h, 1), 260.0 / max(w, 1))
        disp_w, disp_h = max(1, int(w * scale)), max(1, int(h * scale))

        rgb_crop = cv2.cvtColor(self.cropped_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb_crop, (disp_w, disp_h), interpolation=cv2.INTER_AREA)
        pil_img = Image.fromarray(resized)
        self.photo = ImageTk.PhotoImage(pil_img)

        lbl_img = tk.Label(preview_card, image=self.photo, bg="#10121A")
        lbl_img.pack(pady=10)

        # Template Name Input
        ctk.CTkLabel(pad_frame, text="Anchor Name:", font=ctk.CTkFont(size=11), text_color=GlassTheme.TEXT_SECONDARY).pack(anchor="w")
        self.ent_name = ctk.CTkEntry(pad_frame, placeholder_text="e.g. submit_button, login_icon", height=30)
        self.ent_name.insert(0, f"Button_{w}x{h}")
        self.ent_name.pack(fill="x", pady=(2, 10))

        # Confidence Slider
        conf_box = ctk.CTkFrame(pad_frame, fg_color="transparent")
        conf_box.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(conf_box, text="Match Confidence:", font=ctk.CTkFont(size=11), text_color=GlassTheme.TEXT_SECONDARY).pack(side="left")
        self.lbl_conf = ctk.CTkLabel(conf_box, text="85%", font=ctk.CTkFont(size=11, weight="bold"), text_color=GlassTheme.ACCENT_CYAN)
        self.lbl_conf.pack(side="right")

        self.conf_slider = ctk.CTkSlider(pad_frame, from_=0.70, to=0.98, number_of_steps=28, command=self._on_conf_change)
        self.conf_slider.set(0.85)
        self.conf_slider.pack(fill="x", pady=(0, 14))

        # Action Buttons
        btn_box = ctk.CTkFrame(pad_frame, fg_color="transparent")
        btn_box.pack(fill="x")

        ctk.CTkButton(
            btn_box, text="Cancel", width=80, fg_color=GlassTheme.CARD_BG_SECONDARY, hover_color="#333A4D", command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            btn_box,
            text="💾 Save Anchor",
            fg_color=GlassTheme.ACCENT_BLUE,
            hover_color=GlassTheme.ACCENT_CYAN,
            font=ctk.CTkFont(weight="bold"),
            command=self._on_save_click,
        ).pack(side="right")

    def _on_conf_change(self, val):
        self.lbl_conf.configure(text=f"{int(val*100)}%")

    def _on_save_click(self):
        name = self.ent_name.get().strip() or "Visual_Anchor"
        conf = float(self.conf_slider.get())
        if self.on_save:
            self.on_save(name, self.base64_str, conf, self.center_x, self.center_y)
        self.destroy()
