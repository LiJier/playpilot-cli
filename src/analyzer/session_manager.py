"""Temporary packages live only for their page session; no durable package store."""

import asyncio
import logging
import os
import re
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SessionClosedError(ValueError):
    """An upload cannot finish after its page session has ended."""


class SessionFileManager:
    def __init__(self, base_dir: Optional[Path] = None, ttl_seconds: int = 1800):
        self.base_dir = base_dir or (Path(tempfile.gettempdir()) / "playpilot_sessions")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self._closed = {}
        self._uploads = {}
        self._connections = {}

    def connect_session(self, session_id: str) -> str:
        """A live transport owns the package, independent of JS timer activity."""
        sid = self.validate_session_id(session_id)
        if sid in self._closed:
            raise SessionClosedError("Session ended. Please upload the package again.")
        token = uuid.uuid4().hex
        self._connections.setdefault(sid, set()).add(token)
        return token

    def disconnect_session(self, session_id: str, token: str):
        """Only the last connection closes the session; ignore stale handlers."""
        connections = self._connections.get(session_id)
        if not connections or token not in connections:
            return
        connections.remove(token)
        if not connections:
            self.delete_session_file(session_id)

    def _is_active(self, session_id: str) -> bool:
        return bool(self._connections.get(session_id)) or session_id in self._uploads

    @staticmethod
    def validate_session_id(session_id: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", session_id or ""):
            raise ValueError("Invalid session_id")
        return session_id

    def _cleanup_expired(self):
        now = time.time()
        for path in self.base_dir.iterdir():
            if path.is_file() and path.suffix in {".apk", ".aab", ".part"}:
                sid = path.stem.rsplit("_", 1)[0] if path.suffix == ".part" else path.stem
                if self._is_active(sid) and sid not in self._closed:
                    continue
                try:
                    if now - path.stat().st_mtime >= self.ttl_seconds:
                        path.unlink(missing_ok=True)
                except OSError:
                    logger.warning("Could not remove expired temporary package")
        for sid, ended_at in list(self._closed.items()):
            # Retry files held open by a parser or an in-flight upload on Windows.
            self._delete_files(sid)
            if now - ended_at >= self.ttl_seconds and sid not in self._uploads:
                self._closed.pop(sid, None)

    async def cleanup_loop(self, interval_seconds: float = 30):
        while True:
            await asyncio.sleep(interval_seconds)
            self._cleanup_expired()

    def _delete_files(self, session_id: str) -> bool:
        deleted = False
        paths = [self.base_dir / f"{session_id}{ext}" for ext in (".apk", ".aab")]
        paths.extend(self.base_dir.glob(f"{session_id}_*.part"))
        for path in paths:
            try:
                if path.exists():
                    path.unlink(missing_ok=True)
                    deleted = True
            except OSError:
                logger.warning("Could not remove temporary package; cleanup will retry")
        return deleted

    def delete_session_file(self, session_id: str) -> bool:
        """End the session and invalidate uploads before attempting file removal."""
        sid = self.validate_session_id(session_id)
        self._closed[sid] = time.time()
        self._connections.pop(sid, None)
        return self._delete_files(sid)

    def is_closed(self, session_id: str) -> bool:
        return session_id in self._closed

    def touch_session(self, session_id: str):
        sid = self.validate_session_id(session_id)
        if sid in self._closed:
            raise SessionClosedError("Session ended. Please upload the package again.")
        paths = [self.base_dir / f"{sid}{ext}" for ext in (".apk", ".aab")]
        paths.extend(self.base_dir.glob(f"{sid}_*.part"))
        for path in paths:
            try:
                if path.is_file():
                    os.utime(path, None)
            except OSError:
                pass

    async def save_upload(self, session_id: str, upload_file) -> Path:
        sid = self.validate_session_id(session_id)
        if sid in self._closed:
            raise SessionClosedError("Session ended. Please upload the package again.")
        suffix = Path(upload_file.filename or "app.apk").suffix.lower()
        if suffix not in {".aab", ".apk"}:
            raise ValueError("Unsupported package type")
        token = uuid.uuid4().hex
        self._uploads[sid] = token
        self._delete_files(sid)
        partial = self.base_dir / f"{sid}_{token}.part"
        target = self.base_dir / f"{sid}{suffix}"

        def ensure_active():
            if sid in self._closed or self._uploads.get(sid) != token:
                raise SessionClosedError("Session ended or upload replaced.")

        try:
            with partial.open("wb") as output:
                while True:
                    ensure_active()
                    chunk = await upload_file.read(1024 * 1024)
                    ensure_active()
                    if not chunk:
                        break
                    output.write(chunk)
            ensure_active()
            os.replace(partial, target)
            # A slow upload starts its orphan TTL when it completes, not when
            # its last chunk happened to be written.
            os.utime(target, None)
            return target
        finally:
            partial.unlink(missing_ok=True)
            if self._uploads.get(sid) == token:
                self._uploads.pop(sid, None)

    def get_session_file(self, session_id: str) -> Optional[Path]:
        sid = self.validate_session_id(session_id)
        if sid in self._closed:
            return None
        for ext in (".aab", ".apk"):
            path = self.base_dir / f"{sid}{ext}"
            try:
                if not path.is_file():
                    continue
                if not self._is_active(sid) and time.time() - path.stat().st_mtime >= self.ttl_seconds:
                    self.delete_session_file(sid)
                    return None
                return path
            except FileNotFoundError:
                # Explicit cleanup can race this lookup; report absence, not 500.
                continue
        return None


session_manager = SessionFileManager()
