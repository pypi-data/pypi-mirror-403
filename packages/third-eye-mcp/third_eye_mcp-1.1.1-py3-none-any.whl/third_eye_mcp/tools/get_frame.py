"""Get frame tool for Third Eye MCP."""

from typing import Any, Dict, Optional

from third_eye_mcp.services.recording_storage import RecordingStorageService


def get_frame(
    recording_id: str,
    frame_index: Optional[int] = None,
    timestamp: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Retrieve a full-resolution frame from a recording.

    Args:
        recording_id: Recording ID to retrieve frame from
        frame_index: Frame index to retrieve (0-based)
        timestamp: Timestamp in seconds to find closest frame (if frame_index not provided)

    Returns:
        Dictionary with full resolution image and frame metadata.
    """
    storage = RecordingStorageService()

    frame = storage.get_frame(
        recording_id=recording_id,
        frame_index=frame_index,
        timestamp=timestamp,
    )

    if frame is None:
        raise ValueError(
            f"Frame not found. Recording '{recording_id}' may have expired or does not exist."
        )

    return {
        "image": frame.image_base64,
        "metadata": {
            "recordingId": recording_id,
            "frameIndex": frame.index,
            "timestamp": frame.timestamp,
            "changeScore": frame.change_score,
            "width": frame.width,
            "height": frame.height,
        },
    }
