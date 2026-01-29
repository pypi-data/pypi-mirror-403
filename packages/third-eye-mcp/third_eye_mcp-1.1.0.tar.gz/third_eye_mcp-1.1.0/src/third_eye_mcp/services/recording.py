"""Recording service for screen recording with change detection."""

import base64
import io
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import mss
from PIL import Image, ImageDraw, ImageFont

from third_eye_mcp.types import (
    RecordingFrame,
    RecordingMetadata,
    StoredRecording,
)
from third_eye_mcp.services.watermark import add_watermark


class RecordingService:
    """Service for recording screen with change-based keyframe capture."""

    # Size for change detection comparison
    COMPARE_SIZE = (64, 64)

    def __init__(self) -> None:
        """Initialize the recording service."""
        self._sct = mss.mss()

    def record(
        self,
        duration: int = 30,
        interval: float = 1.0,
        display_index: int = 0,
        max_width: int = 1280,
        change_threshold: float = 5.0,
        max_frames: int = 30,
        thumbnail_width: int = 320,
        ttl_minutes: int = 5,
        watermark: Optional[str] = None,
    ) -> StoredRecording:
        """
        Record screen with change-based keyframe capture.

        Args:
            duration: Recording duration in seconds (1-120)
            interval: Capture interval in seconds (0.25-10)
            display_index: Display index to record (0-based)
            max_width: Maximum width for full frames (320-1920)
            change_threshold: Minimum change percentage to keep frame (0-100)
            max_frames: Maximum frames to keep (5-100)
            thumbnail_width: Thumbnail width for grid (160-640)
            ttl_minutes: Time-to-live for the recording in minutes

        Returns:
            StoredRecording with grid image, frames, and metadata
        """
        monitors = self._sct.monitors
        if display_index + 1 >= len(monitors):
            raise ValueError(
                f"Display index {display_index} not found. Available: 0-{len(monitors) - 2}"
            )

        monitor = monitors[display_index + 1]
        recording_id = str(uuid.uuid4())[:8]
        started_at = datetime.now(timezone.utc)

        frames: List[RecordingFrame] = []
        last_compare_image: Optional[Image.Image] = None
        frames_captured = 0
        start_time = time.time()
        end_time = start_time + duration

        while time.time() < end_time and len(frames) < max_frames:
            capture_start = time.time()
            timestamp = capture_start - start_time

            # Capture frame
            screenshot = self._sct.grab(monitor)
            frames_captured += 1

            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

            # Create comparison image (64x64 grayscale)
            compare_image = img.resize(self.COMPARE_SIZE, Image.Resampling.BILINEAR).convert("L")

            # Calculate change from last kept frame
            if last_compare_image is None:
                change_score = 100.0  # First frame always kept
            else:
                change_score = self._calculate_change(last_compare_image, compare_image)

            # Keep frame if change exceeds threshold
            if change_score >= change_threshold:
                # Process full resolution frame
                full_image = self._resize_if_needed(img, max_width)
                full_base64 = self._image_to_base64(full_image)

                # Create thumbnail
                thumbnail = self._resize_if_needed(img, thumbnail_width)
                thumbnail_base64 = self._image_to_base64(thumbnail)

                frame = RecordingFrame(
                    index=len(frames),
                    timestamp=round(timestamp, 2),
                    change_score=round(change_score, 1),
                    image_base64=full_base64,
                    thumbnail_base64=thumbnail_base64,
                    width=full_image.width,
                    height=full_image.height,
                )
                frames.append(frame)
                last_compare_image = compare_image

            # Wait for next interval
            elapsed = time.time() - capture_start
            sleep_time = max(0, interval - elapsed)
            if sleep_time > 0 and time.time() + sleep_time < end_time:
                time.sleep(sleep_time)

        actual_duration = time.time() - start_time

        # Generate grid image with optional watermark
        grid_base64 = self._generate_grid(frames, thumbnail_width, watermark)

        # Create metadata
        metadata = RecordingMetadata(
            recording_id=recording_id,
            duration=round(actual_duration, 2),
            frames_captured=frames_captured,
            frames_kept=len(frames),
            frames_discarded=frames_captured - len(frames),
            display_index=display_index,
            interval=interval,
            change_threshold=change_threshold,
            started_at=started_at.isoformat(),
        )

        # Create stored recording
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
        recording = StoredRecording(
            recording_id=recording_id,
            frames=frames,
            grid_image_base64=grid_base64,
            metadata=metadata,
            expires_at=expires_at,
        )

        return recording

    def scheduled_record(
        self,
        total_duration: int = 60,
        snapshots: List[dict] = None,
        display_index: int = 0,
        max_width: int = 1280,
        thumbnail_width: int = 320,
        ttl_minutes: int = 10,
        watermark: Optional[str] = None,
    ) -> StoredRecording:
        """
        Record screen with scheduled snapshot bursts at specific times.

        Args:
            total_duration: Total duration to monitor in seconds (10-600)
            snapshots: List of snapshot burst configs, each with:
                - at: When to start burst (seconds from start)
                - count: Number of snapshots in burst
                - interval: Time between snapshots in burst
            display_index: Display index to record (0-based)
            max_width: Maximum width for full frames (320-1920)
            thumbnail_width: Thumbnail width for grid (160-640)
            ttl_minutes: Time-to-live for the recording in minutes

        Returns:
            StoredRecording with grid image, frames, and metadata
        """
        if snapshots is None:
            snapshots = [{"at": 0, "count": 3, "interval": 1.0}]

        monitors = self._sct.monitors
        if display_index + 1 >= len(monitors):
            raise ValueError(
                f"Display index {display_index} not found. Available: 0-{len(monitors) - 2}"
            )

        monitor = monitors[display_index + 1]
        recording_id = str(uuid.uuid4())[:8]
        started_at = datetime.now(timezone.utc)

        # Calculate all capture times in advance
        capture_times: List[Tuple[float, int]] = []  # (time, burst_index)
        for burst_idx, burst in enumerate(snapshots):
            burst_start = burst.get("at", 0)
            count = burst.get("count", 3)
            interval = burst.get("interval", 1.0)

            for i in range(count):
                capture_time = burst_start + (i * interval)
                if capture_time <= total_duration:
                    capture_times.append((capture_time, burst_idx))

        # Sort by capture time
        capture_times.sort(key=lambda x: x[0])

        frames: List[RecordingFrame] = []
        start_time = time.time()
        end_time = start_time + total_duration

        for capture_time, burst_idx in capture_times:
            # Calculate absolute time for this capture
            target_time = start_time + capture_time

            # Wait until capture time (or skip if already passed)
            now = time.time()
            if target_time > now:
                sleep_duration = target_time - now
                if now + sleep_duration > end_time:
                    break
                time.sleep(sleep_duration)

            # Check if we've exceeded total duration
            if time.time() > end_time:
                break

            # Capture frame
            actual_timestamp = time.time() - start_time
            screenshot = self._sct.grab(monitor)

            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

            # Process full resolution frame
            full_image = self._resize_if_needed(img, max_width)
            full_base64 = self._image_to_base64(full_image)

            # Create thumbnail
            thumbnail = self._resize_if_needed(img, thumbnail_width)
            thumbnail_base64 = self._image_to_base64(thumbnail)

            frame = RecordingFrame(
                index=len(frames),
                timestamp=round(actual_timestamp, 2),
                change_score=100.0 if len(frames) == 0 else 0.0,  # No change detection for scheduled
                image_base64=full_base64,
                thumbnail_base64=thumbnail_base64,
                width=full_image.width,
                height=full_image.height,
            )
            frames.append(frame)

        actual_duration = time.time() - start_time

        # Generate grid image with optional watermark
        grid_base64 = self._generate_grid(frames, thumbnail_width, watermark)

        # Create metadata
        metadata = RecordingMetadata(
            recording_id=recording_id,
            duration=round(actual_duration, 2),
            frames_captured=len(frames),
            frames_kept=len(frames),
            frames_discarded=0,
            display_index=display_index,
            interval=0.0,  # Not applicable for scheduled
            change_threshold=0.0,  # Not applicable for scheduled
            started_at=started_at.isoformat(),
        )

        # Create stored recording
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
        recording = StoredRecording(
            recording_id=recording_id,
            frames=frames,
            grid_image_base64=grid_base64,
            metadata=metadata,
            expires_at=expires_at,
        )

        return recording

    def _calculate_change(
        self, img1: Image.Image, img2: Image.Image
    ) -> float:
        """
        Calculate percentage of pixels that changed between two images.

        Args:
            img1: First grayscale image (64x64)
            img2: Second grayscale image (64x64)

        Returns:
            Percentage of pixels that changed (0-100)
        """
        pixels1 = list(img1.getdata())
        pixels2 = list(img2.getdata())

        if len(pixels1) != len(pixels2):
            return 100.0

        # Count pixels with significant change (threshold of 20 out of 255)
        change_threshold = 20
        changed = sum(
            1 for p1, p2 in zip(pixels1, pixels2) if abs(p1 - p2) > change_threshold
        )

        return (changed / len(pixels1)) * 100

    def _resize_if_needed(self, img: Image.Image, max_width: int) -> Image.Image:
        """Resize image if it exceeds max_width, maintaining aspect ratio."""
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            return img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        return img

    def _image_to_base64(self, img: Image.Image) -> str:
        """Convert PIL Image to base64-encoded PNG string."""
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def _generate_grid(
        self,
        frames: List[RecordingFrame],
        thumbnail_width: int,
        watermark: Optional[str] = None,
    ) -> str:
        """
        Generate a contact sheet grid image from frames.

        Args:
            frames: List of recording frames
            thumbnail_width: Width for each thumbnail in the grid
            watermark: Optional text to add as watermark

        Returns:
            Base64-encoded PNG of the grid image
        """
        if not frames:
            # Return a small placeholder image
            placeholder = Image.new("RGB", (200, 50), (128, 128, 128))
            return self._image_to_base64(placeholder)

        # Decode first thumbnail to get dimensions
        first_thumb = self._decode_base64_image(frames[0].thumbnail_base64)
        thumb_height = first_thumb.height

        # Calculate grid layout (aim for roughly square grid)
        n_frames = len(frames)
        cols = max(1, min(5, int(n_frames**0.5) + 1))
        rows = (n_frames + cols - 1) // cols

        # Add padding and header space for timestamps
        padding = 4
        header_height = 20
        cell_width = thumbnail_width + padding
        cell_height = thumb_height + header_height + padding

        grid_width = cols * cell_width + padding
        grid_height = rows * cell_height + padding

        # Create grid image
        grid = Image.new("RGB", (grid_width, grid_height), (32, 32, 32))
        draw = ImageDraw.Draw(grid)

        # Try to load a font, fall back to default
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except (OSError, IOError):
            font = ImageFont.load_default()

        # Place thumbnails
        for i, frame in enumerate(frames):
            row = i // cols
            col = i % cols

            x = padding + col * cell_width
            y = padding + row * cell_height

            # Draw timestamp header
            timestamp_text = f"{frame.timestamp:.1f}s ({frame.change_score:.0f}%)"
            draw.text((x + 2, y + 2), timestamp_text, fill=(200, 200, 200), font=font)

            # Decode and paste thumbnail
            thumb = self._decode_base64_image(frame.thumbnail_base64)
            grid.paste(thumb, (x, y + header_height))

        # Add watermark if provided
        if watermark:
            grid = add_watermark(grid, watermark)

        return self._image_to_base64(grid)

    def _decode_base64_image(self, base64_str: str) -> Image.Image:
        """Decode a base64-encoded image string to PIL Image."""
        image_data = base64.b64decode(base64_str)
        return Image.open(io.BytesIO(image_data))

    def close(self) -> None:
        """Close the mss instance."""
        self._sct.close()
