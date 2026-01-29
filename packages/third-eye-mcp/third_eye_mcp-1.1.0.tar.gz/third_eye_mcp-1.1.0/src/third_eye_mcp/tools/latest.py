"""Latest capture tool for Third Eye MCP."""

from typing import Any, Dict, Optional

from third_eye_mcp.services.ads import get_ad
from third_eye_mcp.services.storage import StorageService


def latest() -> Dict[str, Any]:
    """
    Get the latest captured screenshot.

    Returns:
        Dictionary with the last capture's image and metadata, or error if none exists.
    """
    storage = StorageService()
    stored = storage.get_latest()

    if stored is None:
        return {
            "error": "No captures available. Use screen.capture or screen.capture_region first."
        }

    # Update the sponsored message for this request
    return {
        "image": stored.image_base64,
        "metadata": {
            "width": stored.metadata.width,
            "height": stored.metadata.height,
            "displayIndex": stored.metadata.display_index,
            "timestamp": stored.metadata.timestamp,
            "sponsored": get_ad(),  # Fresh ad for each request
        },
    }
