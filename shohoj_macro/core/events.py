"""
Macro Event AST Schema, Data Models & Serialization
Defines all granular action representations for Shohoj Macro.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import json
from typing import Optional, Any


class EventType(str, Enum):
    MOUSE_MOVE = "MOUSE_MOVE"
    MOUSE_CLICK = "MOUSE_CLICK"
    MOUSE_DOWN = "MOUSE_DOWN"
    MOUSE_UP = "MOUSE_UP"
    MOUSE_DRAG = "MOUSE_DRAG"
    MOUSE_SCROLL = "MOUSE_SCROLL"
    KEY_PRESS = "KEY_PRESS"
    KEY_DOWN = "KEY_DOWN"
    KEY_UP = "KEY_UP"
    TEXT_TYPE = "TEXT_TYPE"
    DELAY = "DELAY"
    HUMAN_WANDER_ZONE = "HUMAN_WANDER_ZONE"
    HUMAN_SCROLL_PEEK = "HUMAN_SCROLL_PEEK"
    PIXEL_CHECK = "PIXEL_CHECK"
    BLOCK_LOOP = "BLOCK_LOOP"
    BROWSER_ELEMENT = "BROWSER_ELEMENT"


class ErrorPolicy(str, Enum):
    STOP = "STOP"
    SKIP = "SKIP"
    RETRY_3 = "RETRY_3"


@dataclass
class MacroEvent:
    """Base Macro Event model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    event_type: EventType = EventType.DELAY
    enabled: bool = True
    delay_after_ms: float = 50.0
    comment: str = ""
    error_policy: ErrorPolicy = ErrorPolicy.STOP
    # Specific fields
    x: int = 0
    y: int = 0
    end_x: int = 0
    end_y: int = 0
    button: str = "left"  # left, right, middle, double
    click_count: int = 1
    duration_ms: float = 250.0
    curve_type: str = "windmouse"  # instant, linear, bezier, windmouse
    human_target_radius: int = 0  # 0 = exact pixel, >0 = random Gaussian circle
    scroll_dy: int = 0
    scroll_dx: int = 0
    key_name: str = ""
    vk_code: int = 0
    scan_code: int = 0
    text: str = ""
    wpm: int = 75
    delay_ms: float = 100.0
    jitter_ms: float = 0.0
    # Humanizer specific
    zone_radius: int = 40
    return_to_origin: bool = True
    peek_duration_ms: float = 1200.0
    # Pixel check / Conditional trigger
    target_hex_color: str = "#FFFFFF"
    color_tolerance: int = 15
    on_match_action: str = "CONTINUE"  # CONTINUE, SKIP_NEXT, JUMP_TO
    on_mismatch_action: str = "WAIT_OR_FAIL"
    timeout_ms: float = 3000.0
    # Block loop
    loop_count: int = 1
    child_event_ids: list[str] = field(default_factory=list)
    # Browser Element target
    css_selector: str = ""
    element_description: str = ""
    # Window context
    window_title_filter: str = ""
    is_window_relative: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["error_policy"] = self.error_policy.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MacroEvent":
        d = dict(data)
        if "event_type" in d:
            d["event_type"] = EventType(d["event_type"])
        if "error_policy" in d:
            d["error_policy"] = ErrorPolicy(d["error_policy"])
        return cls(**d)

    def get_summary(self) -> str:
        """Returns a concise human-readable description for UI timeline."""
        t = self.event_type
        if t == EventType.MOUSE_MOVE:
            return f"Move to ({self.x}, {self.y}) via {self.curve_type.capitalize()}"
        elif t == EventType.MOUSE_CLICK:
            rad_str = f" ±{self.human_target_radius}px" if self.human_target_radius > 0 else ""
            cnt_str = "Double " if self.click_count == 2 else ""
            return f"{cnt_str}{self.button.capitalize()} Click at ({self.x}, {self.y}){rad_str}"
        elif t == EventType.MOUSE_DOWN:
            return f"{self.button.capitalize()} Down at ({self.x}, {self.y})"
        elif t == EventType.MOUSE_UP:
            return f"{self.button.capitalize()} Up at ({self.x}, {self.y})"
        elif t == EventType.MOUSE_DRAG:
            return f"Drag from ({self.x}, {self.y}) to ({self.end_x}, {self.end_y})"
        elif t == EventType.MOUSE_SCROLL:
            return f"Scroll vertical {self.scroll_dy} notches (dx={self.scroll_dx})"
        elif t == EventType.KEY_PRESS:
            return f"Press Key: {self.key_name or f'VK_{self.vk_code}'}"
        elif t == EventType.KEY_DOWN:
            return f"Key Down: {self.key_name or f'VK_{self.vk_code}'}"
        elif t == EventType.KEY_UP:
            return f"Key Up: {self.key_name or f'VK_{self.vk_code}'}"
        elif t == EventType.TEXT_TYPE:
            preview = self.text if len(self.text) <= 25 else self.text[:22] + "..."
            return f'Type: "{preview}" ({self.wpm} WPM)'
        elif t == EventType.DELAY:
            jit = f" ±{self.jitter_ms}ms" if self.jitter_ms > 0 else ""
            return f"Wait {self.delay_ms:.0f}ms{jit}"
        elif t == EventType.HUMAN_WANDER_ZONE:
            return f"Human Wander around ({self.x}, {self.y}) R={self.zone_radius}px ({self.duration_ms:.0f}ms)"
        elif t == EventType.HUMAN_SCROLL_PEEK:
            return f"Human Scroll Peek {self.scroll_dy} notches for {self.peek_duration_ms:.0f}ms (Net Zero)"
        elif t == EventType.PIXEL_CHECK:
            return f"Check Pixel ({self.x}, {self.y}) == {self.target_hex_color}"
        elif t == EventType.BLOCK_LOOP:
            return f"Loop Block ({self.loop_count} times, {len(self.child_event_ids)} actions)"
        elif t == EventType.BROWSER_ELEMENT:
            return f"Click Web Element: {self.css_selector or self.element_description}"
        return f"{self.event_type.value}"

    def get_category_icon(self) -> str:
        """Returns visual indicator icon."""
        t = self.event_type
        if t in (EventType.MOUSE_MOVE, EventType.MOUSE_DRAG):
            return "🧭"
        elif t in (EventType.MOUSE_CLICK, EventType.MOUSE_DOWN, EventType.MOUSE_UP):
            return "🖱️"
        elif t == EventType.MOUSE_SCROLL:
            return "📜"
        elif t in (EventType.KEY_PRESS, EventType.KEY_DOWN, EventType.KEY_UP, EventType.TEXT_TYPE):
            return "⌨️"
        elif t == EventType.DELAY:
            return "⏳"
        elif t in (EventType.HUMAN_WANDER_ZONE, EventType.HUMAN_SCROLL_PEEK):
            return "🧠"
        elif t == EventType.PIXEL_CHECK:
            return "🔍"
        elif t == EventType.BROWSER_ELEMENT:
            return "🌐"
        elif t == EventType.BLOCK_LOOP:
            return "🔁"
        return "⚡"
