from __future__ import annotations

import io
import logging
import tempfile
import unittest
from pathlib import Path

from CDDA_editor.app_logging import configure_app_logging, default_log_path


class TestAppLogging(unittest.TestCase):
    def test_default_log_path_is_inside_app_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app_root = Path(tmp)
            expected_log_path = app_root / "logs" / "editor.log"
            console = io.StringIO()

            self.assertEqual(default_log_path(base_dir=app_root), expected_log_path)

            logger = configure_app_logging(
                base_dir=app_root,
                console_stream=console,
                force=True,
            )
            logger.info("local default log")
            for handler in logger.handlers:
                handler.flush()

            self.assertTrue(expected_log_path.exists())
            self.assertIn("local default log", expected_log_path.read_text(encoding="utf-8"))

    def test_configure_app_logging_writes_to_console_and_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "editor.log"
            console = io.StringIO()

            logger = configure_app_logging(
                log_path=log_path,
                console_stream=console,
                force=True,
            )
            logger.info("logging smoke")
            for handler in logger.handlers:
                handler.flush()

            self.assertIn("logging smoke", console.getvalue())
            self.assertIn("logging smoke", log_path.read_text(encoding="utf-8"))
            self.assertEqual(logger.level, logging.INFO)


if __name__ == "__main__":
    unittest.main()
