"""Recording storage service with TTL management."""

from datetime import datetime, timezone
from typing import Dict, Optional

from third_eye_mcp.types import StoredRecording, RecordingFrame


class RecordingStorageService:
    """
    Singleton service for storing recordings in memory with TTL-based expiration.

    Stores max 5 recordings with LRU eviction when at capacity.
    Default TTL is 5 minutes.
    """

    _instance: Optional["RecordingStorageService"] = None
    _recordings: Dict[str, StoredRecording]
    _max_recordings: int = 5

    def __new__(cls) -> "RecordingStorageService":
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._recordings = {}
        return cls._instance

    def store(self, recording: StoredRecording) -> None:
        """
        Store a recording, evicting oldest if at capacity.

        Args:
            recording: The recording to store
        """
        # Clean up expired recordings first
        self._cleanup_expired()

        # Evict oldest if at capacity
        while len(self._recordings) >= self._max_recordings:
            self._evict_oldest()

        self._recordings[recording.recording_id] = recording

    def get(self, recording_id: str) -> Optional[StoredRecording]:
        """
        Get a recording by ID.

        Args:
            recording_id: The recording ID

        Returns:
            The recording if found and not expired, None otherwise
        """
        self._cleanup_expired()

        recording = self._recordings.get(recording_id)
        if recording is None:
            return None

        # Check if expired
        if datetime.now(timezone.utc) > recording.expires_at:
            del self._recordings[recording_id]
            return None

        return recording

    def get_frame(
        self,
        recording_id: str,
        frame_index: Optional[int] = None,
        timestamp: Optional[float] = None,
    ) -> Optional[RecordingFrame]:
        """
        Get a specific frame from a recording.

        Args:
            recording_id: The recording ID
            frame_index: Frame index to retrieve (0-based)
            timestamp: Timestamp to find closest frame (if frame_index not provided)

        Returns:
            The frame if found, None otherwise
        """
        recording = self.get(recording_id)
        if recording is None or not recording.frames:
            return None

        # Get by frame index
        if frame_index is not None:
            if 0 <= frame_index < len(recording.frames):
                return recording.frames[frame_index]
            return None

        # Get by closest timestamp
        if timestamp is not None:
            closest_frame = min(
                recording.frames,
                key=lambda f: abs(f.timestamp - timestamp),
            )
            return closest_frame

        # Default to first frame
        return recording.frames[0]

    def _cleanup_expired(self) -> None:
        """Remove all expired recordings."""
        now = datetime.now(timezone.utc)
        expired_ids = [
            rid
            for rid, recording in self._recordings.items()
            if now > recording.expires_at
        ]
        for rid in expired_ids:
            del self._recordings[rid]

    def _evict_oldest(self) -> None:
        """Evict the oldest recording (by creation time)."""
        if not self._recordings:
            return

        oldest_id = min(
            self._recordings.keys(),
            key=lambda rid: self._recordings[rid].created_at,
        )
        del self._recordings[oldest_id]

    def list_recordings(self) -> list[str]:
        """List all active recording IDs."""
        self._cleanup_expired()
        return list(self._recordings.keys())

    def clear(self) -> None:
        """Clear all recordings."""
        self._recordings.clear()
