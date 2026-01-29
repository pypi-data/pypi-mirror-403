"""Scheduled screen recording tool for Third Eye MCP."""

from typing import Any, Dict, List, Optional

from third_eye_mcp.services.ads import get_ad
from third_eye_mcp.services.recording import RecordingService
from third_eye_mcp.services.recording_storage import RecordingStorageService


def scheduled_record(
    total_duration: int = 60,
    snapshots: Optional[List[Dict[str, Any]]] = None,
    display_index: int = 0,
    max_width: int = 1280,
    thumbnail_width: int = 320,
) -> Dict[str, Any]:
    """
    Record screen with scheduled snapshot bursts at specific times.

    This is useful for longer recordings where you want to capture specific
    moments rather than continuous recording. For example, capturing the
    beginning, middle, and end of a process.

    Args:
        total_duration: Total duration to monitor in seconds (10-600, default 60)
        snapshots: List of snapshot burst configs. Each burst has:
            - at: When to start this burst (seconds from start)
            - count: Number of snapshots in this burst (default 3)
            - interval: Time between snapshots in burst (default 1.0)
        display_index: Display index to record (0-based, default 0)
        max_width: Maximum width for full frames (320-1920, default 1280)
        thumbnail_width: Thumbnail width for grid (160-640, default 320)

    Returns:
        Dictionary with grid image, metadata, and frame summaries.

    Example:
        # 4 minute recording with bursts at start, middle, and end
        scheduled_record(
            total_duration=240,
            snapshots=[
                {"at": 0, "count": 3, "interval": 1.0},      # 3 shots at start
                {"at": 120, "count": 5, "interval": 0.5},    # 5 shots at 2min
                {"at": 230, "count": 3, "interval": 1.0},    # 3 shots near end
            ]
        )
    """
    # Default snapshots if none provided
    if snapshots is None:
        snapshots = [
            {"at": 0, "count": 3, "interval": 1.0},
        ]

    service = RecordingService()
    storage = RecordingStorageService()

    # Get sponsored message for watermark
    sponsored = get_ad()

    # Perform scheduled recording with watermark
    recording = service.scheduled_record(
        total_duration=total_duration,
        snapshots=snapshots,
        display_index=display_index,
        max_width=max_width,
        thumbnail_width=thumbnail_width,
        watermark=sponsored,
    )

    # Add sponsored message to metadata
    recording.metadata.sponsored = sponsored

    # Store for later frame retrieval
    storage.store(recording)

    # Build frame summaries
    frame_summaries = [
        {
            "index": frame.index,
            "timestamp": frame.timestamp,
            "changeScore": frame.change_score,
        }
        for frame in recording.frames
    ]

    # Build burst summary for metadata
    burst_summary = [
        {
            "at": burst.get("at", 0),
            "count": burst.get("count", 3),
            "interval": burst.get("interval", 1.0),
        }
        for burst in snapshots
    ]

    return {
        "gridImage": recording.grid_image_base64,
        "metadata": {
            "recordingId": recording.metadata.recording_id,
            "duration": recording.metadata.duration,
            "totalDuration": total_duration,
            "framesCaptured": recording.metadata.frames_captured,
            "displayIndex": recording.metadata.display_index,
            "startedAt": recording.metadata.started_at,
            "bursts": burst_summary,
            "sponsored": recording.metadata.sponsored,
        },
        "frames": frame_summaries,
    }
