"""
Zero-AI High-Speed Computer Vision Engine (OpenCV Template Matching)
Executes deterministic sub-millisecond visual frame detection, auto-adjusting image anchors,
and multi-scale pyramid matching with Base64 embedded serialization.
"""

import base64
import time
import math
from dataclasses import dataclass
from typing import Optional, Callable
import cv2
import numpy as np
from shohoj_macro.utils.win32_capture import capture_screen_bgr
from shohoj_macro.utils.timer import hires_sleep


@dataclass
class VisualMatchResult:
    found: bool
    confidence: float
    x: int  # Screen coordinate of top-left match
    y: int
    width: int
    height: int
    center_x: int  # Screen coordinate of match center
    center_y: int
    scale_matched: float = 1.0


class CVTemplateMatcher:
    """Zero-AI high-speed visual state engine."""

    @staticmethod
    def encode_image_to_base64(img_bgr: np.ndarray) -> str:
        """Encodes an OpenCV BGR image into a portable PNG base64 string."""
        success, buf = cv2.imencode(".png", img_bgr)
        if not success:
            raise ValueError("Failed to encode image to PNG format")
        return base64.b64encode(buf).decode("utf-8")

    @staticmethod
    def decode_base64_to_image(b64_str: str) -> np.ndarray:
        """Decodes a portable PNG base64 string back into an OpenCV BGR array."""
        raw_bytes = base64.b64decode(b64_str.encode("utf-8"))
        np_arr = np.frombuffer(raw_bytes, dtype=np.uint8)
        img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise ValueError("Failed to decode base64 string to image")
        return img_bgr

    @classmethod
    def match_template(
        cls,
        template_bgr: np.ndarray,
        search_roi: Optional[tuple[int, int, int, int]] = None,
        confidence_threshold: float = 0.85,
        multi_scale: bool = True,
    ) -> VisualMatchResult:
        """
        Searches the screen (or ROI sub-region) for the given template.
        Executes in < 2ms using normalized cross-correlation (TM_CCOEFF_NORMED).
        """
        # 1. Fast screen grab via Win32 GDI
        screen_bgr, origin_x, origin_y = capture_screen_bgr(search_roi)
        if screen_bgr.shape[0] < template_bgr.shape[0] or screen_bgr.shape[1] < template_bgr.shape[1]:
            return VisualMatchResult(found=False, confidence=0.0, x=0, y=0, width=0, height=0, center_x=0, center_y=0)

        # 2. Convert to Grayscale for illumination invariance
        gray_screen = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
        gray_template = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)

        th, tw = gray_template.shape[:2]
        best_val = -1.0
        best_loc = (0, 0)
        best_scale = 1.0
        best_w, best_h = tw, th

        # Scales to evaluate (standard 1.0x first, then pyramid if below threshold)
        scales = [1.0]
        if multi_scale:
            scales = [1.0, 0.9, 1.1, 1.25, 0.8]

        for s in scales:
            if s == 1.0:
                scaled_tmpl = gray_template
                curr_w, curr_h = tw, th
            else:
                curr_w = int(tw * s)
                curr_h = int(th * s)
                if curr_w <= 4 or curr_h <= 4 or curr_w > gray_screen.shape[1] or curr_h > gray_screen.shape[0]:
                    continue
                scaled_tmpl = cv2.resize(gray_template, (curr_w, curr_h), interpolation=cv2.INTER_AREA if s < 1.0 else cv2.INTER_CUBIC)

            res = cv2.matchTemplate(gray_screen, scaled_tmpl, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

            if max_val > best_val:
                best_val = max_val
                best_loc = max_loc
                best_scale = s
                best_w = curr_w
                best_h = curr_h

            if best_val >= confidence_threshold:
                break  # Early exit on high confidence match

        found = best_val >= confidence_threshold
        match_x = origin_x + best_loc[0]
        match_y = origin_y + best_loc[1]
        center_x = match_x + (best_w // 2)
        center_y = match_y + (best_h // 2)

        return VisualMatchResult(
            found=found,
            confidence=float(best_val),
            x=match_x,
            y=match_y,
            width=best_w,
            height=best_h,
            center_x=center_x,
            center_y=center_y,
            scale_matched=best_scale,
        )

    @classmethod
    def wait_for_frame_state(
        cls,
        template_bgr: np.ndarray,
        should_exist: bool = True,
        search_roi: Optional[tuple[int, int, int, int]] = None,
        confidence_threshold: float = 0.85,
        timeout_sec: float = 10.0,
        poll_interval_sec: float = 0.15,
        cancel_check_fn: Optional[Callable[[], bool]] = None,
    ) -> VisualMatchResult:
        """
        Polls screen until the frame appears (should_exist=True) or disappears (should_exist=False).
        Throttled polling prevents CPU spikes.
        """
        start_time = time.perf_counter()
        last_result = VisualMatchResult(found=False, confidence=0.0, x=0, y=0, width=0, height=0, center_x=0, center_y=0)

        while time.perf_counter() - start_time < timeout_sec:
            if cancel_check_fn and cancel_check_fn():
                break

            last_result = cls.match_template(
                template_bgr,
                search_roi=search_roi,
                confidence_threshold=confidence_threshold,
                multi_scale=True,
            )

            if should_exist and last_result.found:
                return last_result
            elif not should_exist and not last_result.found:
                return last_result

            hires_sleep(poll_interval_sec)

        return last_result
