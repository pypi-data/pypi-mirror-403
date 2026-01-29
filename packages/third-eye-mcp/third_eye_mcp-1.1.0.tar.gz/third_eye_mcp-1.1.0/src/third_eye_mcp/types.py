"""Type definitions for Third Eye MCP."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DisplayInfo(BaseModel):
    """Information about a display/monitor."""

    index: int = Field(description="Display index (0-based)")
    name: str = Field(description="Display name")
    x: int = Field(description="X position of the display")
    y: int = Field(description="Y position of the display")
    width: int = Field(description="Width in pixels")
    height: int = Field(description="Height in pixels")
    is_primary: bool = Field(description="Whether this is the primary display")


class CaptureMetadata(BaseModel):
    """Metadata for a screen capture."""

    width: int = Field(description="Image width in pixels")
    height: int = Field(description="Image height in pixels")
    display_index: Optional[int] = Field(default=None, description="Display index captured")
    timestamp: str = Field(description="ISO timestamp of capture")
    sponsored: Optional[str] = Field(default=None, description="Sponsored message")


class CaptureResult(BaseModel):
    """Result of a screen capture operation."""

    image_base64: str = Field(description="Base64-encoded PNG image")
    metadata: CaptureMetadata = Field(description="Capture metadata")


class CaptureInput(BaseModel):
    """Input parameters for screen.capture tool."""

    display_index: int = Field(default=0, ge=0, description="Display index to capture (0-based)")
    max_width: Optional[int] = Field(default=1920, ge=100, le=4096, description="Maximum width for resizing")
    delay: Optional[float] = Field(default=0, ge=0, le=10, description="Delay in seconds before capture")
    instant: Optional[bool] = Field(default=False, description="Skip delay if True")


class CaptureRegionInput(BaseModel):
    """Input parameters for screen.capture_region tool."""

    x: int = Field(ge=0, description="X coordinate of the region")
    y: int = Field(ge=0, description="Y coordinate of the region")
    width: int = Field(gt=0, description="Width of the region")
    height: int = Field(gt=0, description="Height of the region")
    max_width: Optional[int] = Field(default=1920, ge=100, le=4096, description="Maximum width for resizing")
    delay: Optional[float] = Field(default=0, ge=0, le=10, description="Delay in seconds before capture")
    instant: Optional[bool] = Field(default=False, description="Skip delay if True")


class StoredCapture(BaseModel):
    """A stored capture with its data."""

    image_base64: str
    metadata: CaptureMetadata
    captured_at: datetime = Field(default_factory=datetime.utcnow)


# Recording types


class RecordingFrame(BaseModel):
    """A single frame from a screen recording."""

    index: int = Field(description="Frame index in the recording")
    timestamp: float = Field(description="Seconds since recording start")
    change_score: float = Field(description="Percentage of pixels changed from previous frame")
    image_base64: str = Field(description="Base64-encoded PNG image (full resolution)")
    thumbnail_base64: str = Field(description="Base64-encoded PNG thumbnail")
    width: int = Field(description="Frame width in pixels")
    height: int = Field(description="Frame height in pixels")


class RecordingMetadata(BaseModel):
    """Metadata for a screen recording."""

    recording_id: str = Field(description="Unique recording identifier")
    duration: float = Field(description="Actual recording duration in seconds")
    frames_captured: int = Field(description="Total frames captured")
    frames_kept: int = Field(description="Frames kept after change detection")
    frames_discarded: int = Field(description="Frames discarded as duplicates")
    display_index: int = Field(description="Display index that was recorded")
    interval: float = Field(description="Capture interval in seconds")
    change_threshold: float = Field(description="Change threshold percentage used")
    started_at: str = Field(description="ISO timestamp when recording started")
    sponsored: Optional[str] = Field(default=None, description="Sponsored message")


class FrameSummary(BaseModel):
    """Summary of a frame for metadata response."""

    index: int = Field(description="Frame index")
    timestamp: float = Field(description="Seconds since recording start")
    change_score: float = Field(description="Percentage of pixels changed")


class StoredRecording(BaseModel):
    """A stored recording with all its data."""

    recording_id: str = Field(description="Unique recording identifier")
    frames: list[RecordingFrame] = Field(description="All kept frames")
    grid_image_base64: str = Field(description="Contact sheet grid image")
    metadata: RecordingMetadata = Field(description="Recording metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(description="When this recording expires")


class RecordInput(BaseModel):
    """Input parameters for screen.record tool."""

    duration: int = Field(
        default=30, ge=1, le=120, description="Recording duration in seconds (1-120)"
    )
    interval: float = Field(
        default=1.0, ge=0.25, le=10.0, description="Capture interval in seconds (0.25-10)"
    )
    display_index: int = Field(default=0, ge=0, description="Display index to record (0-based)")
    max_width: int = Field(
        default=1280, ge=320, le=1920, description="Maximum width for full frames (320-1920)"
    )
    change_threshold: float = Field(
        default=2.0, ge=0, le=100, description="Minimum change percentage to keep frame (0-100)"
    )
    max_frames: int = Field(
        default=30, ge=5, le=100, description="Maximum frames to keep (5-100)"
    )
    thumbnail_width: int = Field(
        default=320, ge=160, le=640, description="Thumbnail width for grid (160-640)"
    )


class GetFrameInput(BaseModel):
    """Input parameters for screen.get_frame tool."""

    recording_id: str = Field(description="Recording ID to retrieve frame from")
    frame_index: Optional[int] = Field(
        default=None, ge=0, description="Frame index to retrieve (0-based)"
    )
    timestamp: Optional[float] = Field(
        default=None, ge=0, description="Timestamp in seconds to find closest frame"
    )


class SnapshotBurst(BaseModel):
    """Configuration for a burst of snapshots at a specific time."""

    at: float = Field(ge=0, description="When to start this burst (seconds from recording start)")
    count: int = Field(default=3, ge=1, le=20, description="Number of snapshots to take in this burst")
    interval: float = Field(default=1.0, ge=0.25, le=10.0, description="Time between snapshots in this burst")


class ScheduledRecordInput(BaseModel):
    """Input parameters for screen.scheduled_record tool."""

    total_duration: int = Field(
        default=60, ge=10, le=600, description="Total duration to monitor in seconds (10-600)"
    )
    snapshots: list[SnapshotBurst] = Field(
        description="List of snapshot bursts to capture at specific times"
    )
    display_index: int = Field(default=0, ge=0, description="Display index to record (0-based)")
    max_width: int = Field(
        default=1280, ge=320, le=1920, description="Maximum width for full frames (320-1920)"
    )
    thumbnail_width: int = Field(
        default=320, ge=160, le=640, description="Thumbnail width for grid (160-640)"
    )
