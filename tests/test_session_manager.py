import asyncio
import io
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from analyzer.session_manager import SessionClosedError, SessionFileManager


class Upload:
    filename = "app.apk"

    def __init__(self, content=b"package"):
        self.stream = io.BytesIO(content)

    async def read(self, size):
        return self.stream.read(size)


class TestSessionFiles(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.manager = SessionFileManager(Path(self.temp.name), ttl_seconds=10)

    async def test_retained_until_end_and_replacement_removes_old_type(self):
        first = await self.manager.save_upload("page", Upload())
        self.assertEqual(first.read_bytes(), b"package")
        replacement = Upload(b"replacement")
        replacement.filename = "new.aab"
        second = await self.manager.save_upload("page", replacement)
        self.assertFalse(first.exists())
        self.assertEqual(second.read_bytes(), b"replacement")
        self.assertTrue(self.manager.delete_session_file("page"))
        self.assertEqual(list(self.manager.base_dir.iterdir()), [])

    async def test_end_during_upload_cannot_recreate_package(self):
        manager = self.manager

        class EndingUpload(Upload):
            async def read(self, size):
                manager.delete_session_file("page")
                return b"late chunk"

        with self.assertRaises(SessionClosedError):
            await manager.save_upload("page", EndingUpload())
        self.assertEqual(list(manager.base_dir.iterdir()), [])
        with self.assertRaises(SessionClosedError):
            await manager.save_upload("page", Upload())

    async def test_failed_and_cancelled_uploads_leave_no_partial_files(self):
        class BrokenUpload(Upload):
            async def read(self, size):
                raise OSError("connection lost")

        with self.assertRaises(OSError):
            await self.manager.save_upload("broken", BrokenUpload())

        class CancelledUpload(Upload):
            async def read(self, size):
                raise asyncio.CancelledError()

        with self.assertRaises(asyncio.CancelledError):
            await self.manager.save_upload("cancelled", CancelledUpload())
        self.assertEqual(list(self.manager.base_dir.iterdir()), [])

    async def test_expiry_runs_without_another_upload_and_heartbeat_keeps_active_file(self):
        expired = await self.manager.save_upload("expired", Upload())
        active = await self.manager.save_upload("active", Upload())
        old = time.time() - 20
        os.utime(expired, (old, old))
        os.utime(active, (old, old))
        self.manager.touch_session("active")
        task = asyncio.create_task(self.manager.cleanup_loop(interval_seconds=0.01))
        try:
            for _ in range(100):
                if not expired.exists():
                    break
                await asyncio.sleep(0.01)
            self.assertFalse(expired.exists())
            self.assertTrue(active.exists())
        finally:
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

    async def test_unsafe_ids_are_rejected(self):
        for sid in ("../outside", "a/b", "a\\b", "", "x" * 129):
            with self.subTest(sid=sid), self.assertRaises(ValueError):
                await self.manager.save_upload(sid, Upload())


if __name__ == "__main__":
    unittest.main()
