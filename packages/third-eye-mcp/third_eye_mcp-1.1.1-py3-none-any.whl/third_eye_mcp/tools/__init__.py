"""Third Eye MCP tools."""

from third_eye_mcp.tools.list_displays import list_displays
from third_eye_mcp.tools.capture import capture
from third_eye_mcp.tools.capture_region import capture_region
from third_eye_mcp.tools.latest import latest
from third_eye_mcp.tools.record import record
from third_eye_mcp.tools.get_frame import get_frame
from third_eye_mcp.tools.scheduled_record import scheduled_record

__all__ = [
    "list_displays",
    "capture",
    "capture_region",
    "latest",
    "record",
    "get_frame",
    "scheduled_record",
]
