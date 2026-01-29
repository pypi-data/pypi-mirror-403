"""Screen region capture tool for Third Eye MCP."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from third_eye_mcp.services.ads import get_ad
from third_eye_mcp.services.screenshot import ScreenshotService
from third_eye_mcp.services.storage import StorageService
from third_eye_mcp.types import CaptureMetadata, StoredCapture


def capture_region(
    x: int,
    y: int,
    width: int,
    height: int,
    max_width: Optional[int] = 1920,
    delay: Optional[float] = 0,
    instant: Optional[bool] = False,
) -> Dict[str, Any]:
    """
    Capture a specific region of the screen.

    Args:
        x: X coordinate of the region
        y: Y coordinate of the region
        width: Width of the region
        height: Height of the region
        max_width: Maximum width for resizing (default 1920)
        delay: Delay in seconds before capture (default 0)
        instant: Skip delay if True (default False)

    Returns:
        Dictionary with base64 image and metadata including sponsored ad.
    """
    service = ScreenshotService()
    storage = StorageService()

    # Get sponsored message for watermark
    sponsored = get_ad()

    image_base64, final_width, final_height = service.capture_region(
        x=x,
        y=y,
        width=width,
        height=height,
        max_width=max_width,
        delay=delay or 0,
        instant=instant or False,
        watermark=sponsored,
    )

    metadata = CaptureMetadata(
        width=final_width,
        height=final_height,
        display_index=None,
        timestamp=datetime.now(timezone.utc).isoformat(),
        sponsored=sponsored,
    )

    # Store for later retrieval
    storage.store(
        StoredCapture(
            image_base64=image_base64,
            metadata=metadata,
        )
    )

    return {
        "image": image_base64,
        "metadata": {
            "width": metadata.width,
            "height": metadata.height,
            "displayIndex": metadata.display_index,
            "timestamp": metadata.timestamp,
            "sponsored": metadata.sponsored,
        },
    }
