"""In-memory storage service for the latest capture."""

from typing import Optional

from third_eye_mcp.types import StoredCapture


class StorageService:
    """Service for storing and retrieving the latest capture."""

    _instance: Optional["StorageService"] = None
    _latest_capture: Optional[StoredCapture] = None

    def __new__(cls) -> "StorageService":
        """Singleton pattern to ensure one storage instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def store(self, capture: StoredCapture) -> None:
        """Store a capture as the latest."""
        self._latest_capture = capture

    def get_latest(self) -> Optional[StoredCapture]:
        """Get the latest stored capture."""
        return self._latest_capture

    def clear(self) -> None:
        """Clear the stored capture."""
        self._latest_capture = None
