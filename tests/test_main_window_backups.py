from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from PyQt5.QtWidgets import QApplication, QMessageBox
except ImportError:  # pragma: no cover - depends on local dev environment
    QApplication = None  # type: ignore[assignment]
    QMessageBox = None  # type: ignore[assignment]

from CDDA_editor.main import MainWindow


def write_mutation_file(path: Path, obj_id: str) -> None:
    path.write_text(
        f'[{{ "type": "mutation", "id": "{obj_id}" }}]\n',
        encoding="utf-8",
    )


@unittest.skipIf(QApplication is None, "PyQt5 is not installed")
class TestMainWindowBackups(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_loading_mod_folder_from_path_creates_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "TestMod"
            root.mkdir()
            write_mutation_file(root / "mutations.json", "UI_BACKUP_ORIGINAL")
            window = MainWindow()

            loaded = window._load_mod_folder_from_path(str(root))

            self.assertTrue(loaded)
            self.assertIsNotNone(window.project.current_backup)
            self.assertEqual(window.project.current_backup.source_path, root)
            self.assertIsNotNone(
                window.project.get_object_by_type_id("mutation", "UI_BACKUP_ORIGINAL")
            )

    def test_restore_latest_backup_restores_files_and_reloads_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "TestMod"
            root.mkdir()
            source_file = root / "mutations.json"
            write_mutation_file(source_file, "UI_BACKUP_ORIGINAL")
            window = MainWindow()
            self.assertTrue(window._load_mod_folder_from_path(str(root)))
            write_mutation_file(source_file, "UI_BROKEN_EDIT")

            with patch("CDDA_editor.main.QMessageBox.question", return_value=QMessageBox.Yes):
                window._restore_latest_backup()

            self.assertIn("UI_BACKUP_ORIGINAL", source_file.read_text(encoding="utf-8"))
            self.assertIsNotNone(
                window.project.get_object_by_type_id("mutation", "UI_BACKUP_ORIGINAL")
            )
            self.assertIsNone(window.project.get_object_by_type_id("mutation", "UI_BROKEN_EDIT"))
            self.assertGreater(window.tree.topLevelItemCount(), 0)

    def test_loading_mod_folder_starts_autobackup_timer_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "TestMod"
            root.mkdir()
            write_mutation_file(root / "mutations.json", "UI_TIMER_ORIGINAL")
            window = MainWindow()

            self.assertTrue(window._load_mod_folder_from_path(str(root)))

            self.assertTrue(window.autobackup_enabled)
            self.assertTrue(window.autobackup_timer.isActive())
            self.assertEqual(
                window.autobackup_timer.interval(),
                window.autobackup_interval_minutes * 60 * 1000,
            )

    def test_autobackup_toggle_stops_and_restarts_timer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "TestMod"
            root.mkdir()
            write_mutation_file(root / "mutations.json", "UI_TOGGLE_ORIGINAL")
            window = MainWindow()
            self.assertTrue(window._load_mod_folder_from_path(str(root)))

            window._toggle_autobackup(False)

            self.assertFalse(window.autobackup_enabled)
            self.assertFalse(window.autobackup_timer.isActive())

            window._toggle_autobackup(True)

            self.assertTrue(window.autobackup_enabled)
            self.assertTrue(window.autobackup_timer.isActive())

    def test_setting_autobackup_interval_restarts_timer_with_new_interval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "TestMod"
            root.mkdir()
            write_mutation_file(root / "mutations.json", "UI_INTERVAL_ORIGINAL")
            window = MainWindow()
            self.assertTrue(window._load_mod_folder_from_path(str(root)))

            window._set_autobackup_interval_minutes(2)

            self.assertEqual(window.autobackup_interval_minutes, 2)
            self.assertEqual(window.autobackup_timer.interval(), 120000)
            self.assertTrue(window.autobackup_timer.isActive())

    def test_run_autobackup_captures_current_editor_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "TestMod"
            root.mkdir()
            source_file = root / "mutations.json"
            write_mutation_file(source_file, "UI_AUTO_ORIGINAL")
            window = MainWindow()
            self.assertTrue(window._load_mod_folder_from_path(str(root)))
            target = window.project.get_object_by_type_id("mutation", "UI_AUTO_ORIGINAL")
            self.assertIsNotNone(target)
            window.editor.set_object(target)
            id_widget = window.editor.field_widgets["id"]
            id_widget.setText("UI_AUTO_DIRTY")

            window._run_autobackup()

            backup = window.project.current_backup
            self.assertIsNotNone(backup)
            saved_backup = (backup.backup_path / "mutations.json").read_text(encoding="utf-8")
            self.assertIn("UI_AUTO_DIRTY", saved_backup)
            self.assertIn("UI_AUTO_ORIGINAL", source_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
