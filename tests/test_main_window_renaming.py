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
class TestMainWindowObjectRenaming(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_rename_warning_mentions_incoming_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mutations.json").write_text(
                """
                [
                  { "type": "mutation", "id": "SOURCE", "prereqs": [ "TARGET" ] },
                  { "type": "mutation", "id": "TARGET" }
                ]
                """,
                encoding="utf-8",
            )
            window = MainWindow()
            window.project.load_from_dir(str(root))
            target = window.project.get_object_by_type_id("mutation", "TARGET")
            self.assertIsNotNone(target)

            warning = window._rename_warning_text(target)

            self.assertIn("входящих ссылок: 1", warning.lower())
            self.assertIn("SOURCE", warning)

    def test_rebuild_after_rename_does_not_restore_stale_editor_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mutations.json").write_text(
                """
                [
                  { "type": "mutation", "id": "SOURCE", "prereqs": [ "TARGET_OLD" ] },
                  { "type": "mutation", "id": "TARGET_OLD" }
                ]
                """,
                encoding="utf-8",
            )
            window = MainWindow()
            window.project.load_from_dir(str(root))
            target = window.project.get_object_by_type_id("mutation", "TARGET_OLD")
            source = window.project.get_object_by_type_id("mutation", "SOURCE")
            self.assertIsNotNone(target)
            self.assertIsNotNone(source)
            window.editor.set_object(target)

            window.project.rename_object(target, "TARGET_NEW", update_references=True)
            window._rebuild_tree()
            window._select_object_in_tree(target)

            self.assertEqual(target.get_id(), "TARGET_NEW")
            self.assertEqual(source.data["prereqs"], ["TARGET_NEW"])
            self.assertIs(window.project.get_object_by_type_id("mutation", "TARGET_NEW"), target)
            self.assertIsNone(window.project.get_object_by_type_id("mutation", "TARGET_OLD"))

    def test_menu_rename_does_not_restore_stale_editor_id_when_tree_is_rebuilt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mutations.json").write_text(
                """
                [
                  { "type": "mutation", "id": "SOURCE", "prereqs": [ "TARGET_OLD" ] },
                  { "type": "mutation", "id": "TARGET_OLD" }
                ]
                """,
                encoding="utf-8",
            )
            window = MainWindow()
            window.project.load_from_dir(str(root))
            window._rebuild_tree()
            target = window.project.get_object_by_type_id("mutation", "TARGET_OLD")
            source = window.project.get_object_by_type_id("mutation", "SOURCE")
            self.assertIsNotNone(target)
            self.assertIsNotNone(source)
            window._select_object_in_tree(target)

            with (
                patch("CDDA_editor.main.QInputDialog.getText", return_value=("TARGET_NEW", True)),
                patch("CDDA_editor.main.QMessageBox.question", return_value=QMessageBox.Yes),
            ):
                window._rename_selected_object()

            self.assertEqual(target.get_id(), "TARGET_NEW")
            self.assertEqual(source.data["prereqs"], ["TARGET_NEW"])
            self.assertIs(window.project.get_object_by_type_id("mutation", "TARGET_NEW"), target)
            self.assertIsNone(window.project.get_object_by_type_id("mutation", "TARGET_OLD"))


if __name__ == "__main__":
    unittest.main()
