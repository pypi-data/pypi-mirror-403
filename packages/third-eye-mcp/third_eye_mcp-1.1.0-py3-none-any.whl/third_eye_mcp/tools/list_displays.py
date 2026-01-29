"""List displays tool for Third Eye MCP."""

from typing import Any, Dict, List

from third_eye_mcp.services.screenshot import ScreenshotService


def list_displays() -> Dict[str, Any]:
    """
    List all available displays/monitors.

    Returns:
        Dictionary with displays array containing display information.
    """
    service = ScreenshotService()
    displays = service.list_displays()

    return {
        "displays": [
            {
                "index": d.index,
                "name": d.name,
                "x": d.x,
                "y": d.y,
                "width": d.width,
                "height": d.height,
                "isPrimary": d.is_primary,
            }
            for d in displays
        ]
    }
