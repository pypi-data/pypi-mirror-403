"""Screenshot service using mss."""

import base64
import io
import time
from typing import List, Optional, Tuple

import mss
import mss.tools
from PIL import Image

from third_eye_mcp.types import DisplayInfo
from third_eye_mcp.services.watermark import add_watermark


class ScreenshotService:
    """Service for capturing screenshots using mss."""

    def __init__(self) -> None:
        """Initialize the screenshot service."""
        self._sct = mss.mss()

    def list_displays(self) -> List[DisplayInfo]:
        """List all available displays."""
        displays = []
        monitors = self._sct.monitors

        # monitors[0] is the "all monitors" virtual screen, skip it
        for i, mon in enumerate(monitors[1:], start=0):
            displays.append(
                DisplayInfo(
                    index=i,
                    name=f"Display {i + 1}",
                    x=mon["left"],
                    y=mon["top"],
                    width=mon["width"],
                    height=mon["height"],
                    is_primary=(i == 0),
                )
            )
        return displays

    def capture_display(
        self,
        display_index: int = 0,
        max_width: Optional[int] = 1920,
        delay: float = 0,
        instant: bool = False,
        watermark: Optional[str] = None,
    ) -> Tuple[str, int, int]:
        """
        Capture a full display.

        Args:
            display_index: Index of the display to capture (0-based)
            max_width: Maximum width for resizing (None to skip resizing)
            delay: Delay in seconds before capture
            instant: If True, skip the delay
            watermark: Optional text to add as watermark

        Returns:
            Tuple of (base64_image, width, height)
        """
        if not instant and delay > 0:
            time.sleep(delay)

        monitors = self._sct.monitors
        # monitors[0] is all monitors combined, so display_index + 1
        if display_index + 1 >= len(monitors):
            raise ValueError(f"Display index {display_index} not found. Available: 0-{len(monitors) - 2}")

        monitor = monitors[display_index + 1]
        screenshot = self._sct.grab(monitor)

        return self._process_screenshot(screenshot, max_width, watermark)

    def capture_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        max_width: Optional[int] = 1920,
        delay: float = 0,
        instant: bool = False,
        watermark: Optional[str] = None,
    ) -> Tuple[str, int, int]:
        """
        Capture a specific region of the screen.

        Args:
            x: X coordinate of the region
            y: Y coordinate of the region
            width: Width of the region
            height: Height of the region
            max_width: Maximum width for resizing (None to skip resizing)
            delay: Delay in seconds before capture
            instant: If True, skip the delay
            watermark: Optional text to add as watermark

        Returns:
            Tuple of (base64_image, width, height)
        """
        if not instant and delay > 0:
            time.sleep(delay)

        region = {"left": x, "top": y, "width": width, "height": height}
        screenshot = self._sct.grab(region)

        return self._process_screenshot(screenshot, max_width, watermark)

    def _process_screenshot(
        self,
        screenshot: mss.base.ScreenShot,
        max_width: Optional[int],
        watermark: Optional[str] = None,
    ) -> Tuple[str, int, int]:
        """Process a screenshot: resize if needed, add watermark, and convert to base64 PNG."""
        # Convert to PIL Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

        # Resize if needed
        if max_width and img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        # Add watermark if provided
        if watermark:
            img = add_watermark(img, watermark)

        # Convert to base64 PNG
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return base64_image, img.width, img.height

    def close(self) -> None:
        """Close the mss instance."""
        self._sct.close()
