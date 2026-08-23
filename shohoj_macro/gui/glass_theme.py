"""
Apple-Style Glassmorphic Theme Tokens & Custom Widget Styles
Provides simulated frosted acrylic dark palette with glowing accents.
"""

import customtkinter as ctk

# Color Palette (Liquid Obsidian & Apple Vibrant Accents)
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

    # Fonts
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
            corner_radius=kwargs.pop("corner_radius", 10),
            fg_color=kwargs.pop("fg_color", accent),
            hover_color=kwargs.pop("hover_color", GlassTheme.CARD_BG_SECONDARY),
            font=kwargs.pop("font", ctk.CTkFont(family=GlassTheme.FONT_FAMILY, size=12, weight="bold")),
            height=kwargs.pop("height", 32),
            **kwargs
        )
