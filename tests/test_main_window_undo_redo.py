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


@unittest.skipIf(QApplication is None, "PyQt5 is not installed")
class TestMainWindowUndoRedo(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_rename_menu_action_is_undoable_and_redoable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mutations.json").write_text(
                '[{ "type": "mutation", "id": "UI_UNDO_OLD" }]',
                encoding="utf-8",
            )
            window = MainWindow()
            window.project.load_from_dir(str(root))
            window._rebuild_tree()
            target = window.project.get_object_by_type_id("mutation", "UI_UNDO_OLD")
            self.assertIsNotNone(target)
            window._select_object_in_tree(target)

            with (
                patch("CDDA_editor.main.QInputDialog.getText", return_value=("UI_UNDO_NEW", True)),
                patch("CDDA_editor.main.QMessageBox.question", return_value=QMessageBox.Yes),
            ):
                window._rename_selected_object()

            self.assertIsNotNone(window.project.get_object_by_type_id("mutation", "UI_UNDO_NEW"))
            self.assertTrue(window._undo_action.isEnabled())
            self.assertFalse(window._redo_action.isEnabled())

            window._undo_action.trigger()

            self.assertIsNotNone(window.project.get_object_by_type_id("mutation", "UI_UNDO_OLD"))
            self.assertIsNone(window.project.get_object_by_type_id("mutation", "UI_UNDO_NEW"))
            self.assertFalse(window._undo_action.isEnabled())
            self.assertTrue(window._redo_action.isEnabled())

            window._redo_action.trigger()

            self.assertIsNone(window.project.get_object_by_type_id("mutation", "UI_UNDO_OLD"))
            self.assertIsNotNone(window.project.get_object_by_type_id("mutation", "UI_UNDO_NEW"))
            self.assertTrue(window._undo_action.isEnabled())
            self.assertFalse(window._redo_action.isEnabled())

    def test_editor_field_change_is_undoable_and_redoable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_file = root / "mutations.json"
            source_file.write_text(
                '[{ "type": "mutation", "id": "UI_FIELD_EDIT", "points": 1 }]',
                encoding="utf-8",
            )
            window = MainWindow()
            window.project.load_from_dir(str(root))
            window._rebuild_tree()
            target = window.project.get_object_by_type_id("mutation", "UI_FIELD_EDIT")
            self.assertIsNotNone(target)
            window._select_object_in_tree(target)
            points_widget = window.editor.field_widgets["points"]

            points_widget.setValue(9)
            window.editor.apply_changes()

            self.assertEqual(target.data["points"], 9)
            self.assertEqual(window.project.dirty_files, {source_file})
            self.assertTrue(window._undo_action.isEnabled())

            window._undo_action.trigger()

            restored = window.project.get_object_by_type_id("mutation", "UI_FIELD_EDIT")
            self.assertIsNotNone(restored)
            self.assertEqual(restored.data["points"], 1)
            self.assertEqual(window.project.dirty_files, set())
            self.assertFalse(window._undo_action.isEnabled())
            self.assertTrue(window._redo_action.isEnabled())

            window._redo_action.trigger()

            redone = window.project.get_object_by_type_id("mutation", "UI_FIELD_EDIT")
            self.assertIsNotNone(redone)
            self.assertEqual(redone.data["points"], 9)
            self.assertEqual(window.project.dirty_files, {source_file})
            self.assertTrue(window._undo_action.isEnabled())
            self.assertFalse(window._redo_action.isEnabled())

    def test_undo_delete_restores_pending_editor_field_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mutations.json").write_text(
                '[{ "type": "mutation", "id": "UI_DELETE_EDIT", "points": 1 }]',
                encoding="utf-8",
            )
            window = MainWindow()
            window.project.load_from_dir(str(root))
            window._rebuild_tree()
            target = window.project.get_object_by_type_id("mutation", "UI_DELETE_EDIT")
            self.assertIsNotNone(target)
            window._select_object_in_tree(target)
            window.editor.field_widgets["points"].setValue(9)

            with patch("CDDA_editor.main.QMessageBox.question", return_value=QMessageBox.Yes):
                window._delete_object()

            self.assertIsNone(window.project.get_object_by_type_id("mutation", "UI_DELETE_EDIT"))

            window._undo_action.trigger()

            restored = window.project.get_object_by_type_id("mutation", "UI_DELETE_EDIT")
            self.assertIsNotNone(restored)
            self.assertEqual(restored.data["points"], 9)


if __name__ == "__main__":
    unittest.main()
