"""
Restart detection for pod lifecycle tracking.

Detects restarts by checking restart count from:
1. Kubernetes downward API (restart count annotation)
2. Local file marker
3. Environment variables
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RestartInfo:
    """Information about restart status."""
    restart_count: int
    is_restart: bool
    previous_exit_code: int | None = None
    restart_reason: str | None = None

    @property
    def is_first_start(self) -> bool:
        """Check if this is the first start (not a restart)."""
        return not self.is_restart


class RestartDetector:
    """
    Detects pod restarts and tracks restart count.

    Uses multiple methods to detect restarts:
    1. RESTART_COUNT environment variable (set by init container)
    2. Local marker file with count
    3. Kubernetes pod annotation via downward API
    """

    MARKER_FILE_PATH = "/tmp/dory-restart-marker"
    RESTART_COUNT_ENV = "RESTART_COUNT"
    PREVIOUS_EXIT_CODE_ENV = "PREVIOUS_EXIT_CODE"
    RESTART_REASON_ENV = "RESTART_REASON"

    def __init__(self, marker_path: str | None = None):
        """
        Initialize restart detector.

        Args:
            marker_path: Optional custom path for marker file
        """
        self._marker_path = Path(marker_path or self.MARKER_FILE_PATH)

    async def detect(self) -> RestartInfo:
        """
        Detect restart status.

        Returns:
            RestartInfo with restart count and status
        """
        # Try environment variable first (most reliable in K8s)
        env_count = self._detect_from_env()
        if env_count is not None:
            logger.debug(f"Restart count from env: {env_count}")
            return RestartInfo(
                restart_count=env_count,
                is_restart=env_count > 0,
                previous_exit_code=self._get_previous_exit_code(),
                restart_reason=self._get_restart_reason(),
            )

        # Fall back to marker file
        marker_count = self._detect_from_marker()
        logger.debug(f"Restart count from marker: {marker_count}")

        # Increment and save marker for next restart
        self._save_marker(marker_count + 1)

        return RestartInfo(
            restart_count=marker_count,
            is_restart=marker_count > 0,
            previous_exit_code=self._get_previous_exit_code(),
            restart_reason=self._get_restart_reason(),
        )

    def _detect_from_env(self) -> int | None:
        """Detect restart count from environment variable."""
        count_str = os.environ.get(self.RESTART_COUNT_ENV)
        if count_str is None:
            return None

        try:
            return int(count_str)
        except ValueError:
            logger.warning(f"Invalid RESTART_COUNT value: {count_str}")
            return None

    def _detect_from_marker(self) -> int:
        """Detect restart count from marker file."""
        if not self._marker_path.exists():
            return 0

        try:
            content = self._marker_path.read_text().strip()
            return int(content)
        except (ValueError, IOError) as e:
            logger.warning(f"Failed to read marker file: {e}")
            return 0

    def _save_marker(self, count: int) -> None:
        """Save restart count to marker file."""
        try:
            self._marker_path.parent.mkdir(parents=True, exist_ok=True)
            self._marker_path.write_text(str(count))
        except IOError as e:
            logger.warning(f"Failed to save marker file: {e}")

    def _get_previous_exit_code(self) -> int | None:
        """Get previous exit code from environment."""
        code_str = os.environ.get(self.PREVIOUS_EXIT_CODE_ENV)
        if code_str is None:
            return None

        try:
            return int(code_str)
        except ValueError:
            return None

    def _get_restart_reason(self) -> str | None:
        """Get restart reason from environment."""
        return os.environ.get(self.RESTART_REASON_ENV)

    def reset(self) -> None:
        """Reset restart counter (for testing or golden image reset)."""
        if self._marker_path.exists():
            try:
                self._marker_path.unlink()
                logger.info("Restart marker reset")
            except IOError as e:
                logger.warning(f"Failed to reset marker: {e}")
