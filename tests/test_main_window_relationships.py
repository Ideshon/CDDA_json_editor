from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication
except ImportError:  # pragma: no cover - depends on local dev environment
    QApplication = None  # type: ignore[assignment]
    Qt = None  # type: ignore[assignment]

from CDDA_editor.main import MainWindow


def write_relationship_mod(root: Path) -> None:
    (root / "mutations.json").write_text(
        """
        [
          { "type": "mutation", "id": "SOURCE", "prereqs": [ "TARGET" ] },
          { "type": "mutation", "id": "TARGET", "leads_to": [ "DEST", "MISSING" ] },
          { "type": "mutation", "id": "DEST" }
        ]
        """,
        encoding="utf-8",
    )


def table_text(table) -> str:  # type: ignore[no-untyped-def]
    cells: list[str] = []
    for row in range(table.rowCount()):
        for column in range(table.columnCount()):
            item = table.item(row, column)
            if item is not None:
                cells.append(item.text())
    return "\n".join(cells)


@unittest.skipIf(QApplication is None, "PyQt5 is not installed")
class TestMainWindowRelationships(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_relationships_window_is_modeless_and_uses_native_window_controls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = self._window_with_relationship_mod(Path(tmp))
            target = window.project.get_object_by_type_id("mutation", "TARGET")
            self.assertIsNotNone(target)
            window._select_object_in_tree(target)

            window._open_relationships_window()

            relationships = window._relationships_window
            self.assertIsNotNone(relationships)
            self.assertEqual(relationships.windowModality(), Qt.NonModal)
            self.assertTrue(relationships.pin_button.isCheckable())
            self.assertFalse(hasattr(relationships, "minimize_button"))
            self.assertFalse(hasattr(relationships, "maximize_button"))
            self.assertFalse(hasattr(relationships, "close_button"))
            self.assertTrue(relationships.windowFlags() & Qt.WindowMinimizeButtonHint)
            self.assertTrue(relationships.windowFlags() & Qt.WindowMaximizeButtonHint)
            self.assertTrue(relationships.windowFlags() & Qt.WindowCloseButtonHint)

    def test_relationships_window_state_is_saved_and_restored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "mod"
            settings_path = Path(tmp) / "settings.ini"
            window = self._window_with_relationship_mod(root, settings_path=settings_path)
            target = window.project.get_object_by_type_id("mutation", "TARGET")
            self.assertIsNotNone(target)
            window._select_object_in_tree(target)
            window._open_relationships_window()
            relationships = window._relationships_window
            self.assertIsNotNone(relationships)

            relationships.resize(777, 455)
            relationships.pin_button.setChecked(True)
            relationships.dynamic_selection_checkbox.setChecked(False)
            self.app.processEvents()
            relationships._save_window_state()

            restored = self._window_with_relationship_mod(root, settings_path=settings_path)
            restored_target = restored.project.get_object_by_type_id("mutation", "TARGET")
            self.assertIsNotNone(restored_target)
            restored._select_object_in_tree(restored_target)
            restored._open_relationships_window()
            restored_relationships = restored._relationships_window
            self.assertIsNotNone(restored_relationships)
            self.app.processEvents()

            self.assertEqual(restored_relationships.size().width(), 777)
            self.assertEqual(restored_relationships.size().height(), 455)
            self.assertTrue(restored_relationships.pin_button.isChecked())
            self.assertTrue(restored_relationships.windowFlags() & Qt.WindowStaysOnTopHint)
            self.assertFalse(restored_relationships.dynamic_selection_checkbox.isChecked())

    def test_relationships_window_shows_incoming_outgoing_and_unresolved_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = self._window_with_relationship_mod(Path(tmp))
            target = window.project.get_object_by_type_id("mutation", "TARGET")
            self.assertIsNotNone(target)
            window._select_object_in_tree(target)

            window._open_relationships_window()

            relationships = window._relationships_window
            self.assertIsNotNone(relationships)
            self.assertEqual(relationships.current_obj, target)
            self.assertEqual(relationships.incoming_table.rowCount(), 1)
            self.assertEqual(relationships.outgoing_table.rowCount(), 2)
            self.assertIn("SOURCE", table_text(relationships.incoming_table))
            self.assertIn("prereqs", table_text(relationships.incoming_table))
            outgoing_text = table_text(relationships.outgoing_table)
            self.assertIn("DEST", outgoing_text)
            self.assertIn("MISSING", outgoing_text)
            self.assertIn("не найден", outgoing_text.lower())

    def test_dynamic_relationships_window_follows_or_keeps_selected_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = self._window_with_relationship_mod(Path(tmp))
            source = window.project.get_object_by_type_id("mutation", "SOURCE")
            target = window.project.get_object_by_type_id("mutation", "TARGET")
            self.assertIsNotNone(source)
            self.assertIsNotNone(target)
            window._select_object_in_tree(target)
            window._open_relationships_window()
            relationships = window._relationships_window
            self.assertIsNotNone(relationships)

            self.assertTrue(relationships.dynamic_selection_checkbox.isChecked())
            window._select_object_in_tree(source)

            self.assertEqual(relationships.current_obj, source)

            relationships.dynamic_selection_checkbox.setChecked(False)
            window._select_object_in_tree(target)

            self.assertEqual(relationships.current_obj, source)

    def test_clicking_source_or_target_selects_object_in_main_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = self._window_with_relationship_mod(Path(tmp))
            source = window.project.get_object_by_type_id("mutation", "SOURCE")
            target = window.project.get_object_by_type_id("mutation", "TARGET")
            dest = window.project.get_object_by_type_id("mutation", "DEST")
            self.assertIsNotNone(source)
            self.assertIsNotNone(target)
            self.assertIsNotNone(dest)
            window._select_object_in_tree(target)
            window._open_relationships_window()
            relationships = window._relationships_window
            self.assertIsNotNone(relationships)
            relationships.dynamic_selection_checkbox.setChecked(False)

            relationships.incoming_table.cellClicked.emit(0, 0)

            self.assertEqual(window.editor.current_obj, source)

            relationships.outgoing_table.cellClicked.emit(0, 0)

            self.assertEqual(window.editor.current_obj, dest)

    def _window_with_relationship_mod(
        self,
        root: Path,
        settings_path: Path | None = None,
    ) -> MainWindow:
        root.mkdir(parents=True, exist_ok=True)
        write_relationship_mod(root)
        window = MainWindow(settings_path=settings_path)
        window.project.load_from_dir(str(root))
        window._rebuild_tree()
        return window


if __name__ == "__main__":
    unittest.main()
