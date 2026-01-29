"""Screen recording tool for Third Eye MCP."""

from typing import Any, Dict, Optional

from third_eye_mcp.services.ads import get_ad
from third_eye_mcp.services.recording import RecordingService
from third_eye_mcp.services.recording_storage import RecordingStorageService


def record(
    duration: int = 30,
    interval: float = 1.0,
    display_index: int = 0,
    max_width: int = 1280,
    change_threshold: float = 2.0,
    max_frames: int = 30,
    thumbnail_width: int = 320,
) -> Dict[str, Any]:
    """
    Record screen with change-based keyframe capture.

    Captures frames at intervals, discards near-duplicates, and returns a
    compact grid image with timestamps.

    Args:
        duration: Recording duration in seconds (1-120, default 30)
        interval: Capture interval in seconds (0.25-10, default 1.0)
        display_index: Display index to record (0-based, default 0)
        max_width: Maximum width for full frames (320-1920, default 1280)
        change_threshold: Minimum change percentage to keep frame (0-100, default 2.0)
        max_frames: Maximum frames to keep (5-100, default 30)
        thumbnail_width: Thumbnail width for grid (160-640, default 320)

    Returns:
        Dictionary with grid image, metadata, and frame summaries.
    """
    service = RecordingService()
    storage = RecordingStorageService()

    # Get sponsored message for watermark
    sponsored = get_ad()

    # Perform recording with watermark
    recording = service.record(
        duration=duration,
        interval=interval,
        display_index=display_index,
        max_width=max_width,
        change_threshold=change_threshold,
        max_frames=max_frames,
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

    return {
        "gridImage": recording.grid_image_base64,
        "metadata": {
            "recordingId": recording.metadata.recording_id,
            "duration": recording.metadata.duration,
            "framesCaptured": recording.metadata.frames_captured,
            "framesKept": recording.metadata.frames_kept,
            "framesDiscarded": recording.metadata.frames_discarded,
            "displayIndex": recording.metadata.display_index,
            "interval": recording.metadata.interval,
            "changeThreshold": recording.metadata.change_threshold,
            "startedAt": recording.metadata.started_at,
            "sponsored": recording.metadata.sponsored,
        },
        "frames": frame_summaries,
    }
