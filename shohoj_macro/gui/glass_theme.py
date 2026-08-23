"""
Apple-Style Glassmorphic Theme Tokens, Custom Widgets & GlassTooltip
"""

import tkinter as tk
import customtkinter as ctk

class GlassTheme:
    BG_DARK = "#0B0C10"           # Deep space backdrop
    SURFACE_BASE = "#12141D"      # Window canvas base
    CARD_BG = "#1A1D2B"           # Primary frosted card
    CARD_BG_SECONDARY = "#222638" # Secondary card / hover
    CARD_BORDER = "#2E344D"       # Subtle 1px glass border
    CARD_BORDER_GLOW = "#3D4466"  # Highlighted card border
    
    # Text Hierarchy
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#949CB0"
    TEXT_MUTED = "#5E667E"
    
    # Vibrant Accents
    ACCENT_CYAN = "#00F0FF"       # Cyber Cyan
    ACCENT_BLUE = "#0A84FF"       # Apple System Blue
    ACCENT_EMERALD = "#30D158"    # Apple Green (Active / Record)
    ACCENT_ORANGE = "#FF9F0A"     # Apple Orange (Warning / Delay)
    ACCENT_RED = "#FF453A"        # Apple Red (Stop / Error / Delete)
    ACCENT_PURPLE = "#BF5AF2"     # Apple Purple (Humanizer / Zone)

    FONT_FAMILY = "Segoe UI Variable Display" if True else "Segoe UI"
    
    @classmethod
    def apply_global_settings(cls):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")


class GlassCard(ctk.CTkFrame):
    """Frosted glass card with rounded corners and subtle border."""
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=kwargs.pop("fg_color", GlassTheme.CARD_BG),
            border_color=kwargs.pop("border_color", GlassTheme.CARD_BORDER),
            border_width=kwargs.pop("border_width", 1),
            corner_radius=kwargs.pop("corner_radius", 14),
            **kwargs
        )


class GlassButton(ctk.CTkButton):
    """Pill-shaped modern glass action button."""
    def __init__(self, master, **kwargs):
        accent = kwargs.pop("accent_color", GlassTheme.ACCENT_BLUE)
        super().__init__(
            master,
            corner_radius=kwargs.pop("corner_radius", 8),
            fg_color=kwargs.pop("fg_color", accent),
            hover_color=kwargs.pop("hover_color", GlassTheme.CARD_BG_SECONDARY),
            font=kwargs.pop("font", ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=11, weight="bold")),
            height=kwargs.pop("height", 30),
            **kwargs
        )


class GlassTooltip:
    """Lightweight modern hover tooltip for buttons and widgets."""
    def __init__(self, widget, text: str, delay_ms: int = 400):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self.tip_window = None
        self._after_id = None

        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
        self.widget.bind("<ButtonPress>", self._on_leave)

    def _on_enter(self, event=None):
        self._schedule()

    def _on_leave(self, event=None):
        self._cancel()
        self._hide()

    def _schedule(self):
        self._cancel()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel(self):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self):
        if self.tip_window or not self.text:
            return

        x = self.widget.winfo_rootx() + (self.widget.winfo_width() // 2)
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)
        tw.config(bg="#010204")
        tw.wm_attributes("-transparentcolor", "#010204")

        frame = tk.Frame(tw, bg="#161928", highlightbackground="#00F0FF", highlightthickness=1, bd=0)
        frame.pack(padx=1, pady=1)

        lbl = tk.Label(
            frame,
            text=self.text,
            justify="left",
            background="#161928",
            foreground="#FFFFFF",
            font=("Segoe UI", 9),
            padx=8,
            pady=4,
        )
        lbl.pack()

        tw.wm_geometry(f"+{x - 30}+{y}")

    def _hide(self):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
