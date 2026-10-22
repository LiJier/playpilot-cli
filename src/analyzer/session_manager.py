# -*- coding: utf-8 -*-
"""
SessionFileManager: Manages temporary package files scoped to a user session.
Enforces session-level retention:
1. Files are retained only during the active page session.
2. Replacing an uploaded file physically removes the previous package.
3. Explicit cleanup (via page unload beacon or reset) removes the package.
4. Auto-expires and cleans up files older than 30 minutes (TTL) to prevent leaks.
"""

import os
import time
import logging
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SessionFileManager:
    def __init__(self, base_dir: Optional[Path] = None, ttl_seconds: int = 1800):
        self.base_dir = base_dir or (Path(tempfile.gettempdir()) / "playpilot_sessions")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds

    def _cleanup_expired(self):
        """Scans session directory and removes files older than TTL."""
        try:
            now = time.time()
            for p in self.base_dir.iterdir():
                if p.is_file():
                    try:
                        if now - p.stat().st_mtime > self.ttl_seconds:
                            p.unlink(missing_ok=True)
                            logger.info(f"Cleaned up expired session file: {p.name}")
                    except Exception as e:
                        logger.warning(f"Failed to remove expired file {p}: {e}")
        except Exception as e:
            logger.warning(f"Error checking expired sessions: {e}")

    async def save_upload(self, session_id: str, upload_file) -> Path:
        """
        Saves an uploaded package file for the given session_id.
        Automatically destroys any previous file for this session.
        """
        self._cleanup_expired()
        self.delete_session_file(session_id)

        filename = upload_file.filename or "app.apk"
        suffix = Path(filename).suffix.lower()
        if suffix not in [".aab", ".apk"]:
            suffix = ".apk"

        # Sanitize session_id to avoid path traversal
        safe_id = Path(session_id).name
        target_path = self.base_dir / f"{safe_id}{suffix}"

        with open(target_path, "wb") as f:
            while True:
                chunk = await upload_file.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
            f.flush()

        return target_path

    def get_session_file(self, session_id: str) -> Optional[Path]:
        """Returns the Path to the stored session file, if it exists."""
        if not session_id:
            return None
        safe_id = Path(session_id).name
        for ext in [".aab", ".apk"]:
            p = self.base_dir / f"{safe_id}{ext}"
            if p.exists() and p.is_file():
                return p
        return None

    def delete_session_file(self, session_id: str) -> bool:
        """Physically removes any existing file associated with session_id."""
        if not session_id:
            return False
        safe_id = Path(session_id).name
        deleted = False
        for ext in [".aab", ".apk"]:
            p = self.base_dir / f"{safe_id}{ext}"
            if p.exists():
                try:
                    p.unlink(missing_ok=True)
                    deleted = True
                    logger.info(f"Physically deleted session file: {p.name}")
                except Exception as e:
                    logger.warning(f"Failed to delete session file {p}: {e}")
        return deleted


# Global singleton instance for the application
session_manager = SessionFileManager()
