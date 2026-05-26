from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication, QToolBar
except ImportError:  # pragma: no cover - depends on local dev environment
    QApplication = None  # type: ignore[assignment]
    QToolBar = None  # type: ignore[assignment]
    Qt = None  # type: ignore[assignment]

from CDDA_editor.main import MainWindow


@unittest.skipIf(QApplication is None, "PyQt5 is not installed")
class TestMainWindowStatePersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_default_settings_file_is_kept_in_app_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app_root = Path(tmp)
            settings_path = app_root / "settings.ini"

            window = MainWindow(app_base_dir=app_root)
            window.show()
            self.app.processEvents()
            self.assertEqual(Path(window.settings.fileName()).resolve(), settings_path.resolve())

            window.resize(801, 602)
            window._save_window_state()

            self.assertTrue(settings_path.exists())

    def test_window_geometry_splitter_and_toolbar_layout_are_restored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = Path(tmp) / "settings.ini"
            window = MainWindow(settings_path=settings_path)
            window.show()
            self.app.processEvents()
            window.resize(912, 678)
            window.main_splitter.setSizes([321, 654])
            self.app.processEvents()
            object_toolbar = window.findChild(QToolBar, "toolbar_object")
            self.assertIsNotNone(object_toolbar)
            window.addToolBar(Qt.LeftToolBarArea, object_toolbar)
            self.app.processEvents()
            saved_splitter_sizes = window.main_splitter.sizes()

            window._save_window_state()

            restored = MainWindow(settings_path=settings_path)
            restored.show()
            self.app.processEvents()
            restored_toolbar = restored.findChild(QToolBar, "toolbar_object")
            self.assertIsNotNone(restored_toolbar)
            self.assertEqual(restored.size().width(), 912)
            self.assertEqual(restored.size().height(), 678)
            self.assertEqual(restored.main_splitter.sizes(), saved_splitter_sizes)
            self.assertEqual(restored.toolBarArea(restored_toolbar), Qt.LeftToolBarArea)


if __name__ == "__main__":
    unittest.main()
