"""
Macro Event Abstract Syntax Tree (AST) & Event Definitions (v2.0.0 Enterprise)
Provides comprehensive event models for hardware inputs, visual frame synchronization,
CSV variable templating, and biological human kinematics.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import json
from typing import Optional


class EventType(str, Enum):
    # Mouse Events
    MOUSE_CLICK = "mouse_click"
    MOUSE_MOVE = "mouse_move"
    MOUSE_DOWN = "mouse_down"
    MOUSE_UP = "mouse_up"
    MOUSE_DRAG = "mouse_drag"
    MOUSE_SCROLL = "mouse_scroll"

    # Keyboard Events
    KEY_PRESS = "key_press"
    KEY_DOWN = "key_down"
    KEY_UP = "key_up"
    TEXT_TYPE = "text_type"

    # Time & Flow
    DELAY = "delay"

    # Visual State & Image Anchors (Zero-AI CV)
    VISUAL_ANCHOR_CLICK = "visual_anchor_click"
    WAIT_UNTIL_FRAME_APPEARS = "wait_until_frame_appears"
    WAIT_UNTIL_FRAME_DISAPPEARS = "wait_until_frame_disappears"

    # Human Stealth & Organic Kinematics
    HUMAN_WANDER_ZONE = "human_wander_zone"
    HUMAN_WANDER_SLOW = "human_wander_slow"
    HUMAN_SCROLL_PEEK = "human_scroll_peek"

    # Triggers & Legacy
    PIXEL_CHECK = "pixel_check"


class ErrorPolicy(str, Enum):
    STOP = "stop"
    SKIP = "skip"
    RETRY_3 = "retry_3"


@dataclass
class MacroEvent:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    event_type: EventType = EventType.MOUSE_CLICK
    enabled: bool = True
    delay_after_ms: float = 50.0  # Pause after executing this action
    error_policy: ErrorPolicy = ErrorPolicy.STOP
    comment: str = ""

    # Mouse Parameters
    x: int = 0
    y: int = 0
    end_x: int = 0  # For drag
    end_y: int = 0  # For drag
    button: str = "left"  # left, right, middle
    click_count: int = 1
    scroll_dy: int = 0
    scroll_dx: int = 0
    curve_type: str = "windmouse"  # windmouse, bezier, linear, instant
    duration_ms: float = 240.0

    # Keyboard Parameters
    key_name: str = ""
    vk_code: int = 0
    scan_code: int = 0
    text: str = ""  # For text_type (supports {{variable}} CSV interpolation)
    wpm: int = 80
    auto_clear_first: bool = False  # React/Vue SPA auto-clear (Ctrl+A -> Backspace)

    # Delay Parameters
    delay_ms: float = 500.0
    jitter_ms: float = 0.0

    # Visual Frame & Image Anchor Parameters (Zero-AI CV)
    template_name: str = ""
    template_base64: str = ""  # Embedded portable PNG base64
    confidence_threshold: float = 0.85  # 0.70 to 0.99
    timeout_ms: float = 8000.0
    search_roi: Optional[list[int]] = None  # [x, y, w, h] or None for fullscreen
    click_offset_x: int = 0
    click_offset_y: int = 0

    # Humanizer & Biological Parameters
    human_target_radius: int = 0  # 2D Gaussian click dispersion radius
    zone_radius: int = 40
    wander_speed_profile: str = "slow"  # slow, natural, brisk
    return_to_origin: bool = True
    peek_duration_ms: float = 1200.0

    # Pixel Check Trigger
    target_hex_color: str = "#FFFFFF"
    color_tolerance: int = 10

    def to_dict(self) -> dict:
        d = asdict(self)
        d["event_type"] = self.event_type.value
        d["error_policy"] = self.error_policy.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "MacroEvent":
        data_copy = dict(data)
        if "event_type" in data_copy:
            data_copy["event_type"] = EventType(data_copy["event_type"])
        if "error_policy" in data_copy:
            data_copy["error_policy"] = ErrorPolicy(data_copy["error_policy"])
        return cls(**data_copy)

    def get_summary(self) -> str:
        t = self.event_type
        if t == EventType.MOUSE_CLICK:
            btn = self.button.capitalize()
            cnt = "Double " if self.click_count == 2 else ""
            txt = f"{cnt}{btn} Click at ({self.x}, {self.y})"
            if self.human_target_radius > 0:
                txt += f" [Zone R={self.human_target_radius}]"
            return txt
        elif t == EventType.MOUSE_MOVE:
            return f"Move to ({self.x}, {self.y}) via {self.curve_type.capitalize()} ({int(self.duration_ms)}ms)"
        elif t == EventType.MOUSE_DRAG:
            return f"Drag from ({self.x}, {self.y}) to ({self.end_x}, {self.end_y})"
        elif t == EventType.MOUSE_SCROLL:
            return f"Scroll vertical {self.scroll_dy} notches (dx={self.scroll_dx})"
        elif t == EventType.KEY_PRESS:
            return f"Press key '{self.key_name}'"
        elif t == EventType.TEXT_TYPE:
            preview = (self.text[:28] + "...") if len(self.text) > 28 else self.text
            return f"Type \"{preview}\" ({self.wpm} WPM)"
        elif t == EventType.DELAY:
            j = f" ±{int(self.jitter_ms)}ms" if self.jitter_ms > 0 else ""
            return f"Wait {int(self.delay_ms)}ms{j}"
        elif t == EventType.VISUAL_ANCHOR_CLICK:
            name = self.template_name or "Image Snippet"
            return f"Auto-Click Anchor '{name}' (Confidence: {int(self.confidence_threshold*100)}%)"
        elif t == EventType.WAIT_UNTIL_FRAME_APPEARS:
            name = self.template_name or "Visual Frame"
            return f"Wait for Frame '{name}' to appear (Timeout: {int(self.timeout_ms/1000)}s)"
        elif t == EventType.WAIT_UNTIL_FRAME_DISAPPEARS:
            name = self.template_name or "Loading Spinner"
            return f"Wait for Frame '{name}' to vanish (Timeout: {int(self.timeout_ms/1000)}s)"
        elif t == EventType.HUMAN_WANDER_ZONE:
            return f"Human Zone Hover (R={self.zone_radius}px, {int(self.duration_ms)}ms)"
        elif t == EventType.HUMAN_WANDER_SLOW:
            return f"Slow Organic Meander (Profile: {self.wander_speed_profile.capitalize()}, {int(self.duration_ms)}ms)"
        elif t == EventType.HUMAN_SCROLL_PEEK:
            return f"Human Scroll Peek ({self.scroll_dy} notches, {int(self.peek_duration_ms)}ms glance)"
        elif t == EventType.PIXEL_CHECK:
            return f"Check Pixel at ({self.x}, {self.y}) == {self.target_hex_color}"
        return f"{self.event_type.value}"

    def get_category_icon(self) -> str:
        t = self.event_type
        if t in (EventType.MOUSE_CLICK, EventType.MOUSE_MOVE, EventType.MOUSE_DOWN, EventType.MOUSE_UP, EventType.MOUSE_DRAG, EventType.MOUSE_SCROLL):
            return "🖱️"
        elif t in (EventType.KEY_PRESS, EventType.KEY_DOWN, EventType.KEY_UP, EventType.TEXT_TYPE):
            return "⌨️"
        elif t == EventType.DELAY:
            return "⏱️"
        elif t in (EventType.VISUAL_ANCHOR_CLICK, EventType.WAIT_UNTIL_FRAME_APPEARS, EventType.WAIT_UNTIL_FRAME_DISAPPEARS):
            return "📸"
        elif t in (EventType.HUMAN_WANDER_ZONE, EventType.HUMAN_WANDER_SLOW, EventType.HUMAN_SCROLL_PEEK):
            return "🌿"
        return "⚡"
